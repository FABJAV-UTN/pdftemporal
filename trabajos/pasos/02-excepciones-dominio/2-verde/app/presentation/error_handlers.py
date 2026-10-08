"""Traducción de errores de dominio a respuestas HTTP (RFC 9457 - Problem Details).

Es el único lugar que sabe qué status code corresponde a cada error de negocio.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.business.domain.exceptions import (
    DocumentNotFoundError,
    DomainError,
    DuplicateDocumentError,
    InvalidPDFError,
    PDFTooLargeError,
)

PROBLEM_JSON = "application/problem+json"

_HTTP_STATUS: dict[type[DomainError], tuple[int, str]] = {
    DocumentNotFoundError: (404, "Not Found"),
    DuplicateDocumentError: (409, "Conflict"),
    InvalidPDFError: (400, "Bad Request"),
    PDFTooLargeError: (413, "Payload Too Large"),
}
_DEFAULT_STATUS = (400, "Bad Request")


def problem_detail_response(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status, title = _HTTP_STATUS.get(type(exc), _DEFAULT_STATUS)
    return problem_detail_response(status, title, str(exc), str(request.url))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
