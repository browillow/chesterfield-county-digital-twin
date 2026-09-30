"""Complete synthetic release inspection; activation tests inject verifier authority.

The transaction tests exercise SQLite with real sealed *synthetic* fixture rows,
but stub the verifier's mode only within those tests. They are not real activation
or source acceptance evidence, and production has no synthetic activation override.
"""

import contextlib
import io
import json
import sqlite3
import zipfile
from types import SimpleNamespace

import pytest
from test_release_build import release_fixture  # noqa: F401
from test_validation_reports import ids, selection  # noqa: F401

from chesterfield_twin.domain.application import RecordQuery
from chesterfield_twin.storage import BaselineRepository, StorageBusyError, StorageError, initialize
from chesterfield_twin.storage.application import ApplicationError, ReleaseApplication
from chesterfield_twin.storage.validation import CandidateValidation


@pytest.fixture
def application_fixture(release_fixture):  # noqa: F811
    root, staging, run, selected, report, repository, builder = release_fixture
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues
    application = ReleaseApplication(root, repository)
    return application, built.manifest, release_fixture


def error(code, method, *args, **kwargs):
    with pytest.raises(ApplicationError) as caught:
        method(*args, **kwargs)
    assert caught.value.code == code
    assert str(args) not in str(caught.value)


def pointer(root):
    return BaselineRepository(root).bootstrap().active_release_id


def build_second(fixture, inputs):
    _, staging, run, _, _, _, builder = fixture
    selected = tuple(staging.stage(run, *item, synthetic=True).import_id for item in inputs)
    report = CandidateValidation(staging.root).validate(run, selected)
    built = builder.build(run, selected, expected_report_id=report.report_id)
    assert built.sealed, built.report.content.issues
    return built.manifest


def test_complete_projection_and_public_only_graph(application_fixture, monkeypatch):
    app, manifest, fixture = application_fixture
    root, staging, run, selected, _, repository, _ = fixture
    before = (root / "private/strategy.sqlite").read_bytes()
    original = sqlite3.connect

    def baseline_only(path, *args, **kwargs):
        assert "strategy.sqlite" not in str(path)
        connection = original(path, *args, **kwargs)
        connection.set_trace_callback(lambda sql: pytest.fail(sql) if "ATTACH" in sql else None)
        return connection

    monkeypatch.setattr(sqlite3, "connect", baseline_only)
    summary = app.summary(manifest.release_id)
    assert summary.synthetic and summary.current_dependencies_verified
    assert summary.counts == {"observation": 225, "boundary": 75, "document_excerpt": 3}
    assert summary.coverage == next(n.payload for n in manifest.content.nodes if n.kind == "coverage")
    assert summary.sources == tuple(n for n in manifest.content.nodes if n.kind == "source")
    assert summary.candidate_report_id == manifest.content.selection.candidate_report_id
    assert summary.build_report_id == manifest.report_id
    records = app.records(manifest.release_id, query=RecordQuery(limit=303))
    expected = {c.fingerprint: c for import_id in selected
                for c in staging.read_import(run, import_id).candidates}
    assert records.total == 303 and records.synthetic
    assert tuple(r.version_id for r in records.records) == manifest.content.selection.version_ids
    assert {r.version_id: r.candidate for r in records.records} == expected
    for kind in ("observation", "boundary", "document_excerpt"):
        record = next(r for r in records.records if r.candidate.kind == kind)
        evidence = app.evidence(manifest.release_id, record.version_id)
        assert evidence.record == record and evidence.synthetic
        assert tuple(n.node_id for n in evidence.nodes) == tuple(sorted(n.node_id for n in evidence.nodes))
        assert tuple((e.from_node, e.role, e.to_node) for e in evidence.edges) == tuple(sorted(
            (e.from_node, e.role, e.to_node) for e in evidence.edges))
        included = {n.node_id for n in evidence.nodes}
        assert all(e.from_node in included and e.to_node in included for e in evidence.edges)
        candidates = [n for n in evidence.nodes if n.kind == "candidate"]
        assert len(candidates) == (2 if kind == "observation" else 1)
        assert {"source", "spec", "retrieval", "raw", "transform"} <= {n.kind for n in evidence.nodes}
        assert not {"query", "config", "code", "dependency", "schema", "coverage"} & {
            n.kind for n in evidence.nodes}
        rendered = evidence.model_dump_json()
        assert "PRIVATE-REPORT-SENTINEL" not in rendered
        assert str(root) not in rendered and str(repository) not in rendered
        if kind == "boundary":
            assert record.candidate.crs == "EPSG:4269"
        if kind == "document_excerpt":
            assert record.candidate.geographic_scope == ("51041", "51570")
            assert record.candidate.provenance.redistribution == "unconfirmed"
    assert (root / "private/strategy.sqlite").read_bytes() == before
    assert app.bootstrap().model_dump() == {
        "api_version": "v1", "active_release_id": None, "has_baseline": False,
        "capabilities": ["release_activation", "release_reads", "release_comparison"],
    }
    error("synthetic_release", app.activate, manifest.release_id)
    assert pointer(root) is None


