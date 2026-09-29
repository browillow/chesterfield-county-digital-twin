"""Generated three-source acceptance fixtures; no live or real ACS evidence."""

import hashlib
import io
import json
import sqlite3
import zipfile

import pytest
import shapefile
from pydantic import ValidationError
from test_acs_adapter import SPEC as ACS_SPEC
from test_acs_adapter import fixture as acs_rows
from test_acs_adapter import retrieval as acs_retrieval
from test_boundary_adapter import RING, WKT
from test_boundary_adapter import SPEC as BOUNDARY_SPEC
from test_document_adapter import SPEC as DOCUMENT_SPEC
from test_document_adapter import pdf
from test_document_adapter import retrieval as document_retrieval

from chesterfield_twin.domain.candidates import Retrieval, digest
from chesterfield_twin.storage import (
    ArtifactStore,
    BaselineRepository,
    PrivateRepository,
    StorageError,
    initialize,
)
from chesterfield_twin.storage.staging import CandidateStaging
from chesterfield_twin.storage.validation import CandidateValidation


def boundary_bytes():
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON) as writer:
        for name, width in (("STATEFP", 2), ("COUNTYFP", 3), ("TRACTCE", 6),
                            ("GEOIDFQ", 20), ("GEOID", 11), ("NAME", 20), ("NAMELSAD", 30)):
            writer.field(name, "C", width)
        writer.field("ALAND", "N", 14, 0)
        writer.field("AWATER", "N", 14, 0)
        for i in range(75):
            tract = f"{i:06}"
            geoid = "51041" + tract
            writer.poly([RING])
            writer.record("51", "041", tract, "1400000US" + geoid, geoid,
                          str(i), f"Synthetic tract {i}", 20, 0)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for suffix, data in (("shp", shp.getvalue()), ("shx", shx.getvalue()),
                             ("dbf", dbf.getvalue()), ("prj", WKT.encode())):
            archive.writestr("synthetic." + suffix, data)
    return output.getvalue()


@pytest.fixture
def selection(tmp_path):
    root = tmp_path / "data"
    initialize(root)
    PrivateRepository(root).add_research_item("sentinel", "PRIVATE-REPORT-SENTINEL")
    staging = CandidateStaging(root)
    run = staging.create_run(synthetic=True)
    inputs = (
        ("acs", json.dumps(acs_rows()).encode(), acs_retrieval(), ACS_SPEC),
        ("boundary", boundary_bytes(), Retrieval(
            url="https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_51_tract_500k.zip",
            retrieved_at="2026-09-29T12:00:00Z", status_code=200,
            media_type="application/zip"), BOUNDARY_SPEC.replace(
                b"expected_state_records = 2186", b"expected_state_records = 75")),
        ("document", pdf(), document_retrieval(), DOCUMENT_SPEC),
    )
    results = tuple(staging.stage(run, *args, synthetic=True) for args in inputs)
    yield root, staging, run, inputs, results
    assert BaselineRepository(root).bootstrap().active_release_id is None


def ids(results):
    return tuple(result.import_id for result in results)


def codes(report):
    return {issue.code for issue in report.content.issues}


