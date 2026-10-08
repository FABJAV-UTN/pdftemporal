"""Casos de uso de consulta, actualización y borrado."""

import pytest

from app.business.domain.exceptions import DocumentNotFoundError
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.process_pdf import ProcessPDFUseCase
from app.use_cases.update_document import UpdateDocumentUseCase
from tests.unit.fakes import MINIMAL_PDF, FakeTextExtractor, InMemoryDocumentRepository

MISSING_ID = "ffffffffffffffffffffffff"


@pytest.fixture
def repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@pytest.fixture
async def saved(repo):
    return await ProcessPDFUseCase(repo, FakeTextExtractor()).execute(MINIMAL_PDF, "original.pdf")


class TestGetDocument:
    async def test_returns_existing_document(self, repo, saved):
        assert await GetDocumentUseCase(repo).execute(saved.id) == saved

    async def test_missing_document_raises_not_found(self, repo):
        with pytest.raises(DocumentNotFoundError, match=MISSING_ID):
            await GetDocumentUseCase(repo).execute(MISSING_ID)


class TestListDocuments:
    async def test_empty_repository_returns_empty_list(self, repo):
        assert await ListDocumentsUseCase(repo).execute() == []

    async def test_returns_saved_documents(self, repo, saved):
        assert await ListDocumentsUseCase(repo).execute() == [saved]

    async def test_respects_skip_and_limit(self, repo, saved):
        assert await ListDocumentsUseCase(repo).execute(skip=1, limit=10) == []
        assert await ListDocumentsUseCase(repo).execute(skip=0, limit=1) == [saved]


class TestUpdateDocument:
    async def test_renames_document(self, repo, saved):
        updated = await UpdateDocumentUseCase(repo).execute(saved.id, {"filename": "nuevo.pdf"})

        assert updated.filename == "nuevo.pdf"
        assert updated.checksum == saved.checksum
        assert updated.extracted_text == saved.extracted_text

    async def test_missing_document_raises_not_found(self, repo):
        with pytest.raises(DocumentNotFoundError):
            await UpdateDocumentUseCase(repo).execute(MISSING_ID, {"filename": "x.pdf"})


class TestDeleteDocument:
    async def test_deletes_existing_document(self, repo, saved):
        await DeleteDocumentUseCase(repo).execute(saved.id)

        assert await repo.get_by_id(saved.id) is None

    async def test_missing_document_raises_not_found(self, repo):
        with pytest.raises(DocumentNotFoundError):
            await DeleteDocumentUseCase(repo).execute(MISSING_ID)
