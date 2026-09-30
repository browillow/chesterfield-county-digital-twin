"""Independent first-slice closure checks using generated, visibly synthetic evidence."""

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest
from test_validation_reports import (
    ids,
    selection,  # noqa: F401
)

import chesterfield_twin.storage as storage
from chesterfield_twin.storage import (
    ArtifactStore,
    BaselineRepository,
    MigrationError,
    StorageError,
)
from chesterfield_twin.storage.validation import CandidateValidation


@pytest.fixture(scope="module")
def repository_template(tmp_path_factory):
    # Import execution pins and freeze the public checkout once for the whole suite.
    from chesterfield_twin.storage.releases import ReleaseBuilder
    assert ReleaseBuilder is not None
    repository = tmp_path_factory.mktemp("repository-template") / "checkout"
    shutil.copytree(Path(__file__).resolve().parents[1], repository,
                    ignore=shutil.ignore_patterns(".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"))
    return repository


def prepare_closure(selection_values, tmp_path, repository_template):
    # An isolated copy pins one checkout even while other workers edit the shared tree.
    root, staging, run, inputs, results = selection_values
    repository = tmp_path / "checkout"
    shutil.copytree(repository_template, repository)
    from chesterfield_twin.storage.releases import ReleaseBuilder
    builder = ReleaseBuilder(root, repository)
    report = CandidateValidation(root).validate(run, ids(results))
    assert report.content.valid and report.content.synthetic
    return root, builder, run, ids(results), report.report_id, repository, inputs


@pytest.fixture
def closure_inputs(selection, tmp_path, repository_template):  # noqa: F811
    return prepare_closure(selection, tmp_path, repository_template)


@pytest.fixture(scope="module")
def sealed_template(tmp_path_factory, repository_template):
    base = tmp_path_factory.mktemp("sealed-template")
    generated = selection.__wrapped__(base)
    values = next(generated)
    root, builder, run, imports, report_id, repository, inputs = prepare_closure(values, base, repository_template)
    result = builder.build(run, imports, expected_report_id=report_id)
    assert result.sealed, result.report.model_dump_json()
    assert result.manifest is not None and result.manifest.content.synthetic
    yield root, result, repository, inputs
    with pytest.raises(StopIteration):
        next(generated)


@pytest.fixture
def sealed(sealed_template, tmp_path):
    from chesterfield_twin.storage.releases import ReleaseBuilder
    original_root, result, original_repository, inputs = sealed_template
    root, repository = tmp_path / "data", tmp_path / "checkout"
    shutil.copytree(original_root, root)
    shutil.copytree(original_repository, repository)
    return root, ReleaseBuilder(root, repository), result, repository, inputs


def connect(root):
    db = sqlite3.connect(root / "baseline.sqlite")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def test_direct_sealed_insert_and_empty_manifest_transition_rejected(tmp_path):
    root = tmp_path / "data"
    storage.initialize(root)
    with connect(root) as db:
        with pytest.raises(sqlite3.IntegrityError, match="assembled"):
            db.execute("INSERT INTO release VALUES ('forged', 'sealed', '{}', 'synthetic-time')")
        db.execute("INSERT INTO release VALUES ('draft', 'draft', '{}', NULL)")
        with pytest.raises(sqlite3.IntegrityError, match="closure"):
            db.execute("UPDATE release SET status='sealed', sealed_at='synthetic-time'")
        assert db.execute("SELECT status FROM release").fetchall() == [("draft",)]


def test_complete_synthetic_membership_graph_and_private_exclusion(sealed):
    root, builder, result, _, _ = sealed
    manifest = result.manifest
    assert builder.read_release(manifest.release_id) == manifest
    assert len(manifest.content.selection.version_ids) == 303
    candidates = [n for n in manifest.content.nodes if n.kind == "candidate"]
    assert len(candidates) == 303
    assert all(n.payload["synthetic"] for n in candidates)
    assert {n.kind for n in manifest.content.nodes} == {
        "candidate", "raw", "spec", "retrieval", "source", "metric", "document",
        "transform", "query", "config", "dependency", "code", "schema", "coverage"}
    with connect(root) as db:
        assert db.execute("SELECT version_id FROM release_version ORDER BY version_id").fetchall() == [
            (v,) for v in manifest.content.selection.version_ids]
        assert db.execute("SELECT import_id FROM release_import ORDER BY import_id").fetchall() == [
            (i,) for i in manifest.content.selection.import_ids]
        assert db.execute("SELECT node_id FROM release_dependency ORDER BY node_id").fetchall() == [
            (n.node_id,) for n in manifest.content.nodes]
        assert db.execute("SELECT from_node, role, to_node FROM release_edge ORDER BY from_node, role, to_node").fetchall() == [
            (e.from_node, e.role, e.to_node) for e in manifest.content.edges]
    exported = BaselineRepository(root).export_release(manifest.release_id)
    assert len(exported["versions"]) == 303
    assert "PRIVATE-REPORT-SENTINEL" not in json.dumps(exported)
    assert "PRIVATE-REPORT-SENTINEL" not in manifest.model_dump_json()
    for path in (root / "objects").rglob("*"):
        if path.is_file():
            assert b"PRIVATE-REPORT-SENTINEL" not in path.read_bytes()


