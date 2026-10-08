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


def build_pdf(padding: int) -> bytes:
    """PDF válido de una página con un objeto de relleno de `padding` bytes (xref correcta)."""
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>",
        b"<</Length %d>>stream\n" % padding + b"0" * padding + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj" % number + body + b"endobj\n"
    xref_position = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF" % (len(objects) + 1, xref_position)
    return bytes(out)


async def test_large_pdf_is_processed_without_touching_disk(async_client):
    pdf = build_pdf(padding=TWO_MB)
    files = {"file": ("grande.pdf", pdf, "application/pdf")}
    original_rollover = SpooledTemporaryFile.rollover

    with patch.object(SpooledTemporaryFile, "rollover", autospec=True, side_effect=original_rollover) as rollover:
        response = await async_client.post(URL, files=files)

    assert response.status_code == 201, response.text
    assert rollover.call_count == 0, "El PDF se escribió en un archivo temporal en disco"


async def test_body_larger_than_limit_is_rejected_before_parsing(async_client):
    too_big = build_pdf(padding=11 * 1024 * 1024)  # límite por defecto: 10 MB
    files = {"file": ("enorme.pdf", too_big, "application/pdf")}
    original_rollover = SpooledTemporaryFile.rollover

    with patch.object(SpooledTemporaryFile, "rollover", autospec=True, side_effect=original_rollover) as rollover:
        response = await async_client.post(URL, files=files)

    assert response.status_code == 413, response.text
    assert response.json()["title"] == "Payload Too Large"
    assert rollover.call_count == 0
