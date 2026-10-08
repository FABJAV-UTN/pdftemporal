"""Límite de tamaño del body HTTP.

Corta las requests demasiado grandes ANTES de que Starlette parsee el multipart.
Junto con el umbral de spool configurado en main.py, garantiza que un PDF nunca
se escriba en un archivo temporal en disco (consigna de la Etapa 1).
"""

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.presentation.error_handlers import problem_detail_response


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self._declared_length(scope) > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        received = 0
        too_large = False
        rejected = False

        async def limited_receive() -> Message:
            # Sin Content-Length (chunked) contamos los bytes a medida que llegan.
            # Al pasar el límite simulamos una desconexión: la app deja de leer
            # y su respuesta de error se reemplaza por un 413.
            nonlocal received, too_large
            if too_large:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    too_large = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal rejected
            if not too_large:
                await send(message)
            elif not rejected:
                rejected = True
                await self._reject(scope, receive, send)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not too_large:
                raise
        if too_large and not rejected:
            await self._reject(scope, receive, send)

    @staticmethod
    def _declared_length(scope: Scope) -> int:
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    return int(value)
                except ValueError:
                    return 0
        return 0

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        max_mb = self.max_bytes // (1024 * 1024)
        response = problem_detail_response(
            413,
            "Payload Too Large",
            f"La request supera el tamaño máximo permitido (~{max_mb} MB).",
            str(Request(scope).url),
        )
        await response(scope, receive, send)
