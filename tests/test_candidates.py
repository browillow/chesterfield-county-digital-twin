"""All examples in this module are synthetic contract probes."""

import hashlib

import pytest
from pydantic import ValidationError

from chesterfield_twin.domain.candidates import CandidateBatch, Retrieval, SourceNumber
from chesterfield_twin.sources.common import SourceValidationError, prepare


def retrieval(**kwargs):
    return Retrieval(**({"url": "https://example.org/source", "retrieved_at": "2026-09-29T12:00:00Z",
                         "status_code": 200, "media_type": "application/json"} | kwargs))


def test_source_number_distinguishes_zero_and_suppression():
    assert SourceNumber(value_state="observed", value="0", raw="0", annotation=None).value == "0"
    with pytest.raises(ValidationError):
        SourceNumber(value_state="suppressed", value="0", raw="-999999999", annotation="N")
    assert SourceNumber(value_state="suppressed", raw="-999999999", annotation="N",
                        reason="Insufficient sample").value is None


@pytest.mark.parametrize("url", ["https://example.org/?key=secret", "https://u:p@example.org/",
                                  "https://example.org/#secret", "http://example.org/"])
def test_retrieval_rejects_credential_fields(url):
    with pytest.raises(ValidationError):
        retrieval(url=url)


def test_envelope_hashes_and_explicit_synthetic_flag():
    spec = b'spec_version=1\nsource_id="example"\nraw_retention="local research"\n'
    _, provenance = prepare(b"[]", retrieval(), spec, source_id="example", transform_id="test/1",
                            synthetic=True, media_types={"application/json"}, max_bytes=10)
    assert provenance.artifact_sha256 == hashlib.sha256(b"[]").hexdigest()
    assert provenance.spec_sha256 == hashlib.sha256(spec).hexdigest()
    assert provenance.synthetic
    with pytest.raises(SourceValidationError, match="HTTP 200"):
        prepare(b"[]", retrieval(status_code=302), spec, source_id="example", transform_id="test/1",
                synthetic=True, media_types={"application/json"}, max_bytes=10)
    assert CandidateBatch().valid
