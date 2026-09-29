"""Synthetic candidate integration probes; never represent county observations."""

import hashlib

import pytest

from chesterfield_twin.domain.candidates import (
    ApiLocator,
    BoundaryCandidate,
    BoundaryLocator,
    CandidateBatch,
    DocumentCandidate,
    DocumentLocator,
    Geometry,
    ObservationCandidate,
    Provenance,
    Retrieval,
    SourceNumber,
    digest,
)
from chesterfield_twin.domain.contracts import Measurement
from chesterfield_twin.sources.validation import METRICS, validate_slice


def provenance(source_id):
    return Provenance(source_id=source_id, artifact_sha256="a" * 64, artifact_bytes=100,
                      spec_sha256="b" * 64, transform_id="synthetic/1", synthetic=True,
                      retention="synthetic fixture only", retrieval=Retrieval(
                          url="https://example.org/fixture", retrieved_at="2026-09-29T12:00:00Z",
                          status_code=200, media_type="application/json"))


@pytest.fixture
def slice_batches():
    observations, boundaries, documents = [], [], []
    geometry = Geometry(type="Polygon", coordinates=[[[-78, 37], [-77, 37], [-77, 38], [-78, 37]]])
    for tract in range(75):
        geoid = f"51041{tract:06}"
        boundaries.append(BoundaryCandidate(
            natural_key=f"boundary/{geoid}", provenance=provenance("boundary"), geography_id=geoid,
            name="Synthetic tract", crs_wkt="synthetic NAD83", geometry=geometry,
            geometry_sha256=digest(geometry.model_dump()), land_area_m2=1, water_area_m2=0,
            locator=BoundaryLocator(archive_member="fixture.shp", record=tract, geography_id=geoid),
            limitations="synthetic fixture"))
        for metric in sorted(METRICS):
            estimate = SourceNumber(value_state="observed", value="0", raw="0", annotation=None)
            observations.append(ObservationCandidate(
                natural_key=f"observation/{geoid}/{metric}", provenance=provenance("acs"),
                metric_code=metric, metric_label="Synthetic example", aggregation="not_for_use",
                measurement=Measurement(claim_class="reported", value_state="observed", value="0",
                                        unit="synthetic units", universe="synthetic universe",
                                        geography_id=geoid, geography_vintage="2023",
                                        reference_period="2019-2023", synthetic=True),
                estimate=estimate, margin_of_error=estimate,
                locator=ApiLocator(row=tract + 1, geography_id=geoid, fields=("E", "M", "EA", "MA"))))
    for page in (229, 230, 231):
        documents.append(DocumentCandidate(
            natural_key=f"document/{page}", provenance=provenance("document"), title="Synthetic",
            scope_caveat="Synthetic example: Chesterfield and Colonial Heights", excerpt="example",
            extracted_page_sha256=hashlib.sha256(b"example").hexdigest(), locator=DocumentLocator(
                pdf_page=page, printed_page=str(page - 18), heading="Synthetic heading",
                text_start=0, text_end=7)))
    return tuple(CandidateBatch(candidates=c) for c in (observations, boundaries, documents))


def test_complete_synthetic_slice_requires_explicit_opt_in(slice_batches):
    rejected = validate_slice(*slice_batches)
    assert not rejected.valid and not rejected.candidates
    assert "synthetic_evidence" in {i.code for i in rejected.issues}
    accepted = validate_slice(*slice_batches, allow_synthetic=True)
    assert accepted.valid and len(accepted.candidates) == 303
    assert all(c.provenance.synthetic for c in accepted.candidates)


@pytest.mark.parametrize("source_index", [0, 1, 2])
def test_missing_source_record_cannot_pass(slice_batches, source_index):
    slice_batches[source_index].candidates.pop()
    result = validate_slice(*slice_batches, allow_synthetic=True)
    assert not result.valid and not result.candidates


def test_join_and_vintage_mismatch_fail(slice_batches):
    slice_batches[0].candidates[0].measurement.geography_vintage = "2022"
    assert "geography_period" in {i.code for i in validate_slice(
        *slice_batches, allow_synthetic=True).issues}


def test_mixed_snapshot_fails(slice_batches):
    slice_batches[0].candidates[0].provenance.artifact_sha256 = "c" * 64
    assert "mixed_source_versions" in {i.code for i in validate_slice(
        *slice_batches, allow_synthetic=True).issues}


def test_wrong_kind_and_upstream_failure_fail(slice_batches):
    obs, bounds, docs = slice_batches
    assert not validate_slice(bounds, obs, docs, allow_synthetic=True).valid
    assert not validate_slice(CandidateBatch(), bounds, docs, allow_synthetic=True).valid


def test_identity_excludes_retrieval_event_but_tracks_transform_and_bytes(slice_batches):
    candidate = slice_batches[0].candidates[0]
    repeated = candidate.model_copy(deep=True)
    repeated.provenance.retrieval = Retrieval(url="https://example.org/fixture",
        retrieved_at="2026-09-30T12:00:00Z", status_code=200, media_type="application/json")
    assert repeated.fingerprint == candidate.fingerprint
    repeated.provenance.transform_id = "synthetic/2"
    assert repeated.fingerprint != candidate.fingerprint
    assert repeated.natural_key == candidate.natural_key
