"""
Consigna Etapa 1: "El documento no debe ser persistido temporalmente mientras se procesa".

Starlette guarda los archivos de un multipart en un SpooledTemporaryFile: mientras
el archivo es chico vive en memoria, pero si supera el umbral hace `rollover()` y
pasa a un archivo temporal en disco. Verificamos que un PDF grande (pero dentro del
límite permitido) se procese sin ese rollover.
"""

from tempfile import SpooledTemporaryFile
from unittest.mock import patch

URL = "/api/v1/documents/"
TWO_MB = 2 * 1024 * 1024


async def test_large_pdf_is_processed_without_touching_disk(async_client, pdf_factory):
    pdf = pdf_factory(padding=TWO_MB)
    files = {"file": ("grande.pdf", pdf, "application/pdf")}
    original_rollover = SpooledTemporaryFile.rollover

    with patch.object(SpooledTemporaryFile, "rollover", autospec=True, side_effect=original_rollover) as rollover:
        response = await async_client.post(URL, files=files)

    assert response.status_code == 201, response.text
    assert rollover.call_count == 0, "El PDF se escribió en un archivo temporal en disco"


async def test_body_larger_than_limit_is_rejected_before_parsing(async_client, pdf_factory):
    too_big = pdf_factory(padding=11 * 1024 * 1024)  # límite por defecto: 10 MB
    files = {"file": ("enorme.pdf", too_big, "application/pdf")}
    original_rollover = SpooledTemporaryFile.rollover

    with patch.object(SpooledTemporaryFile, "rollover", autospec=True, side_effect=original_rollover) as rollover:
        response = await async_client.post(URL, files=files)

    assert response.status_code == 413, response.text
    assert response.json()["title"] == "Payload Too Large"
    assert rollover.call_count == 0
