"""
Carrera entre dos uploads del mismo PDF.

Si dos requests llegan a la vez, ambas pueden pasar el chequeo previo de
duplicados (get_by_checksum devuelve None) y la que llega segunda choca con
el índice único de MongoDB. El cliente debe recibir 409, no 500.
"""

from unittest.mock import AsyncMock, patch

URL = "/api/v1/documents/"


async def test_duplicate_detected_by_unique_index_returns_409(async_client, fake_pdf_bytes):
    files = {"file": ("doc.pdf", fake_pdf_bytes, "application/pdf")}
    first = await async_client.post(URL, files=files)
    assert first.status_code == 201

    # Simulamos la carrera: el chequeo previo no ve el documento recién insertado.
    with patch(
        "app.data.repositories.mongo_document_repository.MongoDocumentRepository.get_by_checksum",
        new=AsyncMock(return_value=None),
    ):
        second = await async_client.post(URL, files=files)

    assert second.status_code == 409, second.text
    assert second.json()["title"] == "Conflict"
