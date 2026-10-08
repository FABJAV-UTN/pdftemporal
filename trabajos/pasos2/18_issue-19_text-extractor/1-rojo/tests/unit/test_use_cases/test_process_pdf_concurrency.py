"""
La extracción de texto (CPU, sincrónica) no debe bloquear el event loop:
mientras se procesa un PDF, el servidor tiene que poder atender otras requests.
"""

import asyncio
import time

from app.use_cases.process_pdf import ProcessPDFUseCase
from tests.unit.fakes import MINIMAL_PDF, FakeTextExtractor, InMemoryDocumentRepository

EXTRACTION_SECONDS = 0.3


class SlowTextExtractor(FakeTextExtractor):
    def extract(self, file_bytes: bytes) -> str:
        time.sleep(EXTRACTION_SECONDS)  # simula un PDF pesado
        return super().extract(file_bytes)


async def test_event_loop_keeps_running_while_extracting():
    ticks = 0

    async def other_request():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.01)
            ticks += 1

    ticker = asyncio.create_task(other_request())
    use_case = ProcessPDFUseCase(InMemoryDocumentRepository(), SlowTextExtractor())
    await use_case.execute(MINIMAL_PDF, "a.pdf")
    ticker.cancel()

    # En 0,3 s el loop libre hace ~30 ticks; bloqueado, 0 o 1.
    assert ticks >= 10
