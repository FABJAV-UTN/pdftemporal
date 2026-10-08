"""Tests del middleware que limita el tamaño del body."""

import httpx
import pytest
from fastapi import FastAPI, Request

from app.presentation.middlewares.body_size_limit import BodySizeLimitMiddleware

LIMIT = 1000


def make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=LIMIT)

    @app.post("/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    return app


async def post(content) -> httpx.Response:
    transport = httpx.ASGITransport(app=make_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/echo", content=content)


async def test_body_within_limit_passes():
    response = await post(b"x" * LIMIT)

    assert response.status_code == 200
    assert response.json() == {"size": LIMIT}


async def test_declared_length_over_limit_returns_413():
    response = await post(b"x" * (LIMIT + 1))

    assert response.status_code == 413
    assert response.json()["title"] == "Payload Too Large"


async def test_chunked_body_over_limit_returns_413():
    """Sin Content-Length (transferencia por chunks) se corta al superar el límite."""

    async def chunks():
        for _ in range(5):
            yield b"x" * 300

    response = await post(chunks())

    assert response.status_code == 413
    assert response.json()["instance"] == "http://test/echo"


async def test_chunked_multipart_over_limit_returns_413_not_400():
    """Con un endpoint de upload real, FastAPI no debe convertir el corte en un 400 de parseo."""
    from fastapi import File, UploadFile

    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=LIMIT)

    @app.post("/upload")
    async def upload(file: UploadFile = File(...)):
        return {"size": len(await file.read())}

    boundary = b"limite"
    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="a.pdf"\r\n'
        b"Content-Type: application/pdf\r\n\r\n" + b"x" * (LIMIT * 3) + b"\r\n"
        b"--" + boundary + b"--\r\n"
    )

    async def chunks():
        for i in range(0, len(body), 256):
            yield body[i : i + 256]

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/upload",
            content=chunks(),
            headers={"content-type": "multipart/form-data; boundary=limite"},
        )

    assert response.status_code == 413
