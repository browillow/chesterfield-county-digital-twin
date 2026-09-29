"""Unpublished adapter contracts. These objects grant no release/storage authority."""

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from urllib.parse import parse_qsl, urlsplit

from pydantic import AwareDatetime, Field, field_validator, model_validator

from .contracts import Contract, Measurement

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Geoid = Annotated[str, Field(pattern=r"^51041[0-9]{6}$")]


def digest(value: object) -> str:
    """Canonical content identity; never use Python's process-random hash."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class Retrieval(Contract):
    url: str
    retrieved_at: AwareDatetime
    status_code: int = Field(ge=100, le=599)
    media_type: str
    etag: str | None = None
    last_modified: str | None = None

    @field_validator("url")
    @classmethod
    def public_url(cls, value):
        parsed = urlsplit(value)
        # Only source query selectors may be recorded. Credentials must be removed upstream.
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.fragment
                or any(k not in {"get", "for", "in"} for k, _ in parse_qsl(
                    parsed.query, keep_blank_values=True))):
            raise ValueError("Retrieval URL must be HTTPS with only public source selectors")
        return value


class Provenance(Contract):
    source_id: str = Field(min_length=1)
    artifact_sha256: Sha256
    artifact_bytes: int = Field(gt=0)
    spec_sha256: Sha256
    transform_id: str = Field(min_length=1)
    retrieval: Retrieval
    synthetic: bool  # Required: callers must consciously declare fixture vs source evidence.
    retention: str = Field(min_length=1)
    redistribution: Literal["unconfirmed", "allowed"] = "unconfirmed"


class ApiLocator(Contract):
    kind: Literal["api_row"] = "api_row"
    row: int = Field(ge=1, description="Zero-based JSON array row; header is row zero")
    geography_id: Geoid
    fields: tuple[str, str, str, str]  # E, M, EA, MA in that order


class BoundaryLocator(Contract):
    kind: Literal["shapefile_record"] = "shapefile_record"
    archive_member: str = Field(min_length=1)
    record: int = Field(ge=0, description="Zero-based Shapefile/DBF record")
    geography_id: Geoid


class DocumentLocator(Contract):
    kind: Literal["pdf_page"] = "pdf_page"
    pdf_page: int = Field(ge=1)
    printed_page: str = Field(min_length=1)
    heading: str = Field(min_length=1)
    text_start: int = Field(ge=0)
    text_end: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered_span(self):
        if self.text_end <= self.text_start:
            raise ValueError("Document text span must be nonempty")
        return self


class SourceNumber(Contract):
    value_state: Literal["observed", "suppressed", "unavailable", "not_applicable"]
    value: str | None = None
    reason: str | None = None
    raw: str | None
    annotation: str | None

    @model_validator(mode="after")
    def finite_or_reason(self):
        if self.value_state == "observed":
            try:
                if self.value is None or not Decimal(self.value).is_finite():
                    raise ValueError("Observed source number must be finite")
            except InvalidOperation as exc:
                raise ValueError("Invalid numeric value") from exc
        elif self.value is not None or not self.reason or not self.reason.strip():
            raise ValueError("Non-observed source number needs null value and a reason")
        return self


class Candidate(Contract):
    natural_key: str = Field(min_length=1)
    provenance: Provenance

    @property
    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json")
        # Same bytes/spec/transform/content repeat identically despite a new retrieval event.
        payload["provenance"].pop("retrieval")
        return digest(payload)


class ObservationCandidate(Candidate):
    kind: Literal["observation"] = "observation"
    metric_code: str
    metric_label: str
    aggregation: str
    measurement: Measurement
    estimate: SourceNumber
    margin_of_error: SourceNumber
    confidence_level: Literal["90%"] = "90%"
    uncertainty_kind: Literal["published_margin_of_error"] = "published_margin_of_error"
    locator: ApiLocator
    geography_definition: Literal["2020 Census tracts"] = "2020 Census tracts"

    @model_validator(mode="after")
    def consistent(self):
        m, e = self.measurement, self.estimate
        if (m.claim_class != "reported" or m.synthetic != self.provenance.synthetic
                or m.geography_id != self.locator.geography_id
                or (m.value_state, m.value, m.reason) != (e.value_state, e.value, e.reason)):
            raise ValueError("Observation, source estimate and provenance disagree")
        return self


class Geometry(Contract):
    """Source CRS geometry, deliberately not advertised as a WGS84 display layer."""
    type: Literal["Polygon", "MultiPolygon"]
    coordinates: list

    @field_validator("coordinates")
    @classmethod
    def nonempty(cls, value):
        if not value:
            raise ValueError("Empty geometry")
        return value


class BoundaryCandidate(Candidate):
    kind: Literal["boundary"] = "boundary"
    geography_id: Geoid
    name: str = Field(min_length=1)
    geography_vintage: Literal["2023"] = "2023"
    geography_definition: Literal["2020 Census tracts"] = "2020 Census tracts"
    crs: Literal["EPSG:4269"] = "EPSG:4269"
    crs_wkt: str = Field(min_length=1)
    geometry: Geometry
    geometry_sha256: Sha256
    land_area_m2: int = Field(ge=0)
    water_area_m2: int = Field(ge=0)
    locator: BoundaryLocator
    limitations: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        if self.geography_id != self.locator.geography_id:
            raise ValueError("Boundary locator geography mismatch")
        if self.geometry_sha256 != digest(self.geometry.model_dump(mode="json")):
            raise ValueError("Geometry hash mismatch")
        return self


class DocumentCandidate(Candidate):
    kind: Literal["document_excerpt"] = "document_excerpt"
    claim_class: Literal["reported"] = "reported"
    title: str = Field(min_length=1)
    reference_period: Literal["FY2025"] = "FY2025"
    geographic_scope: tuple[Literal["51041"], Literal["51570"]] = ("51041", "51570")
    scope_caveat: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    extracted_page_sha256: Sha256
    locator: DocumentLocator

    @model_validator(mode="after")
    def span_length(self):
        if self.locator.text_end - self.locator.text_start != len(self.excerpt):
            raise ValueError("Excerpt length disagrees with extracted-page span")
        if self.provenance.redistribution != "unconfirmed":
            raise ValueError("County document redistribution remains unconfirmed")
        return self


class ValidationIssue(Contract):
    code: str
    message: str
    locator: str | None = None
    severity: Literal["error", "warning"] = "error"


AnyCandidate = Annotated[ObservationCandidate | BoundaryCandidate | DocumentCandidate,
                         Field(discriminator="kind")]


class CandidateBatch(Contract):
    candidates: list[AnyCandidate] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @model_validator(mode="after")
    def atomic_and_unique(self):
        if not self.valid and self.candidates:
            raise ValueError("Failed normalization must not return partial candidates")
        keys = [c.natural_key for c in self.candidates]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate candidate natural keys")
        return self
