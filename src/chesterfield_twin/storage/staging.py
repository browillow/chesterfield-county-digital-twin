"""Unpublished public-source staging; no private, release or network authority.

Only the three accepted byte adapters can produce persisted candidates. An import
is atomic in SQLite after both complete input objects have reached durable storage.
Unreferenced objects after interruption are safe to reuse and never auto-deleted.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from chesterfield_twin.config import resolve_data_root
from chesterfield_twin.domain.candidates import (
    AnyCandidate,
    CandidateBatch,
    Retrieval,
    ValidationIssue,
    digest,
)
from chesterfield_twin.sources.acs import normalize_acs
from chesterfield_twin.sources.boundaries import normalize_boundaries
from chesterfield_twin.sources.documents import normalize_document
from chesterfield_twin.storage import (
    ArtifactStore,
    MigrationError,
    StorageError,
    _managed_path,
    _mutable_connection,
    _readonly_connection,
    _verify_ledger,
    maintenance_lock,
)

_ADAPTERS = {"acs": normalize_acs, "boundary": normalize_boundaries, "document": normalize_document}
# Deliberately fail closed if a caller supplies a different retention policy.
# New source policies need supervisor review before permitting byte retention.
_RETENTION = {
    "acs": "retain successful response bytes with sanitized request metadata; "
           "API availability is not guaranteed",
    "boundary": "retain original archive and embedded ISO metadata with URL and checksum; "
                "no source retention-duration promise identified",
    "document": "retain one local evidence copy for private research and reproducibility",
}
_CANDIDATE = TypeAdapter(AnyCandidate)
_MAX_SPEC_BYTES = 256_000


class StagingValidationError(StorageError):
    """Normalization or staging declarations failed before retaining any bytes."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("Candidate validation failed: " + ", ".join(i.code for i in issues))


@dataclass(frozen=True)
class StageResult:
    run_id: str
    import_id: str
    retrieval_id: str
    version_ids: tuple[str, ...]
    new_versions: int


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def _invalid(code: str, message: str) -> StagingValidationError:
    return StagingValidationError([ValidationIssue(code=code, message=message)])


def _mode(synthetic: bool) -> int:
    if type(synthetic) is not bool:
        raise _invalid("synthetic_mode", "An explicit boolean synthetic declaration is required")
    return int(synthetic)


