"""Reglas de negocio sobre documentos (la validación de formato está en pdf_validator)."""

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document


def validate_no_duplicate(existing_document: Document | None, checksum: str) -> None:
    """Verifica que no exista ya un documento con el mismo checksum.

    Se llama antes de persistir un nuevo documento. Si ya hay uno con
    el mismo SHA-256, lanza DuplicateDocumentError (el cliente recibe 409).

    Args:
        existing_document: Resultado de buscar por checksum en el repositorio.
                           None significa que el documento es nuevo.
        checksum: Hash SHA-256 del archivo que se intenta guardar.

    Raises:
        DuplicateDocumentError: Si `existing_document` no es None.
    """
    if existing_document is not None:
        raise DuplicateDocumentError(checksum)