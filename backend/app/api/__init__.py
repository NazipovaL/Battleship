# backend/app/api/__init__.py
from fastapi import APIRouter
from backend.app.api.routes import auth
from .generate import router as generate_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(generate_router, prefix="/api")
