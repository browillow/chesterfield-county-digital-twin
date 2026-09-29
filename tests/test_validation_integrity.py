"""Supervisor failure-transaction, historical integrity and migration checks."""

import sqlite3

import pytest
from test_staging_integrity import setup_stage

import chesterfield_twin.storage as storage
from chesterfield_twin.storage import ArtifactStore, MigrationError, StorageError
from chesterfield_twin.storage.staging import CandidateStaging
from chesterfield_twin.storage.validation import CandidateValidation


def test_previous_staging_schema_remains_byte_identical(tmp_path, monkeypatch):
    root = tmp_path / "previous"
    original = storage._migration_files
    with monkeypatch.context() as patch:
        patch.setattr(storage, "_migration_files", lambda name: original(name)[:2])
        storage.initialize(root)
        run = CandidateStaging(root).create_run(synthetic=False)
    before = {p: p.read_bytes() for p in (root / "baseline.sqlite", root / "private/strategy.sqlite")}
    for action in (lambda: storage.initialize(root), lambda: storage.check_initialized(root),
                   lambda: CandidateValidation(root).validate(run, ())):
        with pytest.raises(MigrationError):
            action()
    assert all(p.read_bytes() == b for p, b in before.items())


def test_input_io_failure_persists_diagnostic_pins(tmp_path, monkeypatch):
    root, _, run, _, staged = setup_stage(tmp_path)
    def denied(*args):
        raise PermissionError("not printed")
    monkeypatch.setattr(ArtifactStore, "read", denied)
    service = CandidateValidation(root)
    report = service.validate(run, (staged.import_id,))
    assert not report.content.valid
    assert not report.content.inputs[0].verified
    assert report.content.inputs[0].version_ids == staged.version_ids
    assert "input_integrity" in {i.code for i in report.content.issues}
    assert service.read_report(run, report.report_id) == report
    assert "not printed" not in report.model_dump_json()


def test_metadata_abort_rolls_back_report_and_retry_succeeds(tmp_path):
    root, _, run, _, staged = setup_stage(tmp_path)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("CREATE TRIGGER abort_report BEFORE INSERT ON candidate_validation_report "
                   "BEGIN SELECT RAISE(ABORT, 'injected'); END")
    service = CandidateValidation(root)
    with pytest.raises(StorageError):
        service.validate(run, (staged.import_id,))
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM candidate_validation_report").fetchone()[0] == 0
        db.execute("DROP TRIGGER abort_report")
    report = service.validate(run, (staged.import_id,))
    assert service.read_report(run, report.report_id) == report


def test_corrupt_historical_content_fails_closed(tmp_path):
    root, _, run, _, staged = setup_stage(tmp_path)
    service = CandidateValidation(root)
    report = service.validate(run, (staged.import_id,))
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("DROP TRIGGER immutable_candidate_validation_update")
        db.execute("UPDATE candidate_validation_report SET content_json="
                   "json_set(content_json, '$.synthetic', json('false'))")
    with pytest.raises(StorageError):
        service.read_report(run, report.report_id)


@pytest.mark.parametrize("selection", [None, [], "latest", ("",), (1,), ("x",) * 17])
def test_malformed_selection_never_writes_report(tmp_path, selection):
    root = tmp_path / "data"
    storage.initialize(root)
    run = CandidateStaging(root).create_run(synthetic=False)
    with pytest.raises(StorageError):
        CandidateValidation(root).validate(run, selection)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM candidate_validation_report").fetchone()[0] == 0
