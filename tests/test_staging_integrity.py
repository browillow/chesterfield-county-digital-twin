"""Supervisor integration checks for migrations, lineage and failure boundaries."""

import json
import sqlite3

import pytest
from test_acs_adapter import SPEC, fixture, retrieval

import chesterfield_twin.storage as storage
import chesterfield_twin.storage.staging as staging_module
from chesterfield_twin.storage import ArtifactStore, MigrationError, StorageError, initialize
from chesterfield_twin.storage.staging import CandidateStaging, StagingValidationError


def setup_stage(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    service = CandidateStaging(root)
    run = service.create_run(synthetic=True)
    raw = json.dumps(fixture()).encode()
    result = service.stage(run, "acs", raw, retrieval(), SPEC, synthetic=True)
    return root, service, run, raw, result


def test_existing_initial_schema_fails_closed_without_modification(tmp_path, monkeypatch):
    root = tmp_path / "old"
    original = storage._migration_files
    with monkeypatch.context() as patch:
        patch.setattr(storage, "_migration_files", lambda database: original(database)[:1])
        initialize(root)
    before = {p: p.read_bytes() for p in (root / "baseline.sqlite", root / "private/strategy.sqlite")}
    for action in (lambda: initialize(root), lambda: storage.check_initialized(root),
                   lambda: CandidateStaging(root).create_run(synthetic=True)):
        with pytest.raises(MigrationError):
            action()
    assert all(path.read_bytes() == content for path, content in before.items())
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM schema_migration").fetchone()[0] == 1
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='staging_run'").fetchall()


def test_unsupported_retention_and_mutated_retrieval_leave_no_objects(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    service = CandidateStaging(root)
    run = service.create_run(synthetic=True)
    changed = SPEC.replace(b"retain successful response bytes", b"do not retain response bytes")
    with pytest.raises(StagingValidationError) as failure:
        service.stage(run, "acs", json.dumps(fixture()).encode(), retrieval(), changed, synthetic=True)
    assert failure.value.issues[0].code == "retention"
    event = retrieval()
    event.url += "?key=PRIVATE-CREDENTIAL-SENTINEL"
    with pytest.raises(StagingValidationError) as failure:
        service.stage(run, "acs", json.dumps(fixture()).encode(), event, SPEC, synthetic=True)
    assert failure.value.issues[0].code == "retrieval"
    assert not list((root / "objects/sha256").glob("*/*"))
    assert b"PRIVATE-CREDENTIAL-SENTINEL" not in (root / "baseline.sqlite").read_bytes()


def test_transform_revision_reuses_assertion_but_never_version(tmp_path, monkeypatch):
    _, service, run, raw, first = setup_stage(tmp_path)
    original = staging_module._ADAPTERS["acs"]

    def revised(*args, **kwargs):
        batch = original(*args, **kwargs)
        # Synthetic probe of a deliberately reviewed transform revision.
        for candidate in batch.candidates:
            candidate.provenance.transform_id += "/synthetic-revision"
        return batch

    monkeypatch.setitem(staging_module._ADAPTERS, "acs", revised)
    second = service.stage(run, "acs", raw, retrieval(), SPEC, synthetic=True)
    assert set(first.version_ids).isdisjoint(second.version_ids)
    old = service.read_import(run, first.import_id)
    new = service.read_import(run, second.import_id)
    assert [c.natural_key for c in old.candidates] == [c.natural_key for c in new.candidates]
    assert second.new_versions == 225


def test_registered_staging_and_evidence_metadata_are_immutable(tmp_path):
    root, _, _, _, _ = setup_stage(tmp_path)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        for table in ("version", "staging_run", "staged_candidate", "staging_import",
                      "staging_member", "artifact", "retrieval"):
            column = db.execute(f"PRAGMA table_info({table})").fetchone()[1]
            for query in (f"UPDATE {table} SET {column}={column}", f"DELETE FROM {table}"):
                with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                    db.execute(query)


@pytest.mark.parametrize("damage", ["membership", "payload", "lineage", "retrieval"])
def test_metadata_corruption_is_detected_on_rehydration(tmp_path, damage):
    root, service, run, _, result = setup_stage(tmp_path)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        if damage == "membership":
            db.execute("DROP TRIGGER immutable_staging_member_delete")
            db.execute("DELETE FROM staging_member WHERE ordinal=0")
        elif damage == "payload":
            db.execute("DROP TRIGGER sealed_version_update")
            db.execute("UPDATE version SET payload_json = "
                       "json_set(payload_json, '$.metric_label', 'corrupt label')")
        elif damage == "lineage":
            db.execute("DROP TRIGGER immutable_staged_candidate_update")
            db.execute("UPDATE staged_candidate SET natural_key='corrupt key'")
        else:
            db.execute("DROP TRIGGER retained_retrieval_update")
            db.execute("UPDATE retrieval SET source_url='https://example.org/corrupt'")
    with pytest.raises(StorageError):
        service.read_import(run, result.import_id)


def test_corrupt_existing_object_is_not_silently_replaced_on_retry(tmp_path):
    root, service, run, raw, result = setup_stage(tmp_path)
    batch = service.read_import(run, result.import_id)
    path = ArtifactStore(root).path(batch.candidates[0].provenance.artifact_sha256)
    path.write_bytes(b"corrupt")
    with pytest.raises(StorageError):
        service.stage(run, "acs", raw, retrieval(), SPEC, synthetic=True)
    assert path.read_bytes() == b"corrupt"
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM staging_import").fetchone()[0] == 1


def test_directory_sync_failure_prevents_metadata_commit_then_retry(tmp_path, monkeypatch):
    root = tmp_path / "data"
    initialize(root)
    service = CandidateStaging(root)
    run = service.create_run(synthetic=True)
    raw = json.dumps(fixture()).encode()

    def io_failure(path):
        raise OSError("synthetic directory sync failure")

    with monkeypatch.context() as patch:
        patch.setattr(storage, "_sync_directory", io_failure)
        with pytest.raises(StorageError, match="I/O"):
            service.stage(run, "acs", raw, retrieval(), SPEC, synthetic=True)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM artifact").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM staging_import").fetchone()[0] == 0
    result = service.stage(run, "acs", raw, retrieval(), SPEC, synthetic=True)
    assert result.new_versions == 225
    assert len(service.read_import(run, result.import_id).candidates) == 225
