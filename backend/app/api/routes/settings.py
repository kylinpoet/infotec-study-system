from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Classroom, Course, StudentProfile, TeacherProfile, Tenant, User
from app.db.session import get_db
from app.schemas.contracts import (
    SessionUser,
    StudentSettingsResponse,
    StudentSettingsUpdateRequest,
    TeacherSettingsResponse,
    TeacherSettingsUpdateRequest,
    ZodiacAvatarOption,
)

router = APIRouter()

ZODIAC_OPTIONS = [
    ZodiacAvatarOption(key="rat", label="机灵鼠", animal="鼠", description="反应快，适合提示式答疑"),
    ZodiacAvatarOption(key="ox", label="稳健牛", animal="牛", description="擅长分步骤讲解和耐心陪练"),
    ZodiacAvatarOption(key="tiger", label="探索虎", animal="虎", description="适合挑战任务和创意激发"),
    ZodiacAvatarOption(key="rabbit", label="灵感兔", animal="兔", description="偏温和鼓励，适合低压辅学"),
    ZodiacAvatarOption(key="dragon", label="领航龙", animal="龙", description="擅长课堂引导与项目规划"),
    ZodiacAvatarOption(key="snake", label="推理蛇", animal="蛇", description="适合逻辑分析与细节纠错"),
    ZodiacAvatarOption(key="horse", label="行动马", animal="马", description="适合节奏推进和任务提醒"),
    ZodiacAvatarOption(key="goat", label="共创羊", animal="羊", description="适合同伴互评与协作反馈"),
    ZodiacAvatarOption(key="monkey", label="创客猴", animal="猴", description="适合编程试玩和创客灵感"),
    ZodiacAvatarOption(key="rooster", label="晨光鸡", animal="鸡", description="适合清单式复盘与晨读提醒"),
    ZodiacAvatarOption(key="dog", label="守护狗", animal="狗", description="适合学习陪伴与错题回访"),
    ZodiacAvatarOption(key="pig", label="圆梦猪", animal="猪", description="适合成长鼓励与阶段总结"),
]


def _get_user(user_id: int, role: str, db: Session) -> User:
    user = db.get(User, user_id)
    if not user or user.role != role:
        raise HTTPException(status_code=404, detail="用户不存在。")
    return user


def _tenant_name(user: User, db: Session) -> str:
    tenant = db.get(Tenant, user.tenant_id)
    return tenant.name if tenant else "默认学校"


def _session_user(user: User, db: Session) -> SessionUser:
    classroom_label = None
    current_course_id = None
    tenant = db.get(Tenant, user.tenant_id)

    if user.role == "student":
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        if profile:
            classroom = db.get(Classroom, profile.classroom_id)
            classroom_label = classroom.name if classroom else profile.classroom_label
    elif user.role == "teacher":
        course = db.scalar(
            select(Course)
            .where(Course.tenant_id == user.tenant_id)
            .where(Course.is_published.is_(True))
            .order_by(Course.lesson_no.asc(), Course.id.asc())
            .limit(1)
        )
        current_course_id = course.id if course else None

    return SessionUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_code=tenant.code if tenant else None,
        tenant_name=tenant.name if tenant else "默认学校",
        classroom_label=classroom_label,
        current_course_id=current_course_id,
        avatar=user.avatar,
    )


@router.get("/student/{user_id}", response_model=StudentSettingsResponse)
def get_student_settings(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(user_id, "student", db)
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="学生档案不存在。")
    return StudentSettingsResponse(
        user=_session_user(user, db),
        student_no=profile.student_no,
        grade=profile.grade,
        classroom_label=profile.classroom_label,
        seat_no=profile.seat_no,
        zodiac_options=ZODIAC_OPTIONS,
    )


@router.put("/student", response_model=StudentSettingsResponse)
def update_student_settings(payload: StudentSettingsUpdateRequest, db: Session = Depends(get_db)):
    user = _get_user(payload.user_id, "student", db)
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="学生档案不存在。")
    user.display_name = payload.display_name.strip()
    user.avatar = payload.avatar
    db.commit()
    db.refresh(user)
    return StudentSettingsResponse(
        user=_session_user(user, db),
        student_no=profile.student_no,
        grade=profile.grade,
        classroom_label=profile.classroom_label,
        seat_no=profile.seat_no,
        zodiac_options=ZODIAC_OPTIONS,
    )


@router.get("/teacher/{user_id}", response_model=TeacherSettingsResponse)
def get_teacher_settings(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(user_id, "teacher", db)
    profile = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="教师档案不存在。")
    return TeacherSettingsResponse(
        user=_session_user(user, db),
        teacher_no=profile.teacher_no,
        subject=profile.subject,
        title=profile.title,
        zodiac_options=ZODIAC_OPTIONS,
    )


@router.put("/teacher", response_model=TeacherSettingsResponse)
def update_teacher_settings(payload: TeacherSettingsUpdateRequest, db: Session = Depends(get_db)):
    user = _get_user(payload.user_id, "teacher", db)
    profile = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="教师档案不存在。")
    user.display_name = payload.display_name.strip()
    user.avatar = payload.avatar
    profile.subject = payload.subject.strip()
    profile.title = payload.title.strip() if payload.title else None
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return TeacherSettingsResponse(
        user=_session_user(user, db),
        teacher_no=profile.teacher_no,
        subject=profile.subject,
        title=profile.title,
        zodiac_options=ZODIAC_OPTIONS,
    )
