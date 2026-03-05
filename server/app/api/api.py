# server/app/api/api.py
from fastapi import APIRouter
from server.app.api.endpoints import stream, behavior, books, reading, parent

api_router = APIRouter()

api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(behavior.router, prefix="/behavior", tags=["behavior"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(reading.router, prefix="/reading", tags=["reading"])
api_router.include_router(parent.router, prefix="/parent", tags=["parent"])