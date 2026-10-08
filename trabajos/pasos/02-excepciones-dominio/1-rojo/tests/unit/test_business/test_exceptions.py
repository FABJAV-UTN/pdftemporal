"""
Tests de las excepciones de dominio.

Regla de dependencia (Clean Architecture): la capa de negocio no puede
conocer al framework web. Las excepciones de dominio describen QUÉ pasó;
la traducción a HTTP es responsabilidad de la capa de presentación.
"""

import pytest
from fastapi import HTTPException

from app.business.domain.exceptions import (
    DocumentNotFoundError,
    DomainError,
    DuplicateDocumentError,
    InvalidPDFError,
    PDFTooLargeError,
)

ALL_DOMAIN_ERRORS = [
    DocumentNotFoundError("abc"),
    DuplicateDocumentError("f00"),
    InvalidPDFError(),
    PDFTooLargeError(10),
]


@pytest.mark.parametrize("error", ALL_DOMAIN_ERRORS, ids=lambda e: type(e).__name__)
def test_domain_errors_do_not_depend_on_the_web_framework(error):
    assert isinstance(error, DomainError)
    assert not isinstance(error, HTTPException)


def test_not_found_message_includes_the_id():
    assert "abc123" in str(DocumentNotFoundError("abc123"))


def test_duplicate_message_includes_the_checksum():
    assert "deadbeef" in str(DuplicateDocumentError("deadbeef"))


def test_invalid_pdf_has_a_default_message():
    assert "no es un PDF válido" in str(InvalidPDFError())


def test_too_large_message_includes_the_limit():
    assert "10 MB" in str(PDFTooLargeError(10))
