"""ProcessPDFUseCase: checksum → duplicado → extracción → guardado."""

import pytest

from app.business.domain.exceptions import DuplicateDocumentError, InvalidPDFError
from app.use_cases.process_pdf import ProcessPDFUseCase
from tests.unit.fakes import MINIMAL_PDF, FakeTextExtractor, InMemoryDocumentRepository

SHA256_MINIMAL_PDF = "18c3d79e2d8a7c456bc798bd52c37a490d33af25f63432de60f1d8cf0a897d56"


@pytest.fixture
def repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


async def test_saves_document_with_its_checksum(repo):
    document = await ProcessPDFUseCase(repo, FakeTextExtractor()).execute(MINIMAL_PDF, "a.pdf")

    assert document.id is not None
    assert document.filename == "a.pdf"
    assert document.checksum == SHA256_MINIMAL_PDF
    assert await repo.get_by_id(document.id) == document


async def test_saves_the_text_returned_by_the_injected_extractor(repo):
    extractor = FakeTextExtractor(text="Hola Mundo")

    document = await ProcessPDFUseCase(repo, extractor).execute(MINIMAL_PDF, "a.pdf")

    assert document.extracted_text == "Hola Mundo"
    assert extractor.calls == [MINIMAL_PDF]


async def test_same_content_twice_raises_duplicate_without_extracting_again(repo):
    extractor = FakeTextExtractor()
    use_case = ProcessPDFUseCase(repo, extractor)
    await use_case.execute(MINIMAL_PDF, "a.pdf")

    with pytest.raises(DuplicateDocumentError):
        await use_case.execute(MINIMAL_PDF, "otro_nombre.pdf")
    assert len(extractor.calls) == 1


async def test_unreadable_pdf_raises_and_saves_nothing(repo):
    extractor = FakeTextExtractor(error=InvalidPDFError())

    with pytest.raises(InvalidPDFError):
        await ProcessPDFUseCase(repo, extractor).execute(b"%PDF-1.4 roto", "roto.pdf")

    assert await repo.get_all() == []
