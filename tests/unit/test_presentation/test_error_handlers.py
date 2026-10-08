"""
Tests del traductor de errores de dominio a HTTP (RFC 9457 - Problem Details).

Se prueba con una app FastAPI mínima: cada endpoint lanza un error de dominio
y verificamos el status y el cuerpo que recibe el cliente.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.domain.exceptions import (
    DocumentNotFoundError,
    DuplicateDocumentError,
    InvalidPDFError,
    PDFTooLargeError,
)
from app.presentation.error_handlers import register_error_handlers

CASES = [
    (DocumentNotFoundError("abc"), 404, "Not Found"),
    (DuplicateDocumentError("f00"), 409, "Conflict"),
    (InvalidPDFError(), 400, "Bad Request"),
    (PDFTooLargeError(10), 413, "Payload Too Large"),
]


def make_client(error: Exception) -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    async def boom():
        raise error

    return TestClient(app)


@pytest.mark.parametrize("error,status,title", CASES, ids=lambda c: getattr(c, "__name__", str(c)))
def test_domain_error_is_translated_to_problem_detail(error, status, title):
    response = make_client(error).get("/boom")

    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json() == {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": str(error),
        "instance": "http://testserver/boom",
    }
