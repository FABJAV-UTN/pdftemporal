"""
test_update.py — Integración de la operación UPDATE (PUT /api/v1/documents/{id}).

Solo los metadatos son modificables (custom_name → nombre del documento).
El checksum y el texto extraído no cambian nunca.
"""

URL = "/api/v1/documents/"


async def _upload(async_client, pdf_bytes: bytes, filename: str = "original.pdf") -> dict:
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    response = await async_client.post(URL, files=files)
    assert response.status_code == 201, response.text
    return response.json()


async def test_put_renames_the_document(async_client, fake_pdf_bytes):
    created = await _upload(async_client, fake_pdf_bytes)

    response = await async_client.put(f"{URL}{created['id']}", json={"custom_name": "renombrado.pdf"})

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "renombrado.pdf"


async def test_put_rename_is_persisted(async_client, fake_pdf_bytes):
    created = await _upload(async_client, fake_pdf_bytes)

    await async_client.put(f"{URL}{created['id']}", json={"custom_name": "renombrado.pdf"})
    fetched = await async_client.get(f"{URL}{created['id']}")

    assert fetched.json()["name"] == "renombrado.pdf"


async def test_put_does_not_change_checksum_nor_text(async_client, fake_pdf_bytes):
    created = await _upload(async_client, fake_pdf_bytes)

    response = await async_client.put(f"{URL}{created['id']}", json={"custom_name": "otro.pdf"})

    body = response.json()
    assert body["checksum"] == created["checksum"]
    assert body["extracted_text"] == created["extracted_text"]


async def test_put_on_missing_document_returns_404(async_client):
    response = await async_client.put(f"{URL}000000000000000000000000", json={"custom_name": "x.pdf"})

    assert response.status_code == 404
    assert response.json()["status"] == 404
