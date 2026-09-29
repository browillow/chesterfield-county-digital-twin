"""Retain and verify an offline replay of audited boundary/PDF bytes.

Requires --boundary PATH --document PATH --data-dir EXTERNAL_ROOT.
Original retrieval times come from pinned specifications. Status 200 and media
headers are caller-declared expected envelopes, not fresh HTTP access evidence.
No ACS observations, release activation, or source content output is included.
"""

import argparse
import hashlib
import json
from pathlib import Path

from chesterfield_twin.config import resolve_data_root
from chesterfield_twin.domain.candidates import Retrieval, digest
from chesterfield_twin.sources.boundaries import normalize_boundaries
from chesterfield_twin.sources.common import load_spec
from chesterfield_twin.sources.documents import normalize_document
from chesterfield_twin.storage import StorageError, initialize


class ReplayMismatch(ValueError):
    """Durable replay did not preserve the accepted normalization."""


def _read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Input exceeds the replay byte limit")
    return raw


def replay(boundary: Path, document: Path, data_dir: Path) -> dict:
    from chesterfield_twin.storage.staging import CandidateStaging

    root = resolve_data_root(data_dir)
    specs = Path(__file__).resolve().parents[1] / "source_specs"
    # Validate both inputs before initializing or retaining any source evidence.
    inputs = []
    for source, path, spec_name, adapter, url_key, media, limit in (
        ("boundary", boundary, "census_2023_va_tract_boundaries.toml", normalize_boundaries,
         "artifact_url", "application/zip", 10_000_000),
        ("document", document, "chesterfield_fy2025_social_services.toml", normalize_document,
         "document_url", "application/pdf", 40_000_000),
    ):
        spec_bytes = (specs / spec_name).read_bytes()
        spec = load_spec(spec_bytes)
        raw = _read_bounded(path, limit)
        retrieval = Retrieval(url=spec[url_key], retrieved_at=spec["retrieved_at"],
                              status_code=200, media_type=media)
        expected = adapter(raw, retrieval, spec_bytes, synthetic=False)
        if not expected.valid:
            raise ValueError("Audited input failed normalization")
        inputs.append((source, raw, retrieval, spec_bytes, expected))

    initialize(root)
    staging = CandidateStaging(root)
    run_id = staging.create_run(synthetic=False)
    results = {}
    for source, raw, retrieval, spec_bytes, expected in inputs:
        first = staging.stage(run_id, source, raw, retrieval, spec_bytes, synthetic=False)
        reopened = CandidateStaging(root)
        if reopened.read_import(run_id, first.import_id) != expected:
            raise ReplayMismatch("Candidate roundtrip mismatch")
        repeated = reopened.stage(run_id, source, raw, retrieval, spec_bytes, synthetic=False)
        if (repeated.version_ids != first.version_ids or repeated.new_versions != 0
                or repeated.import_id == first.import_id
                or repeated.retrieval_id == first.retrieval_id
                or CandidateStaging(root).read_import(run_id, repeated.import_id) != expected):
            raise ReplayMismatch("Repeated staging mismatch")
        results[source] = {
            "candidate_count": len(expected.candidates),
            "artifact_sha256": hashlib.sha256(raw).hexdigest(),
            "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
            "candidate_digest": digest(sorted(c.fingerprint for c in expected.candidates)),
            "first_new_versions": first.new_versions,
            "repeat_new_versions": repeated.new_versions,
            "import_event_count": 2,
            "retrieval_event_count": 2,
            "durable_roundtrip_verified": True,
        }
    return {
        "evidence": "offline_replay_of_audited_bytes",
        "retrieval_envelope": "original_spec_times_with_caller_declared_status_and_media_headers",
        "fresh_access_verified": False,
        "real_acs_observations_included": False,
        "synthetic": False,
        "sources": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = replay(args.boundary, args.document, args.data_dir)
    except (OSError, ValueError, StorageError):
        # Exception messages can contain paths, text, geometry, or parsed source values.
        print(json.dumps({"evidence": "offline_replay_of_audited_bytes", "verified": False,
                          "error": "Input, staging, or durable verification failed"}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
