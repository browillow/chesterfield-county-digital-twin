"""Bounded validation CLI contracts, without redoing source adapter coverage."""

import importlib.util
import json
from pathlib import Path

import pytest

from chesterfield_twin.domain.validation_reports import (
    ReportContent,
    ReportInput,
    ReportIssue,
    ValidationReport,
)
from chesterfield_twin.storage import StorageError, initialize
from chesterfield_twin.storage.staging import CandidateStaging
from chesterfield_twin.storage.validation import CandidateValidation

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate_audited_sources.py"


@pytest.fixture
def script():
    spec = importlib.util.spec_from_file_location("validate_audited_sources", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("missing", ["--data-dir", "--run-id"])
def test_requires_explicit_root_and_run(script, tmp_path, missing):
    arguments = {"--data-dir": str(tmp_path), "--run-id": "run"}
    del arguments[missing]
    with pytest.raises(SystemExit) as error:
        script.main([value for pair in arguments.items() for value in pair])
    assert error.value.code == 2


@pytest.mark.parametrize("synthetic,valid", [(True, True), (False, False)])
def test_exact_selection_summary_and_exit(script, tmp_path, monkeypatch, capsys, synthetic, valid):
    (tmp_path / "baseline.sqlite").touch()
    calls = []
    report = ValidationReport(report_id="a" * 64, content=ReportContent(
        run_id="EXPLICIT-RUN", synthetic=synthetic,
        inputs=(ReportInput(import_id="selected", verified=True, version_ids=("one",)),),
        issues=() if valid else (ReportIssue(code="missing_source", message="PRIVATE-TEXT"),)))

    class Validation:
        def __init__(self, root):
            assert root == tmp_path

        def validate(self, run_id, import_ids):
            calls.append((run_id, import_ids))
            return report

    monkeypatch.setattr(script, "CandidateValidation", Validation)
    assert script.main(["--data-dir", str(tmp_path), "--run-id", "EXPLICIT-RUN",
                        "--import-id", "second", "--import-id", "first"]) == int(not valid)
    assert calls == [("EXPLICIT-RUN", ("second", "first"))]
    output = capsys.readouterr().out
    summary = json.loads(output)
    assert summary["synthetic"] == synthetic and summary["valid"] == valid
    assert summary["real_slice_valid"] is False
    assert summary["verified_input_count"] == summary["version_count"] == 1
    assert "PRIVATE-TEXT" not in output and str(tmp_path) not in output
    assert "EXPLICIT-RUN" not in output and "selected" not in output


def test_empty_selection_persists_invalid_report_without_staging(script, tmp_path, capsys):
    root = tmp_path / "data"
    initialize(root)
    run = CandidateStaging(root).create_run(synthetic=False)
    args = ["--data-dir", str(root), "--run-id", run]
    assert script.main(args) == 1
    result = json.loads(capsys.readouterr().out)
    report = CandidateValidation(root).read_report(run, result["report_id"])
    assert report.content.inputs == () and not report.content.real_slice_valid
    assert result["input_count"] == 0
    assert script.main(args) == 1
    assert json.loads(capsys.readouterr().out)["report_id"] == result["report_id"]


@pytest.mark.parametrize("failure", ["missing_store", "over_limit", "exception"])
def test_failures_are_controlled_and_do_not_initialize(script, tmp_path, monkeypatch, capsys, failure):
    root = tmp_path / "data"
    args = ["--data-dir", str(root), "--run-id", "run"]
    if failure == "over_limit":
        initialize(root)
        args[3] = CandidateStaging(root).create_run(synthetic=True)
        args += [value for i in range(17) for value in ("--import-id", str(i))]
    elif failure == "exception":
        root.mkdir()
        (root / "baseline.sqlite").touch()
        def unavailable(*args):
            raise StorageError("PRIVATE-TEXT " + str(tmp_path))
        monkeypatch.setattr(script, "CandidateValidation", unavailable)
    assert script.main(args) == 2
    output = capsys.readouterr().out
    assert json.loads(output)["issues"][0]["code"] == "validation_unavailable"
    assert "PRIVATE-TEXT" not in output and str(tmp_path) not in output
    if failure == "missing_store":
        assert not root.exists()
