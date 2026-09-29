"""Bounded, unpublished excerpts from the audited county budget PDF."""

import hashlib
import io
import re
import tomllib

from pydantic import ValidationError
from pypdf import PdfReader

from chesterfield_twin.domain.candidates import (
    CandidateBatch,
    DocumentCandidate,
    DocumentLocator,
    Retrieval,
)
from chesterfield_twin.sources.common import SourceValidationError, failure, prepare

SOURCE_ID = "chesterfield_fy2025_budget_social_services"
TRANSFORM_ID = "county-budget-pypdf-6.1.1/1"
MAX_BYTES = 32 * 1024 * 1024
MAX_PAGES = 500
MAX_PAGE_TEXT = 100_000
MAX_PAGE_STREAM = 4 * 1024 * 1024
LOCATORS = (
    (229, 211, "Departmental Summaries > Social Services > Description"),
    (230, 212, "Department Blueprint: Priorities, Programs, and Performance"),
    (231, 213, "Housing Choice Voucher; Public Assistance"),
)


def _semantic_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def normalize_document(raw: bytes, retrieval: Retrieval, spec_bytes: bytes, *, synthetic: bool
                       ) -> CandidateBatch:
    """Validate all selected pages before returning exact full-page text spans."""
    try:
        spec, provenance = prepare(
            raw, retrieval, spec_bytes, source_id=SOURCE_ID, transform_id=TRANSFORM_ID,
            synthetic=synthetic, media_types={"application/pdf"}, max_bytes=MAX_BYTES,
        )
        expected = [{"pdf_page": p, "printed_page": printed, "heading": heading}
                    for p, printed, heading in LOCATORS]
        actual = [{k: loc.get(k) for k in ("pdf_page", "printed_page", "heading")}
                  for loc in spec.get("locators", [])]
        if actual != expected or spec.get("fiscal_year") != "FY2025":
            raise SourceValidationError("document_locators", "Specification differs from audited locators")
        caveat = spec.get("scope_caveat", "")
        if not isinstance(caveat, str) or not all(
                name in caveat for name in ("Chesterfield", "Colonial Heights")):
            raise SourceValidationError("document_scope", "Specification lacks two-locality caveat")
        if not raw.startswith(b"%PDF-"):
            raise SourceValidationError("pdf_format", "Source is not a PDF")
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted:
            raise SourceValidationError("pdf_encrypted", "Encrypted PDF is not accepted")
        if not 231 <= len(reader.pages) <= MAX_PAGES:
            raise SourceValidationError("pdf_pages", "PDF is missing selected pages or exceeds page bound")
        if not synthetic and len(reader.pages) != spec.get("page_count"):
            raise SourceValidationError("pdf_pages", "PDF page count differs from audited specification")
        candidates = []
        for page, printed, heading in LOCATORS:
            selected_page = reader.pages[page - 1]
            contents = selected_page.get_contents()
            if contents is not None and len(contents.get_data()) > MAX_PAGE_STREAM:
                raise SourceValidationError("pdf_stream_limit", "Selected page content exceeds bound")
            text = selected_page.extract_text()
            if not text or len(text) > MAX_PAGE_TEXT:
                raise SourceValidationError("pdf_text_limit", "Selected page text is empty or exceeds bound")
            semantic = _semantic_text(text)
            parts = re.split(r" > |; ", heading)
            if not all(_semantic_text(part) in semantic for part in parts):
                raise SourceValidationError("document_heading", f"Audited heading missing on PDF page {page}")
            if "fy2025 budget" not in semantic or "social services" not in semantic:
                raise SourceValidationError("document_heading", "Selected page lacks budget/department evidence")
            if not re.search(rf"(?m)^\s*{printed}\s*$", text):
                raise SourceValidationError("document_printed_page", "Printed page evidence does not match locator")
            if page == 229 and "chesterfield county and the city of colonial heights" not in semantic:
                raise SourceValidationError("document_scope", "Selected document lacks two-locality coverage evidence")
            candidates.append(DocumentCandidate(
                natural_key=f"{SOURCE_ID}/page/{page}/{heading}/FY2025",
                provenance=provenance, title=spec["title"], scope_caveat=caveat,
                excerpt=text, extracted_page_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                locator=DocumentLocator(pdf_page=page, printed_page=str(printed), heading=heading,
                                        text_start=0, text_end=len(text)),
            ))
        return CandidateBatch(candidates=candidates)
    except SourceValidationError as exc:
        return failure(exc.code, str(exc))
    except (UnicodeError, tomllib.TOMLDecodeError, ValidationError, KeyError, TypeError, ValueError):
        return failure("document_validation", "Invalid document or source specification")
    except Exception:
        # Parser errors must not leak extracted content or return partial results.
        return failure("pdf_parse", "PDF could not be safely parsed or extracted")
