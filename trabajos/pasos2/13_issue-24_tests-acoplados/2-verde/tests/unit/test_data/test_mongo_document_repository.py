"""
Tests unitarios de MongoDocumentRepository.

Se usa mongomock-motor: una base MongoDB en memoria con la misma API que Motor.
Así se prueba el comportamiento del repositorio (qué guarda, qué devuelve) y no
la cadena interna de llamadas a Beanie.
"""

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document
from app.data.models.document_model import DocumentModel
from app.data.repositories.mongo_document_repository import MongoDocumentRepository

MISSING_ID = "64a1b2c3d4e5f6a7b8c9d0e1"


@pytest.fixture
async def repo() -> MongoDocumentRepository:
    database = AsyncMongoMockClient()["repo_tests"]
    await init_beanie(database=database, document_models=[DocumentModel])
    return MongoDocumentRepository()


def new_document(checksum: str = "c1", filename: str = "a.pdf") -> Document:
    return Document(filename=filename, checksum=checksum, extracted_text="Texto")


class TestSave:
    async def test_assigns_an_id_and_keeps_the_data(self, repo):
        saved = await repo.save(new_document())

        assert saved.id is not None
        assert (saved.filename, saved.checksum, saved.extracted_text) == ("a.pdf", "c1", "Texto")

    async def test_same_checksum_twice_raises_duplicate(self, repo):
        await repo.save(new_document(checksum="igual"))

        with pytest.raises(DuplicateDocumentError, match="igual"):
            await repo.save(new_document(checksum="igual", filename="otro.pdf"))


class TestGetAll:
    async def test_empty_collection_returns_empty_list(self, repo):
        assert await repo.get_all() == []

    async def test_paginates_with_skip_and_limit(self, repo):
        for i in range(3):
            await repo.save(new_document(checksum=f"c{i}", filename=f"{i}.pdf"))

        page = await repo.get_all(skip=1, limit=1)

        assert [d.filename for d in page] == ["1.pdf"]


class TestGetById:
    async def test_returns_the_saved_document(self, repo):
        saved = await repo.save(new_document())

        found = await repo.get_by_id(saved.id)

        assert (found.id, found.checksum) == (saved.id, saved.checksum)

    async def test_missing_id_returns_none(self, repo):
        assert await repo.get_by_id(MISSING_ID) is None

    async def test_malformed_id_returns_none(self, repo):
        assert await repo.get_by_id("no-es-un-objectid") is None


class TestGetByChecksum:
    async def test_finds_by_checksum(self, repo):
        saved = await repo.save(new_document(checksum="buscado"))

        assert (await repo.get_by_checksum("buscado")).id == saved.id

    async def test_unknown_checksum_returns_none(self, repo):
        assert await repo.get_by_checksum("nada") is None


class TestUpdate:
    async def test_renames_and_persists(self, repo):
        saved = await repo.save(new_document())

        updated = await repo.update(saved.id, {"filename": "nuevo.pdf"})

        assert updated.filename == "nuevo.pdf"
        assert (await repo.get_by_id(saved.id)).filename == "nuevo.pdf"

    async def test_ignores_fields_that_are_not_metadata(self, repo):
        saved = await repo.save(new_document())

        updated = await repo.update(saved.id, {"checksum": "otro", "extracted_text": "otro"})

        assert (updated.checksum, updated.extracted_text) == ("c1", "Texto")

    async def test_missing_id_returns_none(self, repo):
        assert await repo.update(MISSING_ID, {"filename": "x.pdf"}) is None


class TestDelete:
    async def test_deletes_and_returns_true(self, repo):
        saved = await repo.save(new_document())

        assert await repo.delete(saved.id) is True
        assert await repo.get_by_id(saved.id) is None

    async def test_missing_id_returns_false(self, repo):
        assert await repo.delete(MISSING_ID) is False

    async def test_malformed_id_returns_false(self, repo):
        assert await repo.delete("no-es-un-objectid") is False
