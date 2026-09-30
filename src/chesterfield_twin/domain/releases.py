"""T007b canonical first-slice closure; no activation or baseline query authority."""

from typing import Any, Literal

from pydantic import Field, model_validator

from chesterfield_twin.domain.candidates import Sha256, digest
from chesterfield_twin.domain.validation_reports import ReportIssue, ReportModel


class ReleaseNode(ReportModel):
    kind: Literal[
        "candidate", "raw", "spec", "retrieval", "source", "metric", "document",
        "transform", "query", "config", "code", "dependency", "schema", "coverage",
    ]
    key: str = Field(min_length=1)
    payload: dict[str, Any]

    @property
    def node_id(self) -> str:
        return digest(self.model_dump(mode="json"))


class ReleaseEdge(ReportModel):
    from_node: Sha256
    role: str = Field(min_length=1)
    to_node: Sha256


class ReleaseSelection(ReportModel):
    run_id: str = Field(min_length=1)
    import_ids: tuple[str, ...]
    candidate_report_id: Sha256
    version_ids: tuple[Sha256, ...]

    @model_validator(mode="after")
    def canonical_members(self):
        for values in (self.import_ids, self.version_ids):
            if values != tuple(sorted(set(values))):
                raise ValueError("release membership must be unique and sorted")
        if len(self.import_ids) != 3 or len(self.version_ids) != 303:
            raise ValueError("first slice requires three imports and 303 candidate versions")
        return self


class ReleaseContent(ReportModel):
    contract: Literal["first-slice-release/1"] = "first-slice-release/1"
    synthetic: bool
    selection: ReleaseSelection
    nodes: tuple[ReleaseNode, ...]
    edges: tuple[ReleaseEdge, ...]

    @model_validator(mode="after")
    def canonical_graph(self):
        ids = tuple(node.node_id for node in self.nodes)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("release nodes must be unique and sorted by node ID")
        keys = [(node.kind, node.key) for node in self.nodes]
        if len(keys) != len(set(keys)):
            raise ValueError("release node keys must be unique within kind")
        edges = tuple((e.from_node, e.role, e.to_node) for e in self.edges)
        if edges != tuple(sorted(set(edges))):
            raise ValueError("release edges must be unique and sorted")
        if any(a not in ids or b not in ids for a, _, b in edges):
            raise ValueError("release edge endpoint is outside membership")
        return self

    @property
    def content_id(self) -> str:
        return digest(self.model_dump(mode="json"))


class ReleaseReportContent(ReportModel):
    validator_id: Literal["first-slice-closure/1"] = "first-slice-closure/1"
    run_id: str
    import_ids: tuple[str, ...]
    synthetic: bool
    candidate_report_id: Sha256
    content_id: Sha256 | None = None
    issues: tuple[ReportIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return self.content_id is not None and not any(i.severity == "error" for i in self.issues)


class ReleaseBuildReport(ReportModel):
    report_id: Sha256
    content: ReleaseReportContent


class ReleaseManifest(ReportModel):
    content: ReleaseContent
    report_id: Sha256

    @property
    def release_id(self) -> str:
        return digest(self.model_dump(mode="json"))


class ReleaseBuildResult(ReportModel):
    report: ReleaseBuildReport
    manifest: ReleaseManifest | None = None
    sealed: bool = False