def test_filters_pagination_and_unknown_values(application_fixture, selection):  # noqa: F811
    app, manifest, fixture = application_fixture
    release = manifest.release_id
    all_records = app.records(release, query=RecordQuery(limit=303)).records
    for kind, count in (("observation", 225), ("boundary", 75), ("document_excerpt", 3)):
        page = app.records(release, query=RecordQuery(kind=kind, limit=303))
        assert page.total == count
        assert all(r.candidate.kind == kind for r in page.records)
    assert app.records(release, query=RecordQuery(geography_id="51041000000")).total == 4
    assert app.records(release, query=RecordQuery(metric_code="poverty_rate")).total == 75
    page = app.records(release, query=RecordQuery(
        geography_id="51041000000", metric_code="poverty_rate"))
    assert page.total == 1 and page.records[0].candidate.metric_code == "poverty_rate"
    assert app.records(release, query=RecordQuery(
        kind="boundary", metric_code="poverty_rate")).total == 0
    assert app.records(release, query=RecordQuery(geography_id="51041999999")).records == ()
    assert app.records(release).records == all_records[:100]
    assert app.records(release, query=RecordQuery(offset=100, limit=203)).records == all_records[100:]
    assert app.records(release, query=RecordQuery(offset=303, limit=1)).records == ()
    assert any(r.candidate.measurement.value == "0" for r in all_records
               if r.candidate.kind == "observation")
    inputs = list(selection[3])
    rows = json.loads(inputs[0][1])
    rows[1][5:7] = [None, None]
    rows[2][5:7] = ["-999999999", None]
    rows[3][7:9] = [None, None]
    inputs[0] = ("acs", json.dumps(rows).encode(), *inputs[0][2:])
    unknown_release = build_second(fixture, inputs)
    unknown_records = app.records(unknown_release.release_id, query=RecordQuery(limit=303)).records
    unknowns = [r.candidate for r in unknown_records if r.candidate.kind == "observation"
                and r.candidate.measurement.value_state != "observed"]
    assert {c.measurement.value_state for c in unknowns} == {"unavailable", "suppressed"}
    assert all(c.measurement.value is None and c.measurement.reason for c in unknowns)
    assert any(r.candidate.margin_of_error.value_state == "unavailable" for r in unknown_records
               if r.candidate.kind == "observation")
    for query in ({}, RecordQuery.model_construct(limit=0), RecordQuery.model_construct(offset=304),
                  RecordQuery.model_construct(limit=True), RecordQuery.model_construct(kind="arbitrary")):
        error("invalid_query", app.records, release, query=query)


def test_input_validation_precedes_storage(tmp_path, monkeypatch):
    app = ReleaseApplication(tmp_path / "absent", tmp_path)
    monkeypatch.setattr(app.staging, "_locked", lambda: pytest.fail("invalid selection reached storage"))
    for invalid in ("", "A" * 64, "f" * 63, None, 1, "f" * 64 + "\n"):
        error("invalid_query", app.summary, invalid)
        error("invalid_query", app.activate, invalid)
        error("invalid_query", app.records, invalid)
        error("invalid_query", app.evidence, "f" * 64, invalid)
        error("invalid_query", app.compare, "f" * 64, invalid)
    error("invalid_query", app.records, "f" * 64, query=RecordQuery.model_construct(limit=304))


