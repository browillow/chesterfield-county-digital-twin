"""T007c pinned application transport, separate from immutable build contracts."""

from typing import Any, Literal

from pydantic import Field, computed_field, model_validator

from .candidates import AnyCandidate, Geoid, Sha256, digest
from .contracts import Contract
from .releases import ReleaseEdge, ReleaseNode

CandidateKind = Literal["observation", "boundary", "document_excerpt"]
MetricCode = Literal["median_household_income", "poverty_rate", "household_count"]


class RecordQuery(Contract):
    kind: CandidateKind | None = None
    geography_id: Geoid | None = None
    metric_code: MetricCode | None = None
    offset: int = Field(default=0, ge=0, le=303, strict=True)
    limit: int = Field(default=100, ge=1, le=303, strict=True)


class BaselineRecord(Contract):
    version_id: Sha256
    candidate: AnyCandidate


class ReleaseResponse(Contract):
    release_id: Sha256
    synthetic: bool
    current_dependencies_verified: Literal[True] = True


class ReleaseSummary(ReleaseResponse):
    candidate_report_id: Sha256
    build_report_id: Sha256
    counts: dict[str, int]
    coverage: dict[str, Any]
    sources: tuple[ReleaseNode, ...]


class RecordPage(ReleaseResponse):
    records: tuple[BaselineRecord, ...]
    total: int = Field(ge=0, le=303)
    offset: int = Field(ge=0, le=303)
    limit: int = Field(ge=1, le=303)


class EvidenceNode(ReleaseNode):
    """Application projection with an explicit edge target; never sealed content."""

    @model_validator(mode="before")
    @classmethod
    def transport_projection(cls, value):
        if isinstance(value, ReleaseNode):
            return {"kind": value.kind, "key": value.key, "payload": value.payload}
        if isinstance(value, dict) and "node_id" in value:
            content = {key: item for key, item in value.items() if key != "node_id"}
            if value["node_id"] != digest(content):
                raise ValueError("Evidence node identity differs")
            return content
        return value

    @computed_field(return_type=Sha256)
    @property
    def node_id(self) -> str:
        # Deliberately exclude the transport-only field from the sealed identity.
        return digest({"kind": self.kind, "key": self.key, "payload": self.payload})


class EvidenceResponse(ReleaseResponse):
    record: BaselineRecord
    nodes: tuple[EvidenceNode, ...]
    edges: tuple[ReleaseEdge, ...]


class ActivationResult(ReleaseResponse):
    previous_release_id: Sha256 | None
    active_release_id: Sha256
    changed: bool


class RecordChange(Contract):
    kind: CandidateKind
    natural_key: str
    change: Literal["added", "removed", "changed"]
    old_version_id: Sha256 | None
    new_version_id: Sha256 | None


class ReleaseComparison(Contract):
    old_release_id: Sha256
    new_release_id: Sha256
    old_synthetic: bool
    new_synthetic: bool
    current_dependencies_verified: Literal[True] = True
    unchanged_count: int = Field(ge=0, le=303)
    changes: tuple[RecordChange, ...] = Field(max_length=606)
