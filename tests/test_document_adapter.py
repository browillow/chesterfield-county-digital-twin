"""Synthetic PDF probes; no county source text or bytes are fixtures."""

import hashlib
import io
from pathlib import Path

import pytest
from pydantic import ValidationError
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from chesterfield_twin.domain.candidates import DocumentCandidate, Retrieval
from chesterfield_twin.sources.documents import LOCATORS, normalize_document

SPEC = Path("source_specs/chesterfield_fy2025_social_services.toml").read_bytes()
TEXTS = {
    229: "FY2025 Budget Departmental Summaries\nSocial Services\nDescription\n"
         "Chesterfield County and the City of Colonial Heights\nSynthetic text\n211",
    230: "FY2025 Budget Departmental Summaries\nSocial Services\n"
         "Department Blueprint: Priorities, Programs, and Performance\n212",
    231: "FY2025 Budget Departmental Summaries\nSocial Services\n"
         "Housing Choice Voucher\nPublic Assistance\n213",
}


def pdf(texts=None, *, pages=231, encrypted=False):
    writer = PdfWriter()
    texts = TEXTS if texts is None else texts
    for number in range(1, pages + 1):
        page = writer.add_blank_page(width=612, height=792)
        if number in texts:
            escaped = texts[number].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream = DecodedStreamObject()
            stream.set_data(f"BT ({escaped}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("synthetic-password")
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def retrieval(**changes):
    return Retrieval(**({"url": "https://www.chesterfield.gov/DocumentCenter/View/36170/",
                         "retrieved_at": "2026-09-29T12:00:00Z", "status_code": 200,
                         "media_type": "application/pdf"} | changes))


def normalize(raw=None, **kwargs):
    return normalize_document(pdf() if raw is None else raw, retrieval(), SPEC,
                              synthetic=True, **kwargs)


def test_exact_text_locators_hashes_and_repeat_identity():
    raw = pdf()
    batch = normalize(raw)
    assert batch.valid and len(batch.candidates) == 3
    reader = PdfReader(io.BytesIO(raw))
    repeat = normalize_document(raw, retrieval(retrieved_at="2026-09-30T12:00:00Z"),
                                SPEC, synthetic=True)
    for candidate, repeated, (page, printed, heading) in zip(batch.candidates,
                                                           repeat.candidates, LOCATORS):
        text = reader.pages[page - 1].extract_text()
        assert candidate.excerpt == text[candidate.locator.text_start:candidate.locator.text_end]
        assert candidate.extracted_page_sha256 == hashlib.sha256(text.encode()).hexdigest()
        assert candidate.locator.printed_page == str(printed)
        assert candidate.locator.heading == heading
        assert candidate.fingerprint == repeated.fingerprint
        assert candidate.geographic_scope == ("51041", "51570")
        assert candidate.reference_period == "FY2025"
        assert candidate.provenance.synthetic
        assert candidate.provenance.redistribution == "unconfirmed"


def test_changed_bytes_keep_natural_key_change_identity():
    before = normalize()
    after = normalize(pdf(TEXTS | {229: TEXTS[229].replace("Synthetic text", "Changed text")}))
    assert after.valid
    assert before.candidates[0].natural_key == after.candidates[0].natural_key
    assert before.candidates[0].fingerprint != after.candidates[0].fingerprint


@pytest.mark.parametrize(("raw", "code"), [
    (b"%PDF-broken", "pdf_parse"), (b"<html>error</html>", "html_response"),
    (pdf(pages=230), "pdf_pages"), (pdf(encrypted=True), "pdf_encrypted"),
    (pdf(TEXTS | {231: TEXTS[231].replace("Public Assistance", "Other")}), "document_heading"),
    (pdf(TEXTS | {229: TEXTS[229].replace("Colonial Heights", "Other")}), "document_scope"),
    (pdf(TEXTS | {230: TEXTS[230].replace("212", "999")}), "document_printed_page"),
    (pdf(TEXTS | {231: ""}), "pdf_text_limit"),
])
def test_bad_pdf_fails_atomically(raw, code):
    result = normalize(raw)
    assert not result.valid and not result.candidates
    assert result.issues[0].code == code


@pytest.mark.parametrize(("changes", "code"), [
    ({"status_code": 404}, "http_status"), ({"media_type": "text/plain"}, "media_type"),
    ({"url": "https://example.org/other"}, "source_url"),
])
def test_bad_envelope(changes, code):
    result = normalize_document(pdf(), retrieval(**changes), SPEC, synthetic=True)
    assert not result.candidates and result.issues[0].code == code


def test_artifact_pin_and_locator_mismatch():
    result = normalize_document(pdf(), retrieval(), SPEC, synthetic=False)
    assert result.issues[0].code == "artifact_pin"
    result = normalize_document(pdf(), retrieval(), SPEC.replace(b"pdf_page = 229", b"pdf_page = 228"),
                                synthetic=True)
    assert result.issues[0].code == "document_locators"


def test_offsets_reject_mismatched_excerpt_length():
    candidate = normalize().candidates[0].model_dump()
    candidate["locator"]["text_end"] += 1
    with pytest.raises(ValidationError, match="Excerpt length"):
        DocumentCandidate.model_validate(candidate)


@pytest.mark.parametrize(("limit", "code"), [
    ("MAX_BYTES", "byte_limit"), ("MAX_PAGES", "pdf_pages"),
    ("MAX_PAGE_TEXT", "pdf_text_limit"), ("MAX_PAGE_STREAM", "pdf_stream_limit"),
])
def test_resource_bounds(monkeypatch, limit, code):
    monkeypatch.setattr("chesterfield_twin.sources.documents." + limit, 1)
    result = normalize()
    assert not result.candidates and result.issues[0].code == code
