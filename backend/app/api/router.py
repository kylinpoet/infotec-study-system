from fastapi import APIRouter

from app.api.routes import auth, health, portal, student, teacher

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(portal.router, prefix="/public", tags=["public"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(student.router, prefix="/student", tags=["student"])

