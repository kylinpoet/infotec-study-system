from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.models import Classroom, Course, StudentProfile, TeacherProfile, Tenant, User
from app.db.session import get_db
from app.schemas.contracts import LoginRequest, LoginResponse, SessionUser

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误。",
        )

    tenant = db.get(Tenant, user.tenant_id)
    if payload.school_code and tenant and tenant.code != payload.school_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="所选学校与账号不匹配，请先切换学校。",
        )

    classroom_label = None
    current_course_id = None

    if user.role == "student":
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        if profile:
            classroom = db.get(Classroom, profile.classroom_id)
            classroom_label = classroom.name if classroom else profile.classroom_label

    if user.role == "teacher":
        db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
        course = db.scalar(
            select(Course)
            .where(Course.tenant_id == user.tenant_id)
            .where(Course.is_published.is_(True))
            .order_by(Course.lesson_no.asc(), Course.id.asc())
            .limit(1)
        )
        current_course_id = course.id if course else None

    return LoginResponse(
        access_token=f"demo-session-{user.id}",
        user=SessionUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            tenant_id=user.tenant_id,
            tenant_code=tenant.code if tenant else None,
            tenant_name=tenant.name if tenant else "默认学校",
            classroom_label=classroom_label,
            current_course_id=current_course_id,
        ),
    )
