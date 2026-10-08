"""
Un archivo que empieza con %PDF pero cuyo contenido está roto no es un PDF válido:
debe rechazarse con 400 y no persistirse.
"""

URL = "/api/v1/documents/"
CORRUPT_PDF = b"%PDF-1.4\nesto no es un pdf de verdad"


async def test_corrupt_pdf_returns_400(async_client):
    files = {"file": ("roto.pdf", CORRUPT_PDF, "application/pdf")}

    response = await async_client.post(URL, files=files)

    assert response.status_code == 400, response.text
    assert response.json()["title"] == "Bad Request"


async def test_corrupt_pdf_is_not_persisted(async_client):
    files = {"file": ("roto.pdf", CORRUPT_PDF, "application/pdf")}

    await async_client.post(URL, files=files)
    listing = await async_client.get(URL)

    assert listing.json() == []
