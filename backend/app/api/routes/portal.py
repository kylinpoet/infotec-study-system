from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import SchoolRegistrationApplication, Tenant, User
from app.db.session import get_db
from app.schemas.contracts import PortalResponse, SchoolApplicationCreateRequest, SchoolApplicationSubmitResponse
from app.services.portal_content import build_portal_response, serialize_school_application

router = APIRouter()


@router.get("/portal", response_model=PortalResponse)
def get_portal(db: Session = Depends(get_db)):
    return build_portal_response(db)


@router.post("/school-applications", response_model=SchoolApplicationSubmitResponse)
def create_school_application(payload: SchoolApplicationCreateRequest, db: Session = Depends(get_db)):
    normalized_code = payload.school_code.strip().lower()
    normalized_username = payload.applicant_username.strip()

    existing_tenant = db.scalar(select(Tenant).where(Tenant.code == normalized_code).limit(1))
    if existing_tenant:
        raise HTTPException(status_code=409, detail="该学校编码已存在，请更换后重新提交。")

    existing_user = db.scalar(select(User).where(User.username == normalized_username).limit(1))
    if existing_user:
        raise HTTPException(status_code=409, detail="申请人用户名已存在，请更换后重新提交。")

    duplicate_application = db.scalar(
        select(SchoolRegistrationApplication)
        .where(SchoolRegistrationApplication.school_code == normalized_code)
        .where(SchoolRegistrationApplication.status == "pending")
        .limit(1)
    )
    if duplicate_application:
        raise HTTPException(status_code=409, detail="该学校已有待审核申请，请勿重复提交。")

    duplicate_username_application = db.scalar(
        select(SchoolRegistrationApplication)
        .where(SchoolRegistrationApplication.applicant_username == normalized_username)
        .where(SchoolRegistrationApplication.status == "pending")
        .limit(1)
    )
    if duplicate_username_application:
        raise HTTPException(status_code=409, detail="该申请人已有待审核申请，请先等待审核结果。")

    application = SchoolRegistrationApplication(
        school_name=payload.school_name,
        school_code=normalized_code,
        district=payload.district,
        grade_scope=payload.grade_scope,
        slogan=payload.slogan,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        applicant_display_name=payload.applicant_display_name,
        applicant_username=normalized_username,
        applicant_password_hash=hash_password(payload.applicant_password),
        note=payload.note.strip() if payload.note and payload.note.strip() else None,
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return SchoolApplicationSubmitResponse(
        message="学校申请已提交，平台管理员审核通过后会自动创建学校后台与首位管理员账号。",
        application=serialize_school_application(application),
    )
