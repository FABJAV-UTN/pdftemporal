"""DocumentResponseDTO: serialización y ausencia de APIs deprecadas de Pydantic."""

import importlib
import warnings
from datetime import datetime, timezone

from app.presentation.dto.response import document_response


def test_module_defines_the_dto_without_deprecation_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        importlib.reload(document_response)


def test_dates_keep_the_iso_8601_format_of_the_api():
    moment = datetime(2026, 5, 23, 10, 30, tzinfo=timezone.utc)
    dto = document_response.DocumentResponseDTO(
        id="1", name="a.pdf", checksum="c", extracted_text="t", created_at=moment, updated_at=moment
    )

    body = dto.model_dump(mode="json")

    assert body["created_at"] == "2026-05-23T10:30:00+00:00"
    assert body["updated_at"] == "2026-05-23T10:30:00+00:00"
