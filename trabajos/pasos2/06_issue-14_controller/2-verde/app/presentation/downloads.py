"""Helpers para la descarga del texto extraído como archivo .txt."""

from urllib.parse import quote


def txt_filename(original: str) -> str:
    """Nombre del archivo de descarga: el original con extensión .txt."""
    base = original[:-4] if original.lower().endswith(".pdf") else original
    return f"{base}.txt"


def content_disposition(filename: str) -> str:
    """Header Content-Disposition válido para cualquier nombre (RFC 6266 / RFC 5987).

    Los headers HTTP viajan en latin-1: `filename` lleva una versión ASCII de respaldo
    y `filename*` el nombre real codificado en UTF-8.
    """
    ascii_fallback = filename.encode("ascii", "replace").decode("ascii").replace('"', "")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"
