"""Composición: arma el controller con sus casos de uso y el repositorio concreto.

Es el único lugar que conoce las implementaciones (DIP). En los tests se puede
reemplazar con app.dependency_overrides.
"""

from app.data.extractors.pdfplumber_text_extractor import PdfplumberTextExtractor
from app.data.repositories.mongo_document_repository import MongoDocumentRepository
from app.presentation.controllers.document_controller import DocumentController
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.process_pdf import ProcessPDFUseCase
from app.use_cases.update_document import UpdateDocumentUseCase


def get_document_controller() -> DocumentController:
    repo = MongoDocumentRepository()
    return DocumentController(
        process_pdf=ProcessPDFUseCase(repo, PdfplumberTextExtractor()),
        list_documents=ListDocumentsUseCase(repo),
        get_document=GetDocumentUseCase(repo),
        update_document=UpdateDocumentUseCase(repo),
        delete_document=DeleteDocumentUseCase(repo),
    )
