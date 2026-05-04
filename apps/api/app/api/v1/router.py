"""v1 router — aggregates all endpoint sub-routers."""

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.export import router as export_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.integrations import router as integrations_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.users import router as users_router
from fastapi import APIRouter

v1_router = APIRouter()

v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(health_router, prefix="/health", tags=["health"])
v1_router.include_router(users_router, prefix="/users", tags=["users"])
v1_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
v1_router.include_router(documents_router, prefix="/documents", tags=["documents"])
v1_router.include_router(analytics_router, prefix="/sessions", tags=["analytics"])
v1_router.include_router(export_router, prefix="/sessions", tags=["export"])
v1_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