@pytest.mark.parametrize("table", ["release", "release_closure", "release_import", "release_version",
                                   "release_dependency", "release_edge", "release_build_report", "version",
                                   "artifact", "retrieval", "candidate_validation_report", "staged_candidate",
                                   "staging_import", "staging_member", "staging_run"])
def test_sealed_support_and_versions_reject_update_delete(sealed, table):
    root, builder, result, _, _ = sealed
    with connect(root) as db:
        column = db.execute(f"PRAGMA table_info({table})").fetchone()[1]
        for sql in (f"UPDATE {table} SET {column}={column}", f"DELETE FROM {table}"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                db.execute(sql)
    assert builder.read_release(result.manifest.release_id) == result.manifest


@pytest.mark.parametrize("table", ["release_closure", "release_import", "release_version", "release_dependency", "release_edge"])
def test_sealed_support_reject_insert(sealed, table):
    root, _, _, _, _ = sealed
    with connect(root) as db:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute(f"INSERT INTO {table} SELECT * FROM {table} LIMIT 1")


@pytest.mark.parametrize("evidence", ["raw", "spec", "code", "lock", "report", "manifest"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_retained_dependency_damage_rejected_on_current_read(sealed, evidence, damage):
    root, builder, result, repository, inputs = sealed
    if evidence in ("raw", "spec"):
        sha = hashlib.sha256(inputs[0][1 if evidence == "raw" else 3]).hexdigest()
    elif evidence in ("code", "lock"):
        file = "src/chesterfield_twin/sources/acs.py" if evidence == "code" else "uv.lock"
        sha = hashlib.sha256((repository / file).read_bytes()).hexdigest()
    else:
        with connect(root) as db:
            if evidence == "report":
                sha = db.execute("SELECT object_sha256 FROM release_build_report WHERE valid=1").fetchone()[0]
            else:
                sha = db.execute("SELECT manifest_sha256 FROM release_closure").fetchone()[0]
    path = ArtifactStore(root).path(sha)
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"damaged synthetic dependency")
    with pytest.raises(StorageError):
        builder.read_release(result.manifest.release_id)
    with connect(root) as db:
        assert db.execute("SELECT status FROM release").fetchall() == [("sealed",)]


def test_schema003_root_remains_byte_identical_and_fails_closed(tmp_path, monkeypatch):
    root = tmp_path / "schema003"
    original = storage._migration_files
    with monkeypatch.context() as patch:
        patch.setattr(storage, "_migration_files", lambda name: original(name)[:3])
        storage.initialize(root)
    paths = [root / "baseline.sqlite", root / "private/strategy.sqlite"]
    before = {p: p.read_bytes() for p in paths}
    for action in (storage.initialize, storage.check_initialized):
        with pytest.raises(MigrationError):
            action(root)
    assert {p: p.read_bytes() for p in paths} == before


@pytest.mark.parametrize("failure", ["seal_sql", "interrupted_object"])
def test_failed_or_interrupted_build_preserves_previous_seal_and_active_pointer(sealed, monkeypatch, failure):
    root, builder, result, repository, _ = sealed
    release_id = result.manifest.release_id
    # Test-only preexisting state; this does not provide a production activation command.
    with connect(root) as db:
        db.execute("UPDATE app_state SET active_release_id=? WHERE singleton=1", (release_id,))
        before = db.execute("SELECT * FROM app_state").fetchall()
        old_release = db.execute("SELECT * FROM release").fetchall()
    # Change a public build input to force a new closure identity.
    code = repository / "frontend/index.html"
    code.write_bytes(code.read_bytes() + b"\n# Synthetic integrity-test build revision\n")
    run = result.manifest.content.selection.run_id
    imports = result.manifest.content.selection.import_ids
    report_id = result.manifest.content.selection.candidate_report_id
    try:
        if failure == "seal_sql":
            with connect(root) as db:
                db.execute("CREATE TRIGGER injected_seal_failure BEFORE UPDATE OF status ON release "
                           "WHEN NEW.status='sealed' BEGIN SELECT RAISE(ABORT, 'injected'); END")
            try:
                attempt = builder.build(run, imports, expected_report_id=report_id)
            except StorageError:
                pass
            else:
                assert not attempt.sealed and attempt.manifest is None
            with connect(root) as db:
                db.execute("DROP TRIGGER injected_seal_failure")
        else:
            original = ArtifactStore.put
            retained = []

            def interrupt_after_complete_object(self, content):
                sha = original(self, content)
                retained.append(sha)
                raise KeyboardInterrupt("synthetic interruption after complete object")

            with monkeypatch.context() as patch:
                patch.setattr(ArtifactStore, "put", interrupt_after_complete_object)
                with pytest.raises(KeyboardInterrupt):
                    builder.build(run, imports, expected_report_id=report_id)
            assert retained
            assert ArtifactStore(root).read(retained[0])
        with connect(root) as db:
            assert db.execute("SELECT * FROM app_state").fetchall() == before
            assert db.execute("SELECT * FROM release").fetchall() == old_release
            assert db.execute("SELECT release_id FROM release_closure").fetchall() == [(release_id,)]
        # The previous retained snapshot remains readable after a failed different build.
        assert builder.read_release(release_id) == result.manifest
    finally:
        with connect(root) as db:
            db.execute("UPDATE app_state SET active_release_id=NULL WHERE singleton=1")


@pytest.mark.parametrize("table", ["release", "release_closure", "release_import", "release_version",
                                   "release_dependency", "release_edge", "release_build_report",
                                   "candidate_validation_report", "version", "staged_candidate",
                                   "staging_import", "staging_member", "staging_run", "artifact", "retrieval"])
def test_replace_cannot_bypass_immutable_rows_with_recursive_triggers_off(sealed, table):
    root, builder, result, _, _ = sealed
    with connect(root) as db:
        assert db.execute("PRAGMA recursive_triggers").fetchone()[0] == 0
        if table == "release":
            sql = "INSERT OR REPLACE INTO release SELECT release_id, 'draft', '{}', NULL FROM release LIMIT 1"
        elif table == "artifact":
            sql = ("INSERT OR REPLACE INTO artifact SELECT artifact_id, sha256, byte_length+1, "
                   "media_type, created_at FROM artifact LIMIT 1")
        elif table == "retrieval":
            sql = ("INSERT OR REPLACE INTO retrieval SELECT retrieval_id, artifact_id, source_url, "
                   "retrieved_at, 'corrupt', metadata_json FROM retrieval LIMIT 1")
        elif table == "version":
            sql = ("INSERT OR REPLACE INTO version SELECT version_id, kind, '{}', synthetic, "
                   "recorded_at FROM version LIMIT 1")
        elif table == "candidate_validation_report":
            sql = ("INSERT OR REPLACE INTO candidate_validation_report "
                   "SELECT report_id, run_id, '{}', created_at FROM candidate_validation_report LIMIT 1")
        elif table == "release_build_report":
            sql = ("INSERT OR REPLACE INTO release_build_report SELECT report_id, run_id, "
                   "candidate_report_id, content_id, valid, '{}', object_sha256 "
                   "FROM release_build_report LIMIT 1")
        else:
            sql = f"INSERT OR REPLACE INTO {table} SELECT * FROM {table} LIMIT 1"
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(sql)
    assert builder.read_release(result.manifest.release_id) == result.manifest


@pytest.mark.parametrize("evidence", ["raw", "spec", "code", "lock"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_invalid_build_inputs_produce_no_seal(closure_inputs, evidence, damage):
    root, builder, run, imports, report_id, repository, inputs = closure_inputs
    if evidence in ("raw", "spec"):
        sha = hashlib.sha256(inputs[0][1 if evidence == "raw" else 3]).hexdigest()
        path = ArtifactStore(root).path(sha)
    else:
        path = repository / ("src/chesterfield_twin/sources/acs.py" if evidence == "code" else "uv.lock")
    if damage == "missing":
        path.unlink()
    else:
        # Valid source edits are legitimate build pins; corrupt required code/lock is tested
        # through retained object readback above. Here corrupt means an unsafe symlink.
        if evidence in ("code", "lock"):
            path.unlink()
            path.symlink_to(repository / "README.md")
        else:
            path.write_bytes(b"corrupt synthetic evidence")
    result = builder.build(run, imports, expected_report_id=report_id)
    assert not result.sealed and result.manifest is None
    assert not result.report.content.valid
    with connect(root) as db:
        assert db.execute("SELECT count(*) FROM release").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM release_closure").fetchone()[0] == 0
        assert db.execute("SELECT active_release_id FROM app_state").fetchone()[0] is None
        assert db.execute("SELECT valid FROM release_build_report WHERE report_id=?", (result.report.report_id,)).fetchone() == (0,)


def test_alternate_snapshot_cannot_claim_code_other_than_executing_adapter(closure_inputs):
    root, builder, run, imports, report_id, repository, _ = closure_inputs
    adapter = repository / "src/chesterfield_twin/sources/acs.py"
    adapter.write_bytes(adapter.read_bytes() + b"\n# Alternate nonexecuting adapter revision\n")
    result = builder.build(run, imports, expected_report_id=report_id)
    assert not result.sealed and result.manifest is None
    assert not result.report.content.valid
    with connect(root) as db:
        assert db.execute("SELECT count(*) FROM release").fetchone()[0] == 0


@pytest.mark.parametrize("field,value", [
    ("source_id", "unrelated-source"), ("retrieval_id", "unrelated-retrieval"),
    ("raw_sha256", "0" * 64), ("spec_sha256", "1" * 64),
    ("transform_id", "unrelated-transform"), ("run_id", "unrelated-run"),
])
def test_current_report_metadata_must_equal_verified_imports(closure_inputs, monkeypatch, field, value):
    from chesterfield_twin.domain.candidates import digest
    from chesterfield_twin.domain.validation_reports import ValidationReport
    from chesterfield_twin.storage.staging import _json
    root, builder, run, imports, report_id, _, _ = closure_inputs
    report = CandidateValidation(root).read_report(run, report_id)
    pins = report.content.inputs
    altered = pins[0].model_copy(update={field: value})
    content = report.content.model_copy(update={"inputs": (altered, *pins[1:])})
    forged = ValidationReport(report_id=digest(content.model_dump(mode="json")), content=content)
    assert forged.content.valid
    with connect(root) as db:
        db.execute("INSERT INTO candidate_validation_report(report_id,run_id,content_json) VALUES (?,?,?)",
                   (forged.report_id, run, _json(content.model_dump(mode="json"))))
    monkeypatch.setattr(CandidateValidation, "validate", lambda *args: forged)
    result = builder.build(run, imports, expected_report_id=forged.report_id)
    assert not result.sealed and result.manifest is None
    with connect(root) as db:
        assert db.execute("SELECT count(*) FROM release").fetchone()[0] == 0


@pytest.mark.parametrize("target", ["build_report", "manifest"])
def test_replaced_object_after_initial_readback_cannot_authorize_seal(closure_inputs, monkeypatch, target):
    root, builder, run, imports, report_id, _, _ = closure_inputs
    original = ArtifactStore.read
    damaged = []

    def replace_after_successful_read(self, sha):
        data = original(self, sha)
        if damaged:
            return data
        try:
            payload = json.loads(data)
        except (ValueError, UnicodeDecodeError):
            return data
        if not isinstance(payload, dict):
            return data
        matches = (payload.get("validator_id") == "first-slice-closure/1" and payload.get("content_id")) if target == "build_report" else (
            isinstance(payload.get("content"), dict)
            and payload["content"].get("contract") == "first-slice-release/1")
        if matches:
            self.path(sha).write_bytes(b"replacement after successful first readback")
            damaged.append(sha)
        return data

    monkeypatch.setattr(ArtifactStore, "read", replace_after_successful_read)
    result = builder.build(run, imports, expected_report_id=report_id)
    assert damaged, "failure injection must reach the intended object write/readback boundary"
    assert not result.sealed and result.manifest is None
    with connect(root) as db:
        assert db.execute("SELECT count(*) FROM release").fetchone()[0] == 0
        assert db.execute("SELECT active_release_id FROM app_state").fetchone()[0] is None
