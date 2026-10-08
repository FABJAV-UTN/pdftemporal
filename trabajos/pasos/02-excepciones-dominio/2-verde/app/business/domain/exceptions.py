"""Errores de negocio de los documentos.

Describen qué regla se violó, no cómo se informa al cliente: no conocen
HTTP ni FastAPI. La traducción a respuestas HTTP (RFC 9457) vive en
app/presentation/error_handlers.py.
"""


class DomainError(Exception):
    """Base de todos los errores de negocio."""


class DocumentNotFoundError(DomainError):
    """No existe un documento con el id buscado."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' not found.")
        self.document_id = document_id


class DuplicateDocumentError(DomainError):
    """Ya existe un documento con el mismo checksum."""

    def __init__(self, checksum: str) -> None:
        super().__init__(f"A document with checksum '{checksum}' already exists.")
        self.checksum = checksum


class InvalidPDFError(DomainError):
    """El archivo no es un PDF o su contenido no se puede leer."""

    def __init__(self, detail: str = "El archivo no es un PDF válido.") -> None:
        super().__init__(detail)


class PDFTooLargeError(DomainError):
    """El archivo supera el tamaño máximo permitido."""

    def __init__(self, max_size_mb: int) -> None:
        super().__init__(f"El archivo supera el tamaño máximo de {max_size_mb} MB.")
        self.max_size_mb = max_size_mb
