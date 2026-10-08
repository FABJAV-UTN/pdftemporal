"""
Extractor de texto de archivos PDF.

Convierte el contenido binario de un PDF en texto plano, en memoria
(el archivo nunca se escribe a disco).
"""

import io
import logging

import pdfplumber

from app.business.domain.exceptions import InvalidPDFError

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes) -> str:
    """Extrae el texto de todas las páginas de un PDF.

    Un PDF escaneado (sin texto seleccionable) es válido y devuelve ''.

    Raises:
        InvalidPDFError: si el contenido no se puede leer como PDF.
    """
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        logger.warning("No se pudo leer el PDF: %s", exc)
        raise InvalidPDFError("El archivo no es un PDF válido o está dañado.") from exc

    return "\n".join(pages_text).strip()
