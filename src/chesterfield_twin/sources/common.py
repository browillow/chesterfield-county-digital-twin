"""Shared byte envelope validation and pinned TOML loading."""

import hashlib
import tomllib

from chesterfield_twin.domain.candidates import (
    CandidateBatch,
    Provenance,
    Retrieval,
    ValidationIssue,
)


class SourceValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def failure(code: str, message: str) -> CandidateBatch:
    return CandidateBatch(issues=[ValidationIssue(code=code, message=message)])


def load_spec(spec_bytes: bytes) -> dict:
    spec = tomllib.loads(spec_bytes.decode("utf-8"))
    if spec.get("spec_version") != 1:
        raise SourceValidationError("spec_version", "Unsupported source specification version")
    return spec


def prepare(raw: bytes, retrieval: Retrieval, spec_bytes: bytes, *, source_id: str,
            transform_id: str, synthetic: bool, media_types: set[str],
            max_bytes: int) -> tuple[dict, Provenance]:
    spec = load_spec(spec_bytes)
    if spec.get("source_id") != source_id:
        raise SourceValidationError("source_id", "Source specification does not match adapter")
    if retrieval.status_code != 200:
        raise SourceValidationError("http_status", "Source response was not HTTP 200")
    if retrieval.media_type.split(";", 1)[0].strip().lower() not in media_types:
        raise SourceValidationError("media_type", "Source response has an unexpected media type")
    if not raw or len(raw) > max_bytes:
        raise SourceValidationError("byte_limit", "Source response is empty or exceeds byte limit")
    if raw.lstrip()[:32].lower().startswith((b"<!doctype html", b"<html")):
        raise SourceValidationError("html_response", "HTML is not accepted source evidence")
    sha = hashlib.sha256(raw).hexdigest()
    # These audited artifacts are content-pinned; changed bytes require source/spec review.
    if not synthetic and spec.get("artifact_sha256") and (
            sha != spec["artifact_sha256"] or len(raw) != spec["artifact_bytes"]):
        raise SourceValidationError("artifact_pin", "Source bytes differ from the audited artifact")
    expected_url = spec.get("artifact_url", spec.get("document_url"))
    if expected_url and retrieval.url != expected_url:
        raise SourceValidationError("source_url", "Retrieval URL does not match the specification")
    provenance = Provenance(
        source_id=source_id, artifact_sha256=sha, artifact_bytes=len(raw),
        spec_sha256=hashlib.sha256(spec_bytes).hexdigest(), transform_id=transform_id,
        retrieval=retrieval, synthetic=synthetic,
        retention=spec.get("raw_retention", spec.get("retention", "unconfirmed")),
        redistribution="unconfirmed",
    )
    return spec, provenance
