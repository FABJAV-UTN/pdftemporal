import asyncio

from app.business.domain.checksum_calculator import calculate_checksum
from app.business.domain.text_extractor import extract_text
from app.business.domain.validators.document_validator import validate_no_duplicate
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository


class ProcessPDFUseCase:
    """Checksum → control de duplicado → extracción del texto → guardado."""

    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, file_bytes: bytes, filename: str) -> Document:
        checksum = calculate_checksum(file_bytes)
        existing = await self._repository.get_by_checksum(checksum)
        validate_no_duplicate(existing, checksum)

        # La extracción es CPU sincrónica: se ejecuta en un hilo aparte para no
        # bloquear el event loop mientras se procesa el PDF.
        extracted_text = await asyncio.to_thread(extract_text, file_bytes)

        document = Document(filename=filename, checksum=checksum, extracted_text=extracted_text)
        return await self._repository.save(document)
