from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel
from app.presentation.error_handlers import register_error_handlers
from app.presentation.routers.document_router import router as document_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    await init_beanie(database=get_database(), document_models=[DocumentModel])
    yield
    await disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(document_router)
