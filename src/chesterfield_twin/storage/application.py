"""Current verified public baseline reads and explicit atomic activation."""

from __future__ import annotations

import contextlib
import copy
import re
import sqlite3
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from chesterfield_twin.domain.application import (
    ActivationResult,
    BaselineRecord,
    EvidenceResponse,
    RecordChange,
    RecordPage,
    RecordQuery,
    ReleaseComparison,
    ReleaseSummary,
)
from chesterfield_twin.domain.candidates import AnyCandidate
from chesterfield_twin.domain.contracts import Bootstrap
from chesterfield_twin.domain.releases import ReleaseManifest
from chesterfield_twin.storage import StorageBusyError, StorageError
from chesterfield_twin.storage.releases import ReleaseBuilder

ApplicationCode = Literal[
    "invalid_query", "unknown_release", "unknown_evidence", "synthetic_release",
    "release_unavailable",
]
_MESSAGES = {
    "invalid_query": "Invalid application query",
    "unknown_release": "Unknown sealed release",
    "unknown_evidence": "Unknown evidence in selected release",
    "synthetic_release": "Synthetic release is not permitted for this operation",
    "release_unavailable": "Selected release is currently unavailable",
}
_CANDIDATE = TypeAdapter(AnyCandidate)
_CAPABILITIES = ["release_activation", "release_reads", "release_comparison"]


class ApplicationError(StorageError):
    """Fixed safe application error vocabulary, independent of transport."""

    def __init__(self, code: ApplicationCode):
        self.code = code
        super().__init__(_MESSAGES[code])


def _id(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ApplicationError("invalid_query")
    return value


def _busy(error: BaseException) -> bool:
    while error is not None:
        if (isinstance(error, sqlite3.Error)
                and getattr(error, "sqlite_errorcode", 0) & 255
                in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)):
            return True
        error = error.__cause__
    return False


