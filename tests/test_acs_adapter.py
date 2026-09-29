"""Generated synthetic rows; these tests make no live-source access claim."""

import json
from pathlib import Path

import pytest

from chesterfield_twin.domain.candidates import Retrieval
from chesterfield_twin.sources.acs import MAX_BYTES, normalize_acs

SPEC = (Path(__file__).resolve().parents[1] / "source_specs/acs_2023_5yr_subject.toml").read_bytes()
PREFIXES = ["S1901_C01_001", "S1901_C01_012", "S1701_C03_001"]
HEADER = ["NAME"] + [p + s for p in PREFIXES for s in ("E", "EA", "M", "MA")]
HEADER += ["state", "county", "tract"]


def fixture():
    return [HEADER.copy()] + [
        [f"Synthetic tract {i}", "0", None, "2", None, "50000", None, "1000", None,
         "12.5", None, "3.2", None, "51", "041", f"{i:06}"] for i in range(75)]


def retrieval(**changes):
    return Retrieval(**({"url": "https://api.census.gov/data/2023/acs/acs5/subject",
                         "retrieved_at": "2026-09-29T12:00:00Z", "status_code": 200,
                         "media_type": "application/json"} | changes))


def normalize(rows=None, **kwargs):
    return normalize_acs(json.dumps(fixture() if rows is None else rows).encode(),
                         kwargs.pop("retrieval", retrieval()), kwargs.pop("spec", SPEC),
                         synthetic=True, **kwargs)


def test_synthetic_provenance_and_exact_locators():
    batch = normalize()
    assert batch.valid and len(batch.candidates) == 225
    c = batch.candidates[0]
    assert c.metric_code == "median_household_income"
    assert c.measurement.synthetic and c.provenance.synthetic
    assert c.measurement.reference_period == "2019-2023"
    assert c.measurement.geography_vintage == "2023"
    assert c.measurement.unit == "2023 inflation-adjusted dollars per household"
    assert c.measurement.universe == "Households"
    assert c.locator.row == 1 and c.locator.geography_id == "51041000000"
    assert c.locator.fields == tuple("S1901_C01_012" + s for s in ("E", "M", "EA", "MA"))
    assert c.aggregation == "non_additive_median" and c.confidence_level == "90%"


def test_identity_reimport_and_changed_bytes():
    original = normalize().candidates
    repeat = normalize(retrieval=retrieval(retrieved_at="2026-09-30T12:00:00Z")).candidates
    assert [c.fingerprint for c in original] == [c.fingerprint for c in repeat]
    rows = fixture()
    rows[1][5] = "50001"
    changed = normalize(rows).candidates
    assert original[0].natural_key == changed[0].natural_key
    assert original[0].fingerprint != changed[0].fingerprint


@pytest.mark.parametrize("raw,annotation,state", [
    ("0", None, "observed"), ("-999999999", None, "suppressed"),
    ("0", "N", "suppressed"), (None, None, "unavailable"),
    ("-666666666", None, "unavailable"), ("-888888888", None, "unavailable"),
    ("50000", "250,000+", "unavailable"), ("50000", "2,500-", "unavailable"),
])
def test_estimate_annotation_overrides_number(raw, annotation, state):
    rows = fixture()
    rows[1][5:7] = [raw, annotation]
    c = normalize(rows).candidates[0]
    assert c.estimate.value_state == c.measurement.value_state == state
    assert c.estimate.raw == raw and c.estimate.annotation == annotation
    assert c.margin_of_error.value == "1000"
    assert c.estimate.value == (raw if state == "observed" else None)


@pytest.mark.parametrize("raw,annotation,state", [
    ("-222222222", None, "unavailable"), ("-333333333", None, "unavailable"),
    ("-555555555", None, "not_applicable"), ("0", "*****", "not_applicable"),
    ("1000", "**", "unavailable"), (None, None, "unavailable"),
])
def test_moe_independent_annotations(raw, annotation, state):
    rows = fixture()
    rows[1][7:9] = [raw, annotation]
    c = normalize(rows).candidates[0]
    assert c.estimate.value == "50000"
    assert c.margin_of_error.value_state == state and c.margin_of_error.value is None
    assert c.margin_of_error.raw == raw and c.margin_of_error.annotation == annotation


