"""Focused CLI checks without repeated PDF extraction or real source fixtures."""

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/stage_audited_sources.py"


@pytest.fixture
def script():
    spec = importlib.util.spec_from_file_location("stage_audited_sources", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_staging(monkeypatch):
    instances = []
    events = []
    batches = {}

    class Staging:
        def __init__(self, root):
            self.root = root
            instances.append(self)

        def create_run(self, *, synthetic):
            assert synthetic is False
            return "real-run"

        def stage(self, run_id, source, raw, retrieval, spec_bytes, *, synthetic):
            assert run_id == "real-run" and synthetic is False
            assert source in {"boundary", "document"}
            assert retrieval.status_code == 200
            index = len(events)
            new = not any(event[0] == source for event in events)
            events.append((source, raw, retrieval, spec_bytes))
            return SimpleNamespace(import_id=f"import-{index}", retrieval_id=f"retrieval-{index}",
                                   version_ids=(source,), new_versions=int(new))

        def read_import(self, run_id, import_id):
            assert run_id == "real-run"
            source = events[int(import_id.split("-")[1])][0]
            return deepcopy(batches[source])

    module = ModuleType("chesterfield_twin.storage.staging")
    module.CandidateStaging = Staging
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return SimpleNamespace(instances=instances, events=events, batches=batches, cls=Staging)


def arguments(tmp_path):
    return ["--boundary", str(tmp_path / "boundary"), "--document", str(tmp_path / "document"),
            "--data-dir", str(tmp_path / "retained")]


def test_cli_requires_explicit_data_dir(script, tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        script.main(arguments(tmp_path)[:4])
    assert error.value.code == 2
    assert "--data-dir" in capsys.readouterr().err


def test_checkout_root_rejected_before_initialization(script, fake_staging, monkeypatch, capsys):
    initialized = []
    monkeypatch.setattr(script, "initialize", initialized.append)
    assert script.main(["--boundary", "missing", "--document", "missing", "--data-dir",
                        str(SCRIPT.parents[1])]) == 1
    assert not initialized and not fake_staging.events
    assert json.loads(capsys.readouterr().out)["verified"] is False


def test_missing_input_has_controlled_error(script, fake_staging, tmp_path, capsys):
    assert script.main(arguments(tmp_path)) == 1
    output = capsys.readouterr().out
    assert "Traceback" not in output and str(tmp_path) not in output
    assert not (tmp_path / "retained").exists()


def test_bounded_read_rejects_oversized_input(script, tmp_path):
    path = tmp_path / "large"
    path.write_bytes(b"12345")
    with pytest.raises(ValueError, match="byte limit"):
        script._read_bounded(path, 4)
    assert script._read_bounded(path, 5) == b"12345"


def prepare_valid_inputs(script, fake_staging, monkeypatch, tmp_path):
    for source in ("boundary", "document"):
        (tmp_path / source).write_bytes(b"SOURCE-CONTENT-SENTINEL")
        batch = SimpleNamespace(valid=True, candidates=[SimpleNamespace(fingerprint="a" * 64)],
                                issues=["PRIVATE-DETAIL-SENTINEL"])
        fake_staging.batches[source] = batch
        monkeypatch.setattr(script, f"normalize_{'boundaries' if source == 'boundary' else 'document'}",
                            lambda *args, batch=batch, **kwargs: deepcopy(batch))


def test_success_verifies_reopened_batches_and_reuse(
    script, fake_staging, monkeypatch, tmp_path, capsys,
):
    prepare_valid_inputs(script, fake_staging, monkeypatch, tmp_path)
    initialized = []
    monkeypatch.setattr(script, "initialize", initialized.append)
    assert script.main(arguments(tmp_path)) == 0
    output = capsys.readouterr().out
    result = json.loads(output)
    assert len(initialized) == 1 and len(fake_staging.instances) == 5
    assert len(fake_staging.events) == 4
    assert result["fresh_access_verified"] is False
    assert result["real_acs_observations_included"] is False
    assert result["synthetic"] is False
    assert "caller_declared" in result["retrieval_envelope"]
    assert "SOURCE-CONTENT-SENTINEL" not in output and "PRIVATE-DETAIL-SENTINEL" not in output
    assert str(tmp_path) not in output
    assert set(result["sources"]) == {"boundary", "document"}
    for summary in result["sources"].values():
        assert summary["candidate_count"] == 1
        assert summary["first_new_versions"] == 1
        assert summary["repeat_new_versions"] == 0
        assert summary["durable_roundtrip_verified"] is True
        assert len(summary["artifact_sha256"]) == len(summary["spec_sha256"]) == 64


@pytest.mark.parametrize("failure", ["roundtrip", "reuse", "events", "validation"])
def test_mismatch_or_invalid_source_fails_without_source_output(
    failure, script, fake_staging, monkeypatch, tmp_path, capsys,
):
    prepare_valid_inputs(script, fake_staging, monkeypatch, tmp_path)
    monkeypatch.setattr(script, "initialize", lambda root: None)
    if failure == "roundtrip":
        monkeypatch.setattr(fake_staging.cls, "read_import", lambda *args: "SECRET-MISMATCH")
    elif failure in {"reuse", "events"}:
        original = fake_staging.cls.stage

        def broken(*args, **kwargs):
            result = original(*args, **kwargs)
            if failure == "reuse":
                result.new_versions = 1
            else:
                result.retrieval_id = "same-event"
            return result

        monkeypatch.setattr(fake_staging.cls, "stage", broken)
    else:
        fake_staging.batches["document"].valid = False
    assert script.main(arguments(tmp_path)) == 1
    output = capsys.readouterr().out
    assert json.loads(output)["verified"] is False
    assert "SENTINEL" not in output and "SECRET" not in output
    if failure == "validation":
        assert not fake_staging.events
