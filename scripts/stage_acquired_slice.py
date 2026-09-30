"""Explicit offline three-source staging from an accepted acquisition bundle.

Requires a new external root. Boundary/document bytes and their historical
envelopes are replayed from accepted specifications; only the ACS bundle carries
an acquisition envelope. Local declarations are not cryptographic origin proof.
No network, latest selection, upgrade, sealing or activation is performed.
"""

import json
from pathlib import Path

from chesterfield_twin.acquisition import AcquisitionError, read_acquisition
from chesterfield_twin.cli import SafeArgumentParser
from chesterfield_twin.config import PROJECT_ROOT, resolve_data_root
from chesterfield_twin.domain.candidates import Retrieval
from chesterfield_twin.sources.acs import normalize_acs
from chesterfield_twin.sources.boundaries import normalize_boundaries
from chesterfield_twin.sources.common import load_spec
from chesterfield_twin.sources.documents import normalize_document
from chesterfield_twin.sources.validation import validate_slice
from chesterfield_twin.storage import StorageError, initialize
from chesterfield_twin.storage.staging import CandidateStaging
from chesterfield_twin.storage.validation import CandidateValidation


def _read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Input exceeds the accepted byte limit")
    return raw


def stage_slice(*, acquisition_dir: Path, boundary: Path, document: Path,
                data_dir: Path) -> dict:
    """Validate every explicit input before creating a fresh schema-003 store."""
    root = resolve_data_root(data_dir)
    if root.exists() or data_dir.is_symlink():
        raise ValueError("A genuinely new external data root is required")
    audit = acquisition_dir.resolve()
    if root == audit or audit in root.parents or root in audit.parents:
        raise ValueError("Audit and data roots must be separate")
    acquired = read_acquisition(audit_dir=acquisition_dir, boundary_path=boundary)
    acs = normalize_acs(acquired.raw, acquired.retrieval, acquired.spec_bytes, synthetic=False)
    inputs = [("acs", acquired.raw, acquired.retrieval, acquired.spec_bytes, acs)]
    for source, path, spec_name, adapter, url_key, media, limit in (
        ("boundary", boundary, "census_2023_va_tract_boundaries.toml", normalize_boundaries,
         "artifact_url", "application/zip", 10_000_000),
        ("document", document, "chesterfield_fy2025_social_services.toml", normalize_document,
         "document_url", "application/pdf", 40_000_000),
    ):
        spec_bytes = (PROJECT_ROOT / "source_specs" / spec_name).read_bytes()
        spec = load_spec(spec_bytes)
        raw = _read_bounded(path, limit)
        retrieval = Retrieval(url=spec[url_key], retrieved_at=spec["retrieved_at"],
                              status_code=200, media_type=media)
        batch = adapter(raw, retrieval, spec_bytes, synthetic=False)
        inputs.append((source, raw, retrieval, spec_bytes, batch))
    if not validate_slice(*(entry[4] for entry in inputs)).valid:
        raise ValueError("Selected inputs failed the unchanged real-slice contract")

    # Exclusive creation closes the preflight race; existing roots are never reused.
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    initialize(root)
    staging = CandidateStaging(root)
    run_id = staging.create_run(synthetic=False)
    selected = {}
    for source, raw, retrieval, spec_bytes, _ in inputs:
        selected[source] = staging.stage(run_id, source, raw, retrieval, spec_bytes, synthetic=False)
    import_ids = tuple(selected[source].import_id for source in ("acs", "boundary", "document"))
    validation = CandidateValidation(root)
    initial = validation.validate(run_id, import_ids)
    # Reopen current objects through the validator. Historical read_report is insufficient.
    current = CandidateValidation(root).validate(run_id, import_ids)
    return {
        "run_id": run_id,
        "imports": {source: result.import_id for source, result in selected.items()},
        "initial_report_id": initial.report_id,
        "current_report_id": current.report_id,
        "initial_real_slice_valid": initial.content.real_slice_valid,
        "current_real_slice_valid": current.content.real_slice_valid,
        "current_verified_input_count": sum(pin.verified for pin in current.content.inputs),
        "current_version_count": sum(len(pin.version_ids) for pin in current.content.inputs),
        "boundary_document_envelope": "historical_spec_time_declared_status_and_media",
        "boundary_document_fresh_access": False,
        "sealed": False,
        "activated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = SafeArgumentParser(description=__doc__)
    for name in ("acquisition-dir", "boundary", "document", "data-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = stage_slice(acquisition_dir=args.acquisition_dir, boundary=args.boundary,
                             document=args.document, data_dir=args.data_dir)
    except (AcquisitionError, OSError, ValueError, StorageError):
        print(json.dumps({"staged_and_verified": False,
                          "error": "Input, fresh-root staging or current validation failed. "
                          "Preserve any created root; do not reuse or upgrade it."}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if (result["initial_real_slice_valid"] and result["current_real_slice_valid"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
