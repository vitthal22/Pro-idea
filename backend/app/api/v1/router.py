"""Aggregates all v1 routers."""

from fastapi import APIRouter

from app.api.v1 import analyses, auth, resumes

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/v1")
api_v1_router.include_router(resumes.router, prefix="/v1")
api_v1_router.include_router(analyses.router, prefix="/v1")
