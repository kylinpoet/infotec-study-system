from fastapi import APIRouter

from app.api.routes import admin, auth, health, portal, school_admin, settings, student, teacher

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(portal.router, prefix="/public", tags=["public"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(student.router, prefix="/student", tags=["student"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(school_admin.router, prefix="/school-admin", tags=["school-admin"])