def test_complete_synthetic_pins_canonical_repeat_and_private_boundary(selection, monkeypatch):
    root, staging, run, inputs, results = selection
    before = BaselineRepository(root).bootstrap()
    original = sqlite3.connect

    def baseline_only(database, *args, **kwargs):
        assert "strategy.sqlite" not in str(database)
        return original(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", baseline_only)
    service = CandidateValidation(root)
    report = service.validate(run, ids(results))
    assert report.content.valid and report.content.synthetic
    assert not report.content.real_slice_valid
    assert report.content.validator_id == "candidate-set/1+validate-slice/1"
    assert report.report_id == digest(report.content.model_dump(mode="json"))
    assert report == service.validate(run, tuple(reversed(ids(results))))
    assert report == service.read_report(run, report.report_id)
    assert [pin.import_id for pin in report.content.inputs] == sorted(ids(results))
    for args, result in zip(inputs, results):
        pin = next(p for p in report.content.inputs if p.import_id == result.import_id)
        candidate = staging.read_import(run, result.import_id).candidates[0]
        assert pin.verified and pin.synthetic and pin.run_id == run
        assert pin.retrieval_id == result.retrieval_id
        assert pin.source_id == candidate.provenance.source_id
        assert pin.raw_sha256 == hashlib.sha256(args[1]).hexdigest()
        assert pin.spec_sha256 == hashlib.sha256(args[3]).hexdigest()
        assert pin.transform_id == candidate.provenance.transform_id
        assert pin.version_ids == result.version_ids
        assert pin.membership_sha256 == digest(result.version_ids)
    assert tuple(len(r.version_ids) for r in results) == (225, 75, 3)
    assert "PRIVATE-REPORT-SENTINEL" not in report.model_dump_json()
    assert "Synthetic text" not in report.model_dump_json()
    assert BaselineRepository(root).bootstrap() == before
    with sqlite3.connect(root / "baseline.sqlite") as db:
        assert db.execute("SELECT count(*) FROM candidate_validation_report").fetchone()[0] == 1


@pytest.mark.parametrize("kind", ["empty", "missing_id", "missing_source", "duplicate_id",
                                  "duplicate_source"])
def test_invalid_explicit_selections_persist_issues(selection, kind):
    root, staging, run, inputs, results = selection
    chosen = ids(results)
    expected = {"missing_source"}
    if kind == "empty":
        chosen = ()
    elif kind == "missing_id":
        chosen += ("unknown-import",)
        expected = {"missing_import"}
    elif kind == "missing_source":
        chosen = chosen[1:]
    elif kind == "duplicate_id":
        chosen += (chosen[0],)
        expected = {"duplicate_import", "duplicate_source"}
    else:
        duplicate = staging.stage(run, *inputs[0], synthetic=True)
        chosen += (duplicate.import_id,)
        expected = {"duplicate_source"}
    service = CandidateValidation(root)
    report = service.validate(run, chosen)
    assert not report.content.valid and not report.content.real_slice_valid
    assert expected <= codes(report)
    assert service.read_report(run, report.report_id) == report
    if kind == "missing_id":
        pin = next(p for p in report.content.inputs if p.import_id == "unknown-import")
        assert not pin.verified and pin.version_ids == () and pin.source_id is None


@pytest.mark.parametrize("real_target", [False, True])
def test_cross_run_and_mixed_mode_refused(selection, real_target):
    root, staging, _, _, results = selection
    target = staging.create_run(synthetic=not real_target)
    report = CandidateValidation(root).validate(target, ids(results))
    assert not report.content.valid and not report.content.real_slice_valid
    assert {"run_mismatch", "missing_source"} <= codes(report)
    assert ("mixed_mode" in codes(report)) == real_target
    assert all(not pin.verified for pin in report.content.inputs)


@pytest.mark.parametrize("evidence", ["raw", "spec"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_damaged_objects_diagnostic_and_historical_readback(selection, evidence, damage):
    root, _, run, inputs, results = selection
    service = CandidateValidation(root)
    historical = service.validate(run, ids(results))
    raw = inputs[0][1 if evidence == "raw" else 3]
    path = ArtifactStore(root).path(hashlib.sha256(raw).hexdigest())
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"corrupt generated fixture")
    assert service.read_report(run, historical.report_id) == historical
    current = service.validate(run, ids(results))
    assert not current.content.valid and not current.content.real_slice_valid
    assert {"input_integrity", "missing_source"} <= codes(current)
    assert current.report_id != historical.report_id
    pin = next(p for p in current.content.inputs if p.import_id == results[0].import_id)
    old_pin = next(p for p in historical.content.inputs if p.import_id == pin.import_id)
    assert not pin.verified
    assert pin.model_copy(update={"verified": True}) == old_pin
    assert service.read_report(run, current.report_id) == current


def test_report_sql_and_models_immutable(selection):
    root, _, run, _, results = selection
    report = CandidateValidation(root).validate(run, ids(results))
    for model, field, value in ((report, "report_id", "changed"),
                                (report.content, "synthetic", False),
                                (report.content.inputs[0], "verified", False)):
        with pytest.raises(ValidationError, match="frozen"):
            setattr(model, field, value)
    with sqlite3.connect(root / "baseline.sqlite") as db:
        for statement in ("UPDATE candidate_validation_report SET content_json='{}'",
                          "DELETE FROM candidate_validation_report"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                db.execute(statement)
    assert CandidateValidation(root).read_report(run, report.report_id) == report


@pytest.mark.parametrize("chosen", [[], ("",), ("x" * 129,), ("x",) * 17])
def test_malformed_selection_rejected(selection, chosen):
    root, _, run, _, _ = selection
    with pytest.raises(StorageError):
        CandidateValidation(root).validate(run, chosen)


def test_unknown_run_and_wrong_report_run_rejected(selection):
    root, staging, run, _, results = selection
    service = CandidateValidation(root)
    with pytest.raises(StorageError, match="unknown staging run"):
        service.validate("unknown-run", ids(results))
    report = service.validate(run, ids(results))
    other = staging.create_run(synthetic=True)
    with pytest.raises(StorageError, match="unknown validation report"):
        service.read_report(other, report.report_id)


def test_semantic_geography_failure_pins_selected_new_import(selection):
    root, staging, run, inputs, results = selection
    service = CandidateValidation(root)
    prior = service.validate(run, ids(results))
    rows = acs_rows()
    rows[1][-1] = "999999"
    changed_raw = json.dumps(rows).encode()
    changed = staging.stage(run, "acs", changed_raw, inputs[0][2], ACS_SPEC, synthetic=True)
    chosen = (changed.import_id, results[1].import_id, results[2].import_id)
    report = service.validate(run, chosen)
    assert prior.content.valid
    assert not report.content.valid and not report.content.real_slice_valid
    assert "geography_join" in codes(report)
    assert all(pin.verified for pin in report.content.inputs)
    assert {pin.import_id for pin in report.content.inputs} == set(chosen)
    old_pin = next(p for p in prior.content.inputs if p.import_id == results[0].import_id)
    new_pin = next(p for p in report.content.inputs if p.import_id == changed.import_id)
    assert new_pin.raw_sha256 == hashlib.sha256(changed_raw).hexdigest()
    assert new_pin.raw_sha256 != old_pin.raw_sha256
    assert new_pin.version_ids == changed.version_ids
    assert set(new_pin.version_ids).isdisjoint(old_pin.version_ids)
    assert new_pin.membership_sha256 == digest(changed.version_ids)
    for result in results[1:]:
        pin = next(p for p in report.content.inputs if p.import_id == result.import_id)
        assert pin.version_ids == result.version_ids
        assert pin.membership_sha256 == digest(result.version_ids)
    assert report.report_id != prior.report_id
    assert service.read_report(run, report.report_id) == report
