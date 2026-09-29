"""Synthetic staging acceptance; generated ACS rows prove no live observation access."""

import hashlib
import json
import sqlite3
from dataclasses import FrozenInstanceError

import pytest
from chesterfield_twin.storage.staging import CandidateStaging, StagingValidationError
from test_acs_adapter import SPEC, fixture, retrieval

from chesterfield_twin.sources.acs import normalize_acs
from chesterfield_twin.storage import (
    ArtifactStore,
    BaselineRepository,
    PrivateRepository,
    StorageError,
    initialize,
)

TABLES = ("artifact", "retrieval", "version", "staged_candidate", "staging_import", "staging_member")


@pytest.fixture
def staged_root(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    PrivateRepository(root).add_research_item("private-sentinel", "PRIVATE-STAGING-SENTINEL")
    yield root
    assert BaselineRepository(root).bootstrap().active_release_id is None


def raw_rows(rows=None):
    return json.dumps(fixture() if rows is None else rows).encode()


def counts(root):
    with sqlite3.connect(root / "baseline.sqlite") as db:
        return {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in TABLES}


def objects(root):
    return {path.name for path in (root / "objects/sha256").glob("*/*") if path.is_file()}


def stage(service, run, raw=None, event=None, spec=SPEC, synthetic=True):
    return service.stage(run, "acs", raw_rows() if raw is None else raw,
                         retrieval() if event is None else event, spec, synthetic=synthetic)


def test_roundtrip_complete_batch_and_private_release_boundary(staged_root):
    service = CandidateStaging(staged_root)
    before = BaselineRepository(staged_root).bootstrap()
    run = service.create_run(synthetic=True)
    raw = raw_rows()
    expected = normalize_acs(raw, retrieval(), SPEC, synthetic=True)
    result = stage(service, run, raw)
    actual = service.read_import(run, result.import_id)
    assert actual.model_dump(mode="json") == expected.model_dump(mode="json")
    assert result.run_id == run and result.new_versions == 225
    assert isinstance(result.version_ids, tuple)
    assert result.version_ids == tuple(c.fingerprint for c in expected.candidates)
    with pytest.raises(FrozenInstanceError):
        result.new_versions = 0
    assert ArtifactStore(staged_root).read(hashlib.sha256(raw).hexdigest()) == raw
    assert ArtifactStore(staged_root).read(hashlib.sha256(SPEC).hexdigest()) == SPEC
    assert BaselineRepository(staged_root).bootstrap() == before
    assert "PRIVATE-STAGING-SENTINEL" not in actual.model_dump_json()
    assert all(c.provenance.synthetic and c.measurement.synthetic for c in actual.candidates)


def test_reimports_share_versions_but_preserve_each_retrieval(staged_root):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    first = stage(service, run)
    event = retrieval(retrieved_at="2026-09-30T12:00:00Z", etag='"synthetic-v2"',
                      last_modified="Tue, 29 Sep 2026 12:00:00 GMT")
    second = stage(service, run, event=event)
    third = stage(service, run, event=event)
    assert first.version_ids == second.version_ids == third.version_ids
    assert (first.new_versions, second.new_versions, third.new_versions) == (225, 0, 0)
    assert len({first.import_id, second.import_id, third.import_id}) == 3
    assert len({first.retrieval_id, second.retrieval_id, third.retrieval_id}) == 3
    for result, expected_event in ((first, retrieval()), (second, event), (third, event)):
        batch = service.read_import(run, result.import_id)
        assert all(c.provenance.retrieval == expected_event for c in batch.candidates)
    assert counts(staged_root)["version"] == 225


@pytest.mark.parametrize("change", ["raw", "spec"])
def test_content_or_spec_change_creates_new_versions_for_same_keys(staged_root, change):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    first = stage(service, run)
    rows = fixture()
    rows[1][5] = "50001"
    second = stage(service, run, raw_rows(rows) if change == "raw" else raw_rows(),
                   spec=SPEC + b"\n# synthetic specification revision\n" if change == "spec" else SPEC)
    old = service.read_import(run, first.import_id)
    new = service.read_import(run, second.import_id)
    assert [c.natural_key for c in old.candidates] == [c.natural_key for c in new.candidates]
    assert set(first.version_ids).isdisjoint(second.version_ids)
    assert second.new_versions == 225
    assert old.candidates[0].estimate.value == "50000"
    assert new.candidates[0].estimate.value == ("50001" if change == "raw" else "50000")


def test_source_states_annotations_and_independent_moe_survive(staged_root):
    rows = fixture()
    rows[1][5:9] = ["0", None, "0", None]
    rows[2][5:9] = ["50000", "N", "1000", "**"]
    rows[3][5:9] = [None, None, "-555555555", None]
    rows[4][5:9] = ["50000", "250,000+", "1000", None]
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    raw = raw_rows(rows)
    result = stage(service, run, raw)
    actual = service.read_import(run, result.import_id)
    assert actual == normalize_acs(raw, retrieval(), SPEC, synthetic=True)
    income = [c for c in actual.candidates if c.metric_code == "median_household_income"]
    assert [c.estimate.value_state for c in income[:4]] == [
        "observed", "suppressed", "unavailable", "unavailable"]
    assert income[0].estimate.value == income[0].margin_of_error.value == "0"
    assert income[1].estimate.raw == "50000" and income[1].estimate.annotation == "N"
    assert income[1].margin_of_error.annotation == "**"
    assert income[2].margin_of_error.value_state == "not_applicable"
    assert income[3].estimate.annotation == "250,000+"


@pytest.mark.parametrize("failure", ["invalid", "real_run", "real_flag"])
def test_validation_and_mode_mismatch_write_nothing(staged_root, failure):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=failure != "real_run")
    before = counts(staged_root), objects(staged_root)
    with pytest.raises(StagingValidationError) as caught:
        stage(service, run, b"not-json" if failure == "invalid" else None,
              synthetic=failure != "real_flag")
    assert caught.value.issues
    assert (counts(staged_root), objects(staged_root)) == before


