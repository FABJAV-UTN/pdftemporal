import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_download_text_file(async_client: AsyncClient, fake_pdf_bytes: bytes):
    original_filename = "contrato_para_descarga.pdf"
    files = {"file": (original_filename, fake_pdf_bytes, "application/pdf")}

    # Upload
    response = await async_client.post("/api/v1/documents/", files=files)
    assert response.status_code == 201
    body = response.json()
    doc_id = body["id"]

    # Download
    download_resp = await async_client.get(f"/api/v1/documents/{doc_id}/download")
    assert download_resp.status_code == 200

    # Content-Disposition filename should be original name with .txt extension
    disposition = download_resp.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "contrato_para_descarga.txt" in disposition

    # Body should equal the extracted_text stored
    assert download_resp.text == body["extracted_text"]


@pytest.mark.asyncio
async def test_download_nonexistent_returns_problemdetail(async_client: AsyncClient):
    # Use an ID that is extremely unlikely to exist
    missing_id = "64b6f0f0c2f9a1b2c3d4e5f6"
    resp = await async_client.get(f"/api/v1/documents/{missing_id}/download")
    assert resp.status_code == 404
    body = resp.json()
    assert set(["type", "title", "status", "detail", "instance"]).issubset(set(body.keys()))
    assert body["status"] == 404


@pytest.mark.asyncio
async def test_download_with_non_ascii_name(async_client: AsyncClient, fake_pdf_bytes: bytes):
    files = {"file": ("informe_文件.pdf", fake_pdf_bytes, "application/pdf")}
    doc_id = (await async_client.post("/api/v1/documents/", files=files)).json()["id"]

    resp = await async_client.get(f"/api/v1/documents/{doc_id}/download")

    assert resp.status_code == 200
    assert "filename*=UTF-8''informe_%E6%96%87%E4%BB%B6.txt" in resp.headers["content-disposition"]
