"""Immutable historical validation attestations; never release authorization."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReportIssue(ReportModel):
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"
    import_id: str | None = None
    locator: str | None = None


class ReportInput(ReportModel):
    """Metadata pins are diagnostic until verified=True; unknown imports have no pins."""

    import_id: str
    run_id: str | None = None
    synthetic: bool | None = None
    retrieval_id: str | None = None
    source_id: str | None = None
    raw_sha256: str | None = None
    spec_sha256: str | None = None
    transform_id: str | None = None
    version_ids: tuple[str, ...] = ()
    membership_sha256: str | None = None
    verified: bool = False


class ReportContent(ReportModel):
    validator_id: Literal["candidate-set/1+validate-slice/1"] = "candidate-set/1+validate-slice/1"
    run_id: str
    synthetic: bool
    inputs: tuple[ReportInput, ...]
    issues: tuple[ReportIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def real_slice_valid(self) -> bool:
        return self.valid and not self.synthetic


class ValidationReport(ReportModel):
    report_id: str
    content: ReportContent
