"""Inspect exactly selected retained imports; never stage or select latest evidence.

Requires an initialized current store, explicit --data-dir and --run-id. Repeat
--import-id for each selection (at most 16); omission deliberately validates an
empty selection. Exit 0 means a valid report, 1 an invalid persisted report, and
2 an invocation/storage failure. Synthetic validity never certifies a real slice.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from chesterfield_twin.config import resolve_data_root
from chesterfield_twin.storage import StorageError
from chesterfield_twin.storage.validation import CandidateValidation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--import-id", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        root = resolve_data_root(args.data_dir)
        if not (root / "baseline.sqlite").is_file():
            raise StorageError("baseline store is not initialized")
        report = CandidateValidation(root).validate(
            args.run_id, tuple(args.import_id))
    except (OSError, ValueError, StorageError):
        # Exception messages may include local paths or retained evidence details.
        print(json.dumps({"issues": [{"code": "validation_unavailable", "count": 1}]}))
        return 2
    content = report.content
    counts = Counter((issue.code, issue.severity) for issue in content.issues)
    print(json.dumps({
        "report_id": report.report_id,
        "synthetic": content.synthetic,
        "valid": content.valid,
        "real_slice_valid": content.real_slice_valid,
        "input_count": len(content.inputs),
        "verified_input_count": sum(pin.verified for pin in content.inputs),
        "version_count": sum(len(pin.version_ids) for pin in content.inputs),
        "issues": [{"code": code, "severity": severity, "count": count}
                   for (code, severity), count in sorted(counts.items())],
    }, indent=2))
    return 0 if content.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