def test_wrong_run_cannot_read_import(staged_root):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    other = service.create_run(synthetic=True)
    result = stage(service, run)
    with pytest.raises(StorageError):
        service.read_import(other, result.import_id)


@pytest.mark.parametrize("evidence", ["raw", "spec"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_missing_or_corrupt_retained_evidence_fails_closed(staged_root, evidence, damage):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    result = stage(service, run)
    digest = hashlib.sha256(raw_rows() if evidence == "raw" else SPEC).hexdigest()
    path = ArtifactStore(staged_root).path(digest)
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"corrupt synthetic bytes")
    with pytest.raises(StorageError):
        ArtifactStore(staged_root).read(digest)
    with pytest.raises(StorageError):
        service.read_import(run, result.import_id)


def test_interruption_after_retention_leaves_only_orphan_bytes_then_retry(staged_root, monkeypatch):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    before = counts(staged_root)
    original = ArtifactStore.put

    def interrupted(store, content):
        original(store, content)
        raise StorageError("simulated interruption after durable put")

    with monkeypatch.context() as patch:
        patch.setattr(ArtifactStore, "put", interrupted)
        with pytest.raises(StorageError, match="simulated interruption"):
            stage(service, run)
    assert counts(staged_root) == before
    assert objects(staged_root)
    result = stage(service, run)
    assert result.new_versions == 225
    assert service.read_import(run, result.import_id).valid


def test_metadata_failure_rolls_back_every_staging_row_then_retry(staged_root):
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    before = counts(staged_root)
    with sqlite3.connect(staged_root / "baseline.sqlite") as db:
        db.execute("CREATE TRIGGER synthetic_abort BEFORE INSERT ON staging_member "
                   "BEGIN SELECT RAISE(ABORT, 'synthetic metadata interruption'); END")
    with pytest.raises(StorageError):
        stage(service, run)
    assert counts(staged_root) == before
    assert objects(staged_root)
    with sqlite3.connect(staged_root / "baseline.sqlite") as db:
        db.execute("DROP TRIGGER synthetic_abort")
    result = stage(service, run)
    assert result.new_versions == 225
    assert service.read_import(run, result.import_id).valid


def test_staging_operations_never_connect_private_database(staged_root, monkeypatch):
    original = sqlite3.connect

    def public_only(database, *args, **kwargs):
        assert "strategy.sqlite" not in str(database)
        return original(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", public_only)
    service = CandidateStaging(staged_root)
    run = service.create_run(synthetic=True)
    result = stage(service, run)
    assert service.read_import(run, result.import_id).valid