class ReleaseApplication:
    def __init__(self, root: Path, repository_root: Path):
        self.builder = ReleaseBuilder(root, repository_root)
        self.staging = self.builder.staging

    @contextlib.contextmanager
    def _snapshot(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        try:
            with self.staging._locked(), self.staging._connect(write=write) as db:
                db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                try:
                    yield db
                finally:
                    # Includes BaseException (interruptions). Successful activation has
                    # already committed; reads and every incomplete write roll back.
                    if db.in_transaction:
                        db.rollback()
        except StorageError as exc:
            if _busy(exc):
                raise StorageBusyError("Storage is in use") from exc
            raise

    def _verified(self, db: sqlite3.Connection, release_id: str) -> ReleaseManifest:
        row = db.execute("SELECT status FROM release WHERE release_id=?", (release_id,)).fetchone()
        if row is None or row[0] != "sealed":
            raise ApplicationError("unknown_release")
        try:
            return self.builder._read(db, release_id, verify_current=True)
        except (StorageError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
            if isinstance(exc, StorageBusyError) or _busy(exc):
                raise StorageBusyError("Storage is in use") from exc
            raise ApplicationError("release_unavailable") from exc

    @staticmethod
    def _pointer(db: sqlite3.Connection) -> str | None:
        row = db.execute("SELECT active_release_id FROM app_state WHERE singleton=1").fetchone()
        if row is None:
            raise ApplicationError("release_unavailable")
        if row[0] is not None:
            try:
                _id(row[0])
            except ApplicationError as exc:
                raise ApplicationError("release_unavailable") from exc
        return row[0]

    @staticmethod
    def _records(manifest: ReleaseManifest) -> tuple[BaselineRecord, ...]:
        try:
            nodes = {n.node_id: n for n in manifest.content.nodes}
            retrieval_edges = {}
            for edge in manifest.content.edges:
                if edge.role == "retrieval":
                    retrieval_edges.setdefault(edge.from_node, []).append(edge.to_node)
            records = []
            for node in manifest.content.nodes:
                if node.kind != "candidate":
                    continue
                retrievals = [nodes[target] for target in retrieval_edges.get(node.node_id, ())]
                if len(retrievals) != 1 or retrievals[0].kind != "retrieval":
                    raise ValueError("candidate retrieval is not unique")
                payload = copy.deepcopy(node.payload["payload"])
                payload["provenance"]["retrieval"] = retrievals[0].payload["metadata"]
                candidate = _CANDIDATE.validate_python(payload)
                if (candidate.fingerprint != node.key or node.payload["version_id"] != node.key
                        or candidate.provenance.synthetic != manifest.content.synthetic):
                    raise ValueError("candidate identity differs")
                records.append(BaselineRecord(version_id=node.key, candidate=candidate))
            records.sort(key=lambda r: r.version_id)
            if tuple(r.version_id for r in records) != manifest.content.selection.version_ids:
                raise ValueError("candidate selection differs")
            return tuple(records)
        except (ValueError, KeyError, TypeError) as exc:
            raise ApplicationError("release_unavailable") from exc

    def bootstrap(self) -> Bootstrap:
        with self._snapshot() as db:
            active = self._pointer(db)
            if active is not None:
                try:
                    _id(active)
                    manifest = self._verified(db, active)
                    if manifest.content.synthetic:
                        raise ApplicationError("synthetic_release")
                except ApplicationError as exc:
                    raise ApplicationError("release_unavailable") from exc
            return Bootstrap(active_release_id=active, has_baseline=active is not None,
                             capabilities=list(_CAPABILITIES))

    def activate(self, release_id: str) -> ActivationResult:
        _id(release_id)
        with self._snapshot(write=True) as db:
            previous = self._pointer(db)
            manifest = self._verified(db, release_id)
            if manifest.content.synthetic:
                raise ApplicationError("synthetic_release")
            result = ActivationResult(release_id=release_id, synthetic=False,
                                      previous_release_id=previous, active_release_id=release_id,
                                      changed=previous != release_id)
            if result.changed:
                db.execute("UPDATE app_state SET active_release_id=? WHERE singleton=1", (release_id,))
            db.commit()
            return result

    def summary(self, release_id: str) -> ReleaseSummary:
        _id(release_id)
        with self._snapshot() as db:
            manifest = self._verified(db, release_id)
            records = self._records(manifest)
            coverage = next(n for n in manifest.content.nodes if n.kind == "coverage")
            return ReleaseSummary(
                release_id=release_id, synthetic=manifest.content.synthetic,
                candidate_report_id=manifest.content.selection.candidate_report_id,
                build_report_id=manifest.report_id,
                counts=dict(sorted(Counter(r.candidate.kind for r in records).items())),
                coverage=copy.deepcopy(coverage.payload),
                sources=tuple(n for n in manifest.content.nodes if n.kind == "source"),
            )

    def records(self, release_id: str, *, query: RecordQuery | None = None) -> RecordPage:
        _id(release_id)
        try:
            if query is not None and not isinstance(query, RecordQuery):
                raise ValueError("query model required")
            query = RecordQuery.model_validate(query.model_dump(mode="python") if query else {})
        except (ValidationError, ValueError, TypeError) as exc:
            raise ApplicationError("invalid_query") from exc
        with self._snapshot() as db:
            manifest = self._verified(db, release_id)
            selected = []
            for record in self._records(manifest):
                candidate = record.candidate
                if query.kind is not None and candidate.kind != query.kind:
                    continue
                geography = (candidate.measurement.geography_id if candidate.kind == "observation"
                             else candidate.geography_id if candidate.kind == "boundary" else None)
                if query.geography_id is not None and geography != query.geography_id:
                    continue
                metric = candidate.metric_code if candidate.kind == "observation" else None
                if query.metric_code is not None and metric != query.metric_code:
                    continue
                selected.append(record)
            return RecordPage(release_id=release_id, synthetic=manifest.content.synthetic,
                              records=tuple(selected[query.offset:query.offset + query.limit]),
                              total=len(selected), offset=query.offset, limit=query.limit)

    def evidence(self, release_id: str, version_id: str) -> EvidenceResponse:
        _id(release_id)
        _id(version_id)
        with self._snapshot() as db:
            manifest = self._verified(db, release_id)
            record = next((r for r in self._records(manifest) if r.version_id == version_id), None)
            if record is None:
                raise ApplicationError("unknown_evidence")
            start = next(n.node_id for n in manifest.content.nodes
                         if n.kind == "candidate" and n.key == version_id)
            reachable, pending = set(), [start]
            outgoing = {}
            for edge in manifest.content.edges:
                outgoing.setdefault(edge.from_node, []).append(edge.to_node)
            while pending:
                current = pending.pop()
                if current not in reachable:
                    reachable.add(current)
                    pending.extend(outgoing.get(current, ()))
            return EvidenceResponse(
                release_id=release_id, synthetic=manifest.content.synthetic, record=record,
                nodes=tuple(n for n in manifest.content.nodes if n.node_id in reachable),
                edges=tuple(e for e in manifest.content.edges
                            if e.from_node in reachable and e.to_node in reachable),
            )

    def compare(self, old_release_id: str, new_release_id: str) -> ReleaseComparison:
        _id(old_release_id)
        _id(new_release_id)
        with self._snapshot() as db:
            old = self._verified(db, old_release_id)
            new = self._verified(db, new_release_id)
            if old.content.synthetic != new.content.synthetic:
                raise ApplicationError("synthetic_release")
            before = {(r.candidate.kind, r.candidate.natural_key): r.version_id
                      for r in self._records(old)}
            after = {(r.candidate.kind, r.candidate.natural_key): r.version_id
                     for r in self._records(new)}
            changes, unchanged = [], 0
            for kind, key in sorted(before.keys() | after.keys()):
                previous, current = before.get((kind, key)), after.get((kind, key))
                if previous == current:
                    unchanged += 1
                else:
                    changes.append(RecordChange(
                        kind=kind, natural_key=key, old_version_id=previous, new_version_id=current,
                        change="added" if previous is None else "removed" if current is None else "changed",
                    ))
            return ReleaseComparison(old_release_id=old_release_id, new_release_id=new_release_id,
                                     old_synthetic=old.content.synthetic, new_synthetic=new.content.synthetic,
                                     unchanged_count=unchanged, changes=tuple(changes))