def test_unknown_draft_and_unselected_are_not_fallbacks(application_fixture, selection):  # noqa: F811
    app, manifest, fixture = application_fixture
    root, staging, run, _, _, _, _ = fixture
    missing = "0" * 64
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("INSERT INTO release VALUES (?,'draft','{}',NULL)", ("1" * 64,))
    for release in (missing, "1" * 64):
        error("unknown_release", app.summary, release)
        error("unknown_release", app.records, release)
        error("unknown_release", app.evidence, release, manifest.content.selection.version_ids[0])
        error("unknown_release", app.activate, release)
        error("unknown_release", app.compare, manifest.release_id, release)
    inputs = selection[3]
    changed_rows = json.loads(inputs[0][1])
    changed_rows[1][0] = "9999"
    changed = staging.stage(run, "acs", json.dumps(changed_rows).encode(), *inputs[0][2:], synthetic=True)
    for version in (missing, changed.version_ids[0]):
        error("unknown_evidence", app.evidence, manifest.release_id, version)
    assert app.records(manifest.release_id, query=RecordQuery(limit=303)).total == 303


@pytest.mark.parametrize("dependency", ["raw", "spec", "code", "candidate_report", "build_report", "manifest"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_current_dependencies_fail_without_repair(application_fixture, dependency, damage, monkeypatch):
    app, manifest, fixture = application_fixture
    root, _, _, _, _, _, builder = fixture
    nodes = manifest.content.nodes
    if dependency in ("raw", "spec"):
        sha = next(n.key for n in nodes if n.kind == dependency)
    elif dependency == "code":
        code = next(n for n in nodes if n.kind == "code")
        sha = next(f["sha256"] for f in code.payload["files"] if f["path"] == "uv.lock")
    elif dependency == "candidate_report":
        sha = next(n.payload["candidate_report_sha256"] for n in nodes if n.kind == "query")
    elif dependency == "build_report":
        with sqlite3.connect(root / "baseline.sqlite") as db:
            sha = db.execute("SELECT object_sha256 FROM release_build_report WHERE report_id=?",
                             (manifest.report_id,)).fetchone()[0]
    else:
        sha = manifest.release_id
    path = app.staging.objects.path(sha)
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"broken synthetic retained evidence")
    state = (root / "baseline.sqlite").read_bytes()
    objects = {p.relative_to(root): p.read_bytes() for p in (root / "objects").rglob("*") if p.is_file()}
    monkeypatch.setattr(app.staging.objects, "put", lambda *a: pytest.fail("read attempted repair"))
    for method, arguments in ((app.summary, (manifest.release_id,)),
                              (app.records, (manifest.release_id,)),
                              (app.evidence, (manifest.release_id, manifest.content.selection.version_ids[0])),
                              (app.compare, (manifest.release_id, manifest.release_id)),
                              (app.activate, (manifest.release_id,))):
        error("release_unavailable", method, *arguments)
    if dependency in ("raw", "spec", "code"):
        assert builder.read_release(manifest.release_id, verify_current=False) == manifest
    assert state == (root / "baseline.sqlite").read_bytes()
    assert objects == {p.relative_to(root): p.read_bytes() for p in (root / "objects").rglob("*") if p.is_file()}


def test_pinned_retrieval_support_and_comparison(application_fixture, selection):  # noqa: F811
    app, first, fixture = application_fixture
    inputs = selection[3]
    before = app.records(first.release_id, query=RecordQuery(limit=303))
    first_evidence = app.evidence(first.release_id, before.records[0].version_id)
    later = tuple((source, raw, retrieval.model_copy(update={
        "retrieved_at": retrieval.retrieved_at.replace(day=30)}), spec)
        for source, raw, retrieval, spec in inputs)
    second = build_second(fixture, later)
    assert first.release_id != second.release_id
    # Fixture-only pointer injection proves pinned reads ignore the active selection;
    # production activation rejects these honestly synthetic sealed releases.
    with sqlite3.connect(fixture[0] / "baseline.sqlite") as db:
        db.execute("UPDATE app_state SET active_release_id=?", (second.release_id,))
    try:
        assert app.records(first.release_id, query=RecordQuery(limit=303)) == before
        assert app.evidence(first.release_id, before.records[0].version_id) == first_evidence
    finally:
        with sqlite3.connect(fixture[0] / "baseline.sqlite") as db:
            db.execute("UPDATE app_state SET active_release_id=NULL")
    comparison = app.compare(first.release_id, second.release_id)
    assert comparison.unchanged_count == 303 and comparison.changes == ()
    assert comparison.old_synthetic and comparison.new_synthetic
    second_records = app.records(second.release_id, query=RecordQuery(limit=303))
    assert tuple(r.version_id for r in second_records.records) == tuple(r.version_id for r in before.records)
    assert all(r.candidate.provenance.retrieval.retrieved_at.day == 30 for r in second_records.records)
    assert all(r.candidate.provenance.retrieval.retrieved_at.day == 29 for r in before.records)
    assert app.compare(first.release_id, first.release_id).unchanged_count == 303


def test_complete_changed_added_removed_natural_keys(application_fixture, selection):  # noqa: F811
    app, first, fixture = application_fixture
    inputs = list(selection[3])
    rows = json.loads(inputs[0][1])
    rows[-1][-1] = "000075"
    inputs[0] = ("acs", json.dumps(rows).encode(), *inputs[0][2:])
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(inputs[1][1])) as old, zipfile.ZipFile(output, "w") as new:
        for name in old.namelist():
            data = old.read(name)
            if name.endswith(".dbf"):
                data = data.replace(b"000074", b"000075")
            new.writestr(name, data)
    inputs[1] = ("boundary", output.getvalue(), *inputs[1][2:])
    second = build_second(fixture, inputs)
    comparison = app.compare(first.release_id, second.release_id)
    assert comparison.unchanged_count == 3
    assert {kind: sum(c.change == kind for c in comparison.changes)
            for kind in ("changed", "added", "removed")} == {"changed": 296, "added": 4, "removed": 4}
    assert tuple((c.kind, c.natural_key) for c in comparison.changes) == tuple(sorted(
        (c.kind, c.natural_key) for c in comparison.changes))
    for change in comparison.changes:
        assert (change.old_version_id is None) == (change.change == "added")
        assert (change.new_version_id is None) == (change.change == "removed")