class CandidateStaging:
    """Internal service requiring an initialized external public data root."""

    def __init__(self, root: Path):
        # Check lexical paths before resolving, preserving the existing symlink boundary.
        _managed_path(Path(root), "baseline.sqlite")
        self.root = resolve_data_root(root)
        self.objects = ArtifactStore(self.root)

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        try:
            with maintenance_lock(self.root, exclusive=False):
                yield
        except OSError as exc:
            raise StorageError("candidate storage I/O failed") from exc

    @contextlib.contextmanager
    def _connect(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        path = _managed_path(self.root, "baseline.sqlite")
        if not path.is_file():
            raise MigrationError("baseline database is not initialized")
        factory = _mutable_connection if write else _readonly_connection
        try:
            with contextlib.closing(factory(path)) as connection:
                connection.row_factory = sqlite3.Row
                _verify_ledger(connection, "baseline")
                yield connection
        except sqlite3.Error as exc:
            raise StorageError("candidate storage operation failed") from exc

    @staticmethod
    def _run(connection: sqlite3.Connection, run_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM staging_run WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise StorageError("unknown staging run")
        return row

    def create_run(self, *, synthetic: bool) -> str:
        mode = _mode(synthetic)
        run_id = str(uuid4())
        with self._locked(), self._connect(write=True) as connection:
            with connection:
                connection.execute("INSERT INTO staging_run(run_id, synthetic) VALUES (?, ?)",
                                   (run_id, mode))
        return run_id

    def stage(self, run_id: str, source: str, raw: bytes, retrieval: Retrieval,
              spec_bytes: bytes, *, synthetic: bool) -> StageResult:
        mode = _mode(synthetic)
        if source not in _ADAPTERS:
            raise _invalid("source", "Unsupported source adapter")
        if not isinstance(raw, bytes) or not isinstance(spec_bytes, bytes):
            raise _invalid("input_bytes", "Source and specification must be immutable bytes")
        if not spec_bytes or len(spec_bytes) > _MAX_SPEC_BYTES:
            raise _invalid("spec_size", "Specification is empty or exceeds the byte limit")
        # Revalidate mutable caller models before passing them to an adapter.
        try:
            retrieval = Retrieval.model_validate(retrieval.model_dump(mode="json"))
        except (ValidationError, AttributeError) as exc:
            raise _invalid("retrieval", "Invalid public retrieval metadata") from exc
        with self._locked():
            with self._connect() as connection:
                if self._run(connection, run_id)["synthetic"] != mode:
                    raise _invalid("synthetic_mode", "Import declaration differs from run mode")
            batch = _ADAPTERS[source](raw, retrieval, spec_bytes, synthetic=synthetic)
            if not batch.valid or not batch.candidates:
                raise StagingValidationError(batch.issues or [ValidationIssue(
                    code="empty_batch", message="No candidates to stage")])
            raw_sha = hashlib.sha256(raw).hexdigest()
            spec_sha = hashlib.sha256(spec_bytes).hexdigest()
            provenance = batch.candidates[0].provenance
            for candidate in batch.candidates:
                p = candidate.provenance
                if (p != provenance or p.artifact_sha256 != raw_sha or p.spec_sha256 != spec_sha
                        or p.artifact_bytes != len(raw) or p.synthetic != synthetic
                        or p.retrieval != retrieval):
                    raise _invalid("lineage", "Adapter returned inconsistent source lineage")
                if p.retention != _RETENTION[source] or p.redistribution != "unconfirmed":
                    raise _invalid("retention", "Source retention policy has not been approved")

            # A failure from here may leave complete unreferenced objects, never partial metadata.
            self.objects.put(raw)
            self.objects.put(spec_bytes)
            self.objects.read(raw_sha)
            self.objects.read(spec_sha)
            import_id, retrieval_id = str(uuid4()), str(uuid4())
            version_ids = tuple(c.fingerprint for c in batch.candidates)
            inserted = 0
            with self._connect(write=True) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                for sha, content, media in ((raw_sha, raw, retrieval.media_type),
                                            (spec_sha, spec_bytes, "application/toml")):
                    connection.execute(
                        "INSERT OR IGNORE INTO artifact(artifact_id, sha256, byte_length, media_type) "
                        "VALUES (?, ?, ?, ?)", (sha, sha, len(content), media))
                    row = connection.execute("SELECT * FROM artifact WHERE sha256 = ?",
                                             (sha,)).fetchone()
                    if row is None or row["byte_length"] != len(content):
                        raise StorageError("artifact registration conflicts with retained bytes")
                raw_id = connection.execute("SELECT artifact_id FROM artifact WHERE sha256 = ?",
                                            (raw_sha,)).fetchone()[0]
                connection.execute(
                    "INSERT INTO retrieval(retrieval_id, artifact_id, source_url, retrieved_at, "
                    "outcome, metadata_json) VALUES (?, ?, ?, ?, 'accepted', ?)",
                    (retrieval_id, raw_id, retrieval.url, retrieval.retrieved_at.isoformat(),
                     retrieval.model_dump_json()))
                for candidate in batch.candidates:
                    payload = candidate.model_dump(mode="json")
                    payload["provenance"].pop("retrieval")
                    payload_json = _json(payload)
                    version_id = candidate.fingerprint
                    row = connection.execute("SELECT * FROM version WHERE version_id = ?",
                                             (version_id,)).fetchone()
                    if row is None:
                        connection.execute(
                            "INSERT INTO version(version_id, kind, payload_json, synthetic) "
                            "VALUES (?, ?, ?, ?)",
                            (version_id, candidate.kind, payload_json, mode))
                        connection.execute(
                            "INSERT INTO staged_candidate VALUES (?, ?, ?, ?, ?, ?)",
                            (version_id, candidate.natural_key, provenance.source_id, raw_sha,
                             spec_sha, provenance.transform_id))
                        inserted += 1
                    else:
                        if (row["kind"] != candidate.kind or row["synthetic"] != mode
                                or row["payload_json"] != payload_json):
                            raise StorageError("existing candidate fingerprint conflicts with payload")
                        index = connection.execute(
                            "SELECT * FROM staged_candidate WHERE version_id = ?",
                            (version_id,)).fetchone()
                        if index is None or tuple(index) != (
                            version_id, candidate.natural_key, provenance.source_id,
                            raw_sha, spec_sha, provenance.transform_id,
                        ):
                            raise StorageError("existing candidate lineage index conflicts")
                connection.execute(
                    "INSERT INTO staging_import(import_id, run_id, retrieval_id, source_id, "
                    "spec_sha256, transform_id, candidate_count, membership_sha256, issues_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (import_id, run_id, retrieval_id, provenance.source_id, spec_sha,
                     provenance.transform_id, len(version_ids), digest(version_ids),
                     _json([i.model_dump(mode="json") for i in batch.issues])))
                connection.executemany("INSERT INTO staging_member VALUES (?, ?, ?)",
                                       [(import_id, i, v) for i, v in enumerate(version_ids)])
            return StageResult(run_id, import_id, retrieval_id, version_ids, inserted)

    def read_import(self, run_id: str, import_id: str) -> CandidateBatch:
        with self._locked(), self._connect() as connection:
            try:
                return self._read_import(connection, run_id, import_id)
            except (ValidationError, ValueError, KeyError, TypeError) as exc:
                raise StorageError("stored candidate metadata is invalid") from exc

    def _read_import(self, connection: sqlite3.Connection, run_id: str,
                     import_id: str) -> CandidateBatch:
        mode = self._run(connection, run_id)["synthetic"]
        imported = connection.execute(
            "SELECT * FROM staging_import WHERE import_id = ? AND run_id = ?",
            (import_id, run_id)).fetchone()
        if imported is None:
            raise StorageError("unknown import in the requested staging run")
        event = connection.execute("SELECT * FROM retrieval WHERE retrieval_id = ?",
                                   (imported["retrieval_id"],)).fetchone()
        if event is None or event["outcome"] != "accepted":
            raise StorageError("missing accepted retrieval event")
        retrieval = Retrieval.model_validate_json(event["metadata_json"])
        if (event["source_url"] != retrieval.url
                or event["retrieved_at"] != retrieval.retrieved_at.isoformat()
                or retrieval.status_code != 200):
            raise StorageError("retrieval event disagrees with its metadata")
        artifact = connection.execute("SELECT * FROM artifact WHERE artifact_id = ?",
                                      (event["artifact_id"],)).fetchone()
        spec = connection.execute("SELECT * FROM artifact WHERE sha256 = ?",
                                  (imported["spec_sha256"],)).fetchone()
        if artifact is None or spec is None:
            raise StorageError("missing registered input artifacts")
        for obj in (artifact, spec):
            if len(self.objects.read(obj["sha256"])) != obj["byte_length"]:
                raise StorageError("retained artifact length disagrees with metadata")
        rows = connection.execute(
            "SELECT m.ordinal, c.*, v.kind, v.synthetic, v.payload_json "
            "FROM staging_member m JOIN staged_candidate c ON c.version_id = m.version_id "
            "JOIN version v ON v.version_id = c.version_id "
            "WHERE m.import_id = ? ORDER BY m.ordinal", (import_id,)).fetchall()
        version_ids = [r["version_id"] for r in rows]
        if (len(rows) != imported["candidate_count"]
                or [r["ordinal"] for r in rows] != list(range(len(rows)))
                or digest(version_ids) != imported["membership_sha256"]):
            raise StorageError("candidate membership is incomplete or corrupt")
        candidates = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if "retrieval" in payload["provenance"]:
                raise StorageError("candidate version embeds a retrieval event")
            payload["provenance"]["retrieval"] = retrieval.model_dump(mode="json")
            candidate = _CANDIDATE.validate_python(payload)
            p = candidate.provenance
            if (candidate.fingerprint != row["version_id"] or candidate.kind != row["kind"]
                    or candidate.natural_key != row["natural_key"]
                    or p.synthetic != bool(mode) or row["synthetic"] != mode
                    or p.source_id != row["source_id"] or p.source_id != imported["source_id"]
                    or p.transform_id != row["transform_id"]
                    or p.transform_id != imported["transform_id"]
                    or p.artifact_sha256 != row["raw_sha256"]
                    or p.artifact_sha256 != artifact["sha256"]
                    or p.artifact_bytes != artifact["byte_length"]
                    or p.spec_sha256 != row["spec_sha256"]
                    or p.spec_sha256 != imported["spec_sha256"]):
                raise StorageError("candidate identity or lineage is inconsistent")
            candidates.append(candidate)
        return CandidateBatch(candidates=candidates, issues=json.loads(imported["issues_json"]))
