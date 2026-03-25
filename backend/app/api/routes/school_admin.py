from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import PortalSchoolProfile, TeacherProfile, Tenant, User
from app.db.session import get_db
from app.schemas.contracts import (
    QuickStat,
    SchoolAdminDashboardResponse,
    SchoolProfileUpdateRequest,
    SchoolStaffCreateRequest,
    SchoolStaffMember,
    SchoolStaffMutationResponse,
    SchoolStaffRoleUpdateRequest,
)
from app.services.portal_content import DEFAULT_SCHOOL_THEME, portal_school_payload

router = APIRouter()


def _get_school_admin(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user or user.role != "school_admin":
        raise HTTPException(status_code=404, detail="学校管理员不存在。")
    return user


def _serialize_staff_member(user: User, teacher_profile: TeacherProfile | None) -> SchoolStaffMember:
    return SchoolStaffMember(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
        teacher_no=teacher_profile.teacher_no if teacher_profile else None,
        subject=teacher_profile.subject if teacher_profile else None,
        title=teacher_profile.title if teacher_profile else None,
        created_at=user.created_at,
    )


def _build_teacher_profile(user: User, db: Session) -> TeacherProfile | None:
    return db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id).limit(1))


@router.get("/dashboard/{user_id}", response_model=SchoolAdminDashboardResponse)
def get_school_admin_dashboard(user_id: int, db: Session = Depends(get_db)):
    admin = _get_school_admin(user_id, db)
    tenant = db.get(Tenant, admin.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="学校不存在。")

    profile = db.scalar(select(PortalSchoolProfile).where(PortalSchoolProfile.tenant_id == tenant.id).limit(1))
    school = portal_school_payload(tenant, profile, {})

    staff_users = db.scalars(
        select(User)
        .where(User.tenant_id == tenant.id)
        .where(User.role.in_(("teacher", "school_admin")))
        .order_by(User.role.desc(), User.created_at.asc(), User.id.asc())
    ).all()
    teacher_profiles = {
        item.user_id: item
        for item in db.scalars(
            select(TeacherProfile).where(TeacherProfile.user_id.in_([user.id for user in staff_users] or [0]))
        ).all()
    }
    school_admin_count = len([user for user in staff_users if user.role == "school_admin"])
    teacher_count = len([user for user in staff_users if user.role == "teacher"])

    return SchoolAdminDashboardResponse(
        admin_name=admin.display_name,
        tenant_name=tenant.name,
        school=school,
        quick_stats=[
            QuickStat(title="校级管理员", value=str(school_admin_count), hint="首位入驻申请人默认成为学校管理员"),
            QuickStat(title="教师账号", value=str(teacher_count), hint="学校管理员可在本校后台继续添加教师账号"),
            QuickStat(title="学校编码", value=tenant.code, hint="用于学校登录匹配与多校租户边界隔离"),
            QuickStat(title="当前状态", value=tenant.status, hint="学校资料保存后会同步反映到门户展示中"),
        ],
        staff_members=[_serialize_staff_member(user, teacher_profiles.get(user.id)) for user in staff_users],
    )


@router.put("/profile", response_model=SchoolAdminDashboardResponse)
def update_school_profile(payload: SchoolProfileUpdateRequest, db: Session = Depends(get_db)):
    admin = _get_school_admin(payload.admin_user_id, db)
    tenant = db.get(Tenant, admin.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="学校不存在。")

    profile = db.scalar(select(PortalSchoolProfile).where(PortalSchoolProfile.tenant_id == tenant.id).limit(1))
    if not profile:
        profile = PortalSchoolProfile(
            tenant_id=tenant.id,
            district=payload.district,
            slogan=payload.slogan,
            grade_scope=payload.grade_scope,
            features_json=[],
            metrics_json=[],
        )
        db.add(profile)
        db.flush()

    tenant.name = payload.name.strip()
    tenant.theme_json = payload.theme.model_dump() if payload.theme else DEFAULT_SCHOOL_THEME
    profile.district = payload.district.strip()
    profile.slogan = payload.slogan.strip()
    profile.grade_scope = payload.grade_scope.strip()
    profile.features_json = [item.model_dump() for item in payload.features]
    profile.metrics_json = [item.model_dump() for item in payload.metrics]
    db.commit()
    return get_school_admin_dashboard(admin.id, db)


@router.post("/staff", response_model=SchoolStaffMutationResponse)
def create_school_staff(payload: SchoolStaffCreateRequest, db: Session = Depends(get_db)):
    admin = _get_school_admin(payload.admin_user_id, db)
    existing_user = db.scalar(select(User).where(User.username == payload.username).limit(1))
    if existing_user:
        raise HTTPException(status_code=409, detail="用户名已存在，请更换后再创建。")

    teacher_count = db.scalar(
        select(func.count(User.id))
        .where(User.tenant_id == admin.tenant_id)
        .where(User.role == "teacher")
    ) or 0
    teacher_no = payload.teacher_no.strip() if payload.teacher_no and payload.teacher_no.strip() else f"T-{teacher_count + 1:03d}"

    user = User(
        tenant_id=admin.tenant_id,
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        role="teacher",
        display_name=payload.display_name.strip(),
        avatar="horse",
        status="active",
    )
    db.add(user)
    db.flush()

    db.add(
        TeacherProfile(
            user_id=user.id,
            teacher_no=teacher_no,
            subject=payload.subject.strip(),
            title=payload.title.strip() if payload.title and payload.title.strip() else None,
        )
    )
    db.commit()
    db.refresh(user)
    return SchoolStaffMutationResponse(
        message=f"已为本校创建教师账号 {user.display_name}。",
        staff_member=_serialize_staff_member(user, _build_teacher_profile(user, db)),
    )


@router.put("/staff/{staff_user_id}/role", response_model=SchoolStaffMutationResponse)
def update_school_staff_role(
    staff_user_id: int,
    payload: SchoolStaffRoleUpdateRequest,
    db: Session = Depends(get_db),
):
    admin = _get_school_admin(payload.admin_user_id, db)
    user = db.get(User, staff_user_id)
    if not user or user.tenant_id != admin.tenant_id or user.role not in {"teacher", "school_admin"}:
        raise HTTPException(status_code=404, detail="目标成员不存在。")

    if user.role == "school_admin" and payload.role == "teacher":
        school_admin_count = db.scalar(
            select(func.count(User.id))
            .where(User.tenant_id == admin.tenant_id)
            .where(User.role == "school_admin")
        ) or 0
        if school_admin_count <= 1:
            raise HTTPException(status_code=422, detail="学校至少需要保留一位学校管理员。")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    teacher_profile = _build_teacher_profile(user, db)
    return SchoolStaffMutationResponse(
        message=f"已将 {user.display_name} 设置为{'学校管理员' if user.role == 'school_admin' else '教师'}。",
        staff_member=_serialize_staff_member(user, teacher_profile),
    )
