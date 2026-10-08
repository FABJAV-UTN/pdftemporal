"""Validación de formato y tamaño del archivo subido.

Se mira el contenido, no la extensión: todo PDF empieza con los bytes b"%PDF"
(magic bytes), así que un .docx renombrado a .pdf se rechaza.
"""

from fastapi import UploadFile

from app.business.domain.exceptions import InvalidPDFError, PDFTooLargeError
from app.config.settings import settings

PDF_MAGIC_BYTES: bytes = b"%PDF"


async def validate_pdf(file: UploadFile) -> None:
    """Verifica que el archivo sea un PDF y no supere el tamaño máximo.

    Lee solo los primeros 4 bytes, toma el tamaño de `file.size` (lo informa
    Starlette al parsear el multipart) y deja el cursor al inicio para que
    después se pueda leer el archivo completo.

    Raises:
        InvalidPDFError: si no empieza con %PDF (el cliente recibe 400).
        PDFTooLargeError: si supera MAX_PDF_SIZE_MB (el cliente recibe 413).
    """
    header = await file.read(len(PDF_MAGIC_BYTES))
    await file.seek(0)

    if header != PDF_MAGIC_BYTES:
        raise InvalidPDFError()

    if file.size > settings.max_pdf_size_bytes:
        raise PDFTooLargeError(settings.max_pdf_size_mb)
