from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.formparsers import MultiPartParser

from app.config.settings import settings
from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middlewares.body_size_limit import BodySizeLimitMiddleware
from app.presentation.routers.document_router import router as document_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    await init_beanie(database=get_database(), document_models=[DocumentModel])
    yield
    await disconnect()


# Margen para los bytes del multipart que no son el PDF (boundaries, headers, custom_name).
MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_REQUEST_BYTES = settings.max_pdf_size_bytes + MULTIPART_OVERHEAD_BYTES

# Consigna Etapa 1: el PDF no se persiste temporalmente. Starlette pasa los uploads a
# disco cuando superan spool_max_size (1 MB por defecto); lo subimos al tamaño máximo
# de request, y BodySizeLimitMiddleware rechaza todo lo que lo supere.
MultiPartParser.spool_max_size = MAX_REQUEST_BYTES

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(document_router)
