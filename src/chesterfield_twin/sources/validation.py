"""Cross-source candidate checks, not persistence or permission to seal a release."""

from collections import Counter

from chesterfield_twin.domain.candidates import (
    BoundaryCandidate,
    CandidateBatch,
    DocumentCandidate,
    ObservationCandidate,
    ValidationIssue,
)

METRICS = {"median_household_income", "poverty_rate", "household_count"}


def validate_slice(observations: CandidateBatch, boundaries: CandidateBatch,
                   documents: CandidateBatch, *, allow_synthetic: bool = False) -> CandidateBatch:
    """Require the pinned three-source slice. Synthetic opt-in is only for validation tests.

    A passing result does not verify retained-byte availability, create a release, or
    establish provenance closure in storage. Those are subsequent T006/T007 services.
    """
    issues = [i for batch in (observations, boundaries, documents) for i in batch.issues]

    def error(code, message):
        issues.append(ValidationIssue(code=code, message=message))

    expected = ((observations, ObservationCandidate), (boundaries, BoundaryCandidate),
                (documents, DocumentCandidate))
    for batch, candidate_type in expected:
        if not batch.valid or not batch.candidates:
            error("incomplete_source", "Every source must provide a successful nonempty batch")
        if any(not isinstance(c, candidate_type) for c in batch.candidates):
            error("candidate_kind", "Source batch contains an unexpected candidate kind")
    if any(i.severity == "error" for i in issues):
        return CandidateBatch(issues=issues)

    all_candidates = [c for b in (observations, boundaries, documents) for c in b.candidates]
    if not allow_synthetic and any(c.provenance.synthetic for c in all_candidates):
        error("synthetic_evidence", "Synthetic candidates cannot satisfy a real source slice")
    for batch in (observations, boundaries, documents):
        # One spec, artifact and transformation per source in this bounded checkpoint.
        identities = {(c.provenance.source_id, c.provenance.artifact_sha256,
                       c.provenance.spec_sha256, c.provenance.transform_id,
                       c.provenance.synthetic) for c in batch.candidates}
        if len(identities) != 1:
            error("mixed_source_versions", "A source batch mixes snapshot/spec/transform identities")

    places = {c.geography_id for c in boundaries.candidates}
    if len(places) != 75 or len(boundaries.candidates) != 75:
        error("boundary_cardinality", "The pinned county slice requires 75 unique boundaries")
    counts = Counter((c.measurement.geography_id, c.metric_code) for c in observations.candidates)
    if set(counts) != {(g, m) for g in places for m in METRICS} or any(
            count != 1 for count in counts.values()):
        error("geography_join", "Each county boundary must match exactly one observation per metric")
    for c in observations.candidates:
        if (c.measurement.reference_period != "2019-2023"
                or c.measurement.geography_vintage != "2023"
                or c.geography_definition != "2020 Census tracts"):
            error("geography_period", "Observation period or geographic vintage is incompatible")
            break
    pages = {(c.locator.pdf_page, c.locator.printed_page) for c in documents.candidates}
    if len(documents.candidates) != 3 or pages != {(229, "211"), (230, "212"), (231, "213")}:
        error("document_coverage", "The slice requires all three audited PDF/printed page locators")
    if any(i.severity == "error" for i in issues):
        return CandidateBatch(issues=issues)
    return CandidateBatch(candidates=all_candidates, issues=issues)