@pytest.mark.parametrize("field,value", [(5, "-777777777"), (6, "?"), (8, "?"),
                                          (5, "NaN"), (7, "Infinity"), (5, "-1"),
                                          (9, "100.1"), (11, "-1"), (5, "abc")])
def test_bad_values_fail_atomically(field, value):
    rows = fixture()
    rows[-1][field] = value
    batch = normalize(rows)
    assert not batch.valid and not batch.candidates and batch.issues


@pytest.mark.parametrize("change", ["duplicate", "county", "tract", "row_count", "header",
                                    "extra_header", "number", "row_shape"])
def test_structural_failures(change):
    rows = fixture()
    if change == "duplicate":
        rows[-1] = rows[1].copy()
    elif change == "county":
        rows[-1][-2] = "042"
    elif change == "tract":
        rows[-1][-1] = "12345"
    elif change == "row_count":
        rows.pop()
    elif change == "header":
        rows[0][1] = "UNKNOWN"
    elif change == "extra_header":
        rows[0].append("EXTRA")
    elif change == "number":
        rows[-1][5] = 5
    else:
        rows[-1].pop()
    batch = normalize(rows)
    assert not batch.valid and not batch.candidates


@pytest.mark.parametrize("raw", [b"<html>Missing Key</html>", b"not-json", b"[]", b"\xff",
                                 b"x" * (MAX_BYTES + 1)])
def test_malformed_response(raw):
    batch = normalize_acs(raw, retrieval(), SPEC, synthetic=True)
    assert not batch.valid and not batch.candidates


@pytest.mark.parametrize("changes", [{"status_code": 302}, {"media_type": "text/html"},
                                      {"url": "https://example.org/data"}])
def test_retrieval_rejected(changes):
    assert not normalize(retrieval=retrieval(**changes)).valid


def test_fixed_spec_validation_and_required_synthetic():
    assert not normalize(spec=SPEC.replace(b'publication_vintage = "2023"',
                                          b'publication_vintage = "2022"')).valid
    assert not normalize(spec=b"broken [").valid
    with pytest.raises(TypeError):
        normalize_acs(b"[]", retrieval(), SPEC)


def test_caller_declared_flag_is_a_trust_boundary_probe():
    # Generated bytes declared false probe caller trust; they are never source evidence.
    rows = fixture()
    valid = normalize_acs(json.dumps(rows).encode(), retrieval(), SPEC, synthetic=False)
    assert valid.valid and not valid.candidates[0].provenance.synthetic
    rows.pop()
    invalid = normalize_acs(json.dumps(rows).encode(), retrieval(), SPEC, synthetic=False)
    assert not invalid.valid and not invalid.candidates


def test_excessive_json_nesting_fails_structurally():
    batch = normalize_acs(b"[" * 2000 + b"]" * 2000, retrieval(), SPEC, synthetic=True)
    assert not batch.valid and not batch.candidates


@pytest.mark.parametrize("raw,annotation", [
    ("-222222222", None), ("-333333333", None), ("-555555555", None),
    ("50000", "**"), ("50000", "***"), ("50000", "*****"),
])
def test_moe_only_nonvalues_invalid_for_estimates(raw, annotation):
    rows = fixture()
    rows[1][5:7] = [raw, annotation]
    batch = normalize(rows)
    assert not batch.valid and not batch.candidates
    assert batch.issues[0].code == "estimate_semantics"


def test_percentage_moe_can_exceed_100():
    rows = fixture()
    rows[1][11] = "125.5"
    batch = normalize(rows)
    assert batch.valid
    c = next(c for c in batch.candidates if c.metric_code == "poverty_rate")
    assert c.margin_of_error.value == "125.5"
    assert c.estimate.value == "12.5"


@pytest.mark.parametrize("annotation", ["median+", "median-", "2,50-", "NaN+", "1e9+",
                                       "250,000+ extra", "9" * 65 + "+"])
def test_unknown_or_unbounded_median_annotations_rejected(annotation):
    rows = fixture()
    rows[1][6] = annotation
    batch = normalize(rows)
    assert not batch.valid and not batch.candidates


def test_numeric_bound_annotation_preserved_and_median_only():
    rows = fixture()
    rows[1][6] = "250,000+"
    c = normalize(rows).candidates[0]
    assert c.estimate.annotation == "250,000+" and c.estimate.raw == "50000"
    assert c.estimate.value is None and c.estimate.value_state == "unavailable"
    rows[1][10] = "2,500-"
    assert not normalize(rows).valid
