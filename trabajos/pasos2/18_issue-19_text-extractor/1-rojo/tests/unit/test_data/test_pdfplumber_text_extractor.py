"""Adaptador PdfplumberTextExtractor probado con PDFs reales (sin mockear la librería)."""

import pytest

from app.business.domain.exceptions import InvalidPDFError
from app.data.extractors.pdfplumber_text_extractor import PdfplumberTextExtractor
from tests.unit.fakes import MINIMAL_PDF, TEXT_PDF


@pytest.fixture
def extractor() -> PdfplumberTextExtractor:
    return PdfplumberTextExtractor()


def test_extracts_the_text_of_the_pdf(extractor):
    assert extractor.extract(TEXT_PDF) == "Hola Mundo PDF"


def test_pdf_without_selectable_text_returns_empty_string(extractor):
    assert extractor.extract(MINIMAL_PDF) == ""


@pytest.mark.parametrize("content", [b"%PDF-1.4 roto", b"%PDF", b"no es un pdf"])
def test_unreadable_content_raises_invalid_pdf(extractor, content):
    with pytest.raises(InvalidPDFError):
        extractor.extract(content)
