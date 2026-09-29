"""Persist bounded reports over explicit imports, using staging's verified readback.

Reports attest to checks at creation time. Reading a report verifies its content,
not the current availability of evidence. Revalidate to check evidence again.
"""

from pathlib import Path

from pydantic import ValidationError

from chesterfield_twin.domain.candidates import CandidateBatch, digest
from chesterfield_twin.domain.validation_reports import (
    ReportContent,
    ReportInput,
    ReportIssue,
    ValidationReport,
)
from chesterfield_twin.sources.validation import validate_slice
from chesterfield_twin.storage import StorageError
from chesterfield_twin.storage.staging import CandidateStaging, _json

_SOURCES = {
    "census_acs_2023_5yr_subject": "acs",
    "census_cartographic_2023_va_tract_500k": "boundary",
    "chesterfield_fy2025_budget_social_services": "document",
}


class CandidateValidation:
    def __init__(self, root: Path):
        self.staging = CandidateStaging(root)

    def validate(self, run_id: str, import_ids: tuple[str, ...]) -> ValidationReport:
        """Canonicalize selection order, preserving duplicates as explicit failures.

        Unknown run / malformed or over-limit request / inaccessible database raises
        StorageError. An accepted request (0..16 explicit IDs) produces a report even
        when imports or evidence are absent, corrupt, duplicated or from other runs.
        """
        if (not isinstance(run_id, str) or not run_id
                or not isinstance(import_ids, tuple) or len(import_ids) > 16
                or any(not isinstance(i, str) or not i or len(i) > 128 for i in import_ids)):
            raise StorageError("validation requires an explicit run and a tuple of at most 16 IDs")
        with self.staging._locked(), self.staging._connect(write=True) as db, db:
            db.execute("BEGIN IMMEDIATE")
            mode = bool(self.staging._run(db, run_id)["synthetic"])
            inputs, issues, batches = [], [], {}

            def error(code, message, imported=None):
                issues.append(ReportIssue(code=code, message=message, import_id=imported))

            seen = set()
            for imported in sorted(import_ids):
                if imported in seen:
                    error("duplicate_import", "Import is selected more than once", imported)
                seen.add(imported)
                row = db.execute(
                    "SELECT i.*, r.synthetic, a.sha256 AS raw_sha256 "
                    "FROM staging_import i JOIN staging_run r ON r.run_id=i.run_id "
                    "LEFT JOIN retrieval e ON e.retrieval_id=i.retrieval_id "
                    "LEFT JOIN artifact a ON a.artifact_id=e.artifact_id WHERE i.import_id=?",
                    (imported,)).fetchone()
                if row is None:
                    inputs.append(ReportInput(import_id=imported))
                    error("missing_import", "Selected import does not exist", imported)
                    continue
                versions = tuple(r[0] for r in db.execute(
                    "SELECT version_id FROM staging_member WHERE import_id=? ORDER BY ordinal",
                    (imported,)))
                pin = ReportInput(import_id=imported, run_id=row["run_id"],
                    synthetic=bool(row["synthetic"]), retrieval_id=row["retrieval_id"],
                    source_id=row["source_id"], raw_sha256=row["raw_sha256"],
                    spec_sha256=row["spec_sha256"], transform_id=row["transform_id"],
                    version_ids=versions, membership_sha256=row["membership_sha256"])
                inputs.append(pin)
                if row["run_id"] != run_id:
                    error("run_mismatch", "Selected import belongs to another run", imported)
                    if pin.synthetic != mode:
                        error("mixed_mode", "Real and synthetic imports cannot mix", imported)
                    continue
                try:
                    # Exact same verification implementation as public read_import,
                    # sharing this transaction's snapshot and maintenance lock.
                    batch = self.staging._read_import(db, run_id, imported)
                    if not batch.candidates:
                        raise StorageError("empty stored batch")
                except (StorageError, OSError, ValidationError, ValueError, KeyError, TypeError):
                    error("input_integrity", "Selected import failed retained evidence verification",
                          imported)
                    continue
                inputs[-1] = pin.model_copy(update={"verified": True})
                source = _SOURCES.get(pin.source_id)
                if source is None:
                    error("unsupported_source", "Selected source is outside the pinned slice", imported)
                elif source in batches:
                    error("duplicate_source", f"Multiple imports selected for {source}", imported)
                else:
                    batches[source] = batch
            for source in ("acs", "boundary", "document"):
                if source not in batches:
                    error("missing_source", f"Missing verified {source} import")
            validated = validate_slice(*(batches.get(s, CandidateBatch())
                for s in ("acs", "boundary", "document")), allow_synthetic=mode)
            issues.extend(ReportIssue(code=i.code, message=i.message, severity=i.severity,
                                      locator=i.locator)
                          for i in validated.issues)
            content = ReportContent(run_id=run_id, synthetic=mode,
                                    inputs=tuple(inputs), issues=tuple(issues))
            payload = content.model_dump(mode="json")
            report_id = digest(payload)
            encoded = _json(payload)
            db.execute("INSERT OR IGNORE INTO candidate_validation_report "
                       "(report_id, run_id, content_json) VALUES (?, ?, ?)",
                       (report_id, run_id, encoded))
            row = db.execute("SELECT content_json FROM candidate_validation_report WHERE report_id=?",
                             (report_id,)).fetchone()
            if row[0] != encoded:
                raise StorageError("existing validation report conflicts with content")
            return ValidationReport(report_id=report_id, content=content)

    def read_report(self, run_id: str, report_id: str) -> ValidationReport:
        """Read a historical report only; does not certify current evidence availability."""
        with self.staging._locked(), self.staging._connect() as db:
            self.staging._run(db, run_id)
            row = db.execute("SELECT content_json FROM candidate_validation_report "
                             "WHERE report_id=? AND run_id=?", (report_id, run_id)).fetchone()
            if row is None:
                raise StorageError("unknown validation report in requested run")
            try:
                content = ReportContent.model_validate_json(row[0])
                if content.run_id != run_id or digest(content.model_dump(mode="json")) != report_id:
                    raise StorageError("validation report identity is corrupt")
                return ValidationReport(report_id=report_id, content=content)
            except (ValidationError, ValueError, TypeError) as exc:
                raise StorageError("stored validation report is invalid") from exc