@pytest.fixture
def synthetic_transaction_fixture(application_fixture, selection, monkeypatch):  # noqa: F811
    app, prior, fixture = application_fixture
    inputs = tuple((source, raw, retrieval.model_copy(update={"etag": '"synthetic transaction"'}), spec)
                   for source, raw, retrieval, spec in selection[3])
    target = build_second(fixture, inputs)
    root = fixture[0]
    calls = []

    def verifier(db, release_id, *, verify_current):
        assert db.in_transaction and verify_current is True
        calls.append(release_id)
        return SimpleNamespace(content=SimpleNamespace(synthetic=False))

    monkeypatch.setattr(app.builder, "_read", verifier)
    try:
        yield app, prior, target, root, calls
    finally:
        with sqlite3.connect(root / "baseline.sqlite") as db:
            db.execute("UPDATE app_state SET active_release_id=NULL")


def test_synthetic_transaction_stub_null_prior_commit_and_same_id(synthetic_transaction_fixture):
    app, prior, target, root, calls = synthetic_transaction_fixture
    first = app.activate(prior.release_id)
    assert first.previous_release_id is None and first.changed and pointer(root) == prior.release_id
    switched = app.activate(target.release_id)
    assert switched.previous_release_id == prior.release_id and switched.changed
    assert pointer(root) == target.release_id and not switched.synthetic
    same = app.activate(target.release_id)
    assert not same.changed and same.previous_release_id == target.release_id
    assert calls == [prior.release_id, target.release_id, target.release_id]
    assert app.bootstrap().active_release_id == target.release_id


@pytest.mark.parametrize("failure", ["verify", "before_update", "update", "commit",
                                     "interrupt_verify", "interrupt_commit"])
