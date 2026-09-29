"""Replay retained audit bytes, without fetching, persistence, or county text output.

Run from the checkout: .venv/bin/python scripts/replay_audited_sources.py
  --boundary /private/tmp/cdt-boundary.zip --document /private/tmp/cdt-fy2025
Retrieval time comes from the original audit, NOT the time of this replay.
The declared successful status/media types reproduce the expected envelope;
this command does not re-verify original HTTP headers or current access.
"""

import argparse
import json
from pathlib import Path

from chesterfield_twin.domain.candidates import Retrieval
from chesterfield_twin.sources.boundaries import normalize_boundaries
from chesterfield_twin.sources.common import load_spec
from chesterfield_twin.sources.documents import normalize_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    args = parser.parse_args()
    specs = Path(__file__).resolve().parents[1] / "source_specs"
    results = {}
    for name, path, spec_name, adapter, url_key, media, limit in (
        ("boundary", args.boundary, "census_2023_va_tract_boundaries.toml", normalize_boundaries,
         "artifact_url", "application/zip", 10_000_000),
        ("document", args.document, "chesterfield_fy2025_social_services.toml", normalize_document,
         "document_url", "application/pdf", 40_000_000),
    ):
        spec_bytes = (specs / spec_name).read_bytes()
        spec = load_spec(spec_bytes)
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        batch = adapter(raw, Retrieval(url=spec[url_key], retrieved_at=spec["retrieved_at"],
                                       status_code=200, media_type=media), spec_bytes, synthetic=False)
        results[name] = {
            "valid": batch.valid, "candidate_count": len(batch.candidates),
            "issues": [i.model_dump() for i in batch.issues],
            "artifact_sha256": spec["artifact_sha256"],
            "candidate_digest": None,
        }
        if batch.valid:
            from chesterfield_twin.domain.candidates import digest
            results[name]["candidate_digest"] = digest(sorted(c.fingerprint for c in batch.candidates))
    print(json.dumps({"evidence": "replay_of_audited_bytes", "sources": results}, indent=2))
    return 0 if all(r["valid"] for r in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
