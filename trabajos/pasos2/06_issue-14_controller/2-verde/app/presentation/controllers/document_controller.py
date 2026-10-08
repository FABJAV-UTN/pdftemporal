from fastapi import UploadFile
from fastapi.responses import PlainTextResponse

from app.presentation.downloads import content_disposition, txt_filename
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.request.upload_request import UploadRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.validators.pdf_validator import validate_pdf
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.process_pdf import ProcessPDFUseCase
from app.use_cases.update_document import UpdateDocumentUseCase


class DocumentController:
    """Traduce entre HTTP (DTOs) y los casos de uso.

    Los errores de dominio no se capturan acá: los traduce a HTTP
    app/presentation/error_handlers.py.
    """

    def __init__(
        self,
        process_pdf: ProcessPDFUseCase,
        list_documents: ListDocumentsUseCase,
        get_document: GetDocumentUseCase,
        update_document: UpdateDocumentUseCase,
        delete_document: DeleteDocumentUseCase,
    ) -> None:
        self._process_pdf = process_pdf
        self._list_documents = list_documents
        self._get_document = get_document
        self._update_document = update_document
        self._delete_document = delete_document

    async def upload_document(self, file: UploadFile, dto: UploadRequestDTO) -> DocumentResponseDTO:
        await validate_pdf(file)
        file_bytes = await file.read()
        filename = dto.custom_name or file.filename
        document = await self._process_pdf.execute(file_bytes, filename)
        return DocumentResponseDTO.from_entity(document)

    async def get_all_documents(self, skip: int, limit: int) -> list[DocumentResponseDTO]:
        documents = await self._list_documents.execute(skip=skip, limit=limit)
        return [DocumentResponseDTO.from_entity(d) for d in documents]

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        document = await self._get_document.execute(document_id)
        return DocumentResponseDTO.from_entity(document)

    async def update_document(self, document_id: str, dto: UpdateRequestDTO) -> DocumentResponseDTO:
        document = await self._update_document.execute(document_id, self._to_domain_fields(dto))
        return DocumentResponseDTO.from_entity(document)

    async def delete_document(self, document_id: str) -> dict[str, str]:
        await self._delete_document.execute(document_id)
        return {"message": f"Documento '{document_id}' eliminado correctamente."}

    async def download_document_text(self, document_id: str) -> PlainTextResponse:
        document = await self._get_document.execute(document_id)
        filename = txt_filename(document.filename or document_id)
        return PlainTextResponse(
            document.extracted_text,
            headers={"Content-Disposition": content_disposition(filename)},
        )

    @staticmethod
    def _to_domain_fields(dto: UpdateRequestDTO) -> dict[str, str]:
        """Traduce el contrato HTTP (custom_name) al nombre del campo de dominio (filename)."""
        return {"filename": dto.custom_name} if dto.custom_name is not None else {}