def test_synthetic_transaction_stub_failure_preserves_sealed_prior(
        synthetic_transaction_fixture, failure, monkeypatch):
    app, prior, target, root, _ = synthetic_transaction_fixture
    app.activate(prior.release_id)
    original_read = app.builder._read
    original_connect = app.staging._connect
    exception = KeyboardInterrupt if failure.startswith("interrupt") else StorageError

    def verifier(*args, **kwargs):
        if failure in ("verify", "interrupt_verify"):
            raise exception("injected transaction failure")
        return original_read(*args, **kwargs)

    class InjectedConnection:
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def execute(self, sql, *args):
            if failure == "before_update" and sql.startswith("UPDATE app_state"):
                raise StorageError("injected failure before update")
            if failure == "update" and sql.startswith("UPDATE app_state"):
                self.connection.execute(sql, *args)
                raise StorageError("injected failure after update")
            return self.connection.execute(sql, *args)

        def commit(self):
            assert pointer(root) == prior.release_id
            raise exception("injected failure before commit")

    @contextlib.contextmanager
    def connection(**kwargs):
        with original_connect(**kwargs) as db:
            yield (InjectedConnection(db) if failure in
                   ("before_update", "update", "commit", "interrupt_commit") else db)

    monkeypatch.setattr(app.builder, "_read", verifier)
    monkeypatch.setattr(app.staging, "_connect", connection)
    with pytest.raises(exception):
        app.activate(target.release_id)
    assert pointer(root) == prior.release_id


def test_synthetic_transaction_stub_same_id_reverification_failure(synthetic_transaction_fixture, monkeypatch):
    app, prior, _, root, _ = synthetic_transaction_fixture
    app.activate(prior.release_id)
    monkeypatch.setattr(app.builder, "_read", lambda *a, **k: (_ for _ in ()).throw(StorageError("broken")))
    error("release_unavailable", app.activate, prior.release_id)
    assert pointer(root) == prior.release_id


def test_mixed_comparison_rejected_after_both_verifications(application_fixture, monkeypatch):
    app, manifest, _ = application_fixture
    original = app.builder._read
    calls = []

    def verifier(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(args[1])
        return (result if len(calls) == 1 else result.model_copy(update={
            "content": result.content.model_copy(update={"synthetic": False})}))

    monkeypatch.setattr(app.builder, "_read", verifier)
    error("synthetic_release", app.compare, manifest.release_id, manifest.release_id)
    assert calls == [manifest.release_id, manifest.release_id]


def test_bootstrap_invalid_active_state_fails_closed(application_fixture):
    app, manifest, fixture = application_fixture
    root = fixture[0]
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("UPDATE app_state SET active_release_id=?", (manifest.release_id,))
    try:
        error("release_unavailable", app.bootstrap)
        assert pointer(root) == manifest.release_id
    finally:
        with sqlite3.connect(root / "baseline.sqlite") as db:
            db.execute("UPDATE app_state SET active_release_id=NULL")
    # Deliberately corrupted pointer via a raw fixture connection with FK checks
    # disabled. Missing referenced rows cannot create a valid active baseline.
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("UPDATE app_state SET active_release_id='malformed-pointer'")
    try:
        error("release_unavailable", app.bootstrap)
        error("release_unavailable", app.activate, manifest.release_id)
        assert pointer(root) == "malformed-pointer"
    finally:
        with sqlite3.connect(root / "baseline.sqlite") as db:
            db.execute("UPDATE app_state SET active_release_id=NULL")
    with sqlite3.connect(root / "baseline.sqlite") as db:
        db.execute("DELETE FROM app_state")
    error("release_unavailable", app.bootstrap)
    error("release_unavailable", app.activate, manifest.release_id)


def test_actual_sqlite_contention_is_storage_busy(tmp_path, monkeypatch):
    root = tmp_path / "busy"
    initialize(root)
    app = ReleaseApplication(root, tmp_path)
    import chesterfield_twin.storage as storage
    monkeypatch.setattr(storage, "_BUSY_TIMEOUT_MS", 1)
    with sqlite3.connect(root / "baseline.sqlite") as writer:
        writer.execute("BEGIN IMMEDIATE")
        with pytest.raises(StorageBusyError):
            app.activate("f" * 64)
        assert pointer(root) is None


def test_read_comparison_uses_one_explicit_snapshot(application_fixture, monkeypatch):
    app, manifest, _ = application_fixture
    original = app.builder._read
    connections = []

    def verified(db, *args, **kwargs):
        assert db.in_transaction
        connections.append(db)
        return original(db, *args, **kwargs)

    monkeypatch.setattr(app.builder, "_read", verified)
    result = app.compare(manifest.release_id, manifest.release_id)
    assert result.unchanged_count == 303 and len(connections) == 2
    assert connections[0] is connections[1]
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")
