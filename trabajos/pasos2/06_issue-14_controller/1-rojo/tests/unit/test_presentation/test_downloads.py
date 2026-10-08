"""Tests de los helpers que arman el nombre y el header de la descarga .txt."""

from urllib.parse import quote

import pytest

from app.presentation.downloads import content_disposition, txt_filename


@pytest.mark.parametrize(
    "original,expected",
    [
        ("informe.pdf", "informe.txt"),
        ("INFORME.PDF", "INFORME.txt"),
        ("notas", "notas.txt"),
        ("version.final.pdf", "version.final.txt"),
    ],
)
def test_txt_filename_replaces_pdf_extension(original, expected):
    assert txt_filename(original) == expected


def test_content_disposition_for_ascii_name():
    assert content_disposition("informe.txt") == (
        "attachment; filename=\"informe.txt\"; filename*=UTF-8''informe.txt"
    )


def test_content_disposition_for_non_ascii_name_is_latin1_safe():
    header = content_disposition("año_文件.txt")

    header.encode("latin-1")  # los headers HTTP se envían en latin-1: no debe fallar
    assert "filename*=UTF-8''" + quote("año_文件.txt") in header
