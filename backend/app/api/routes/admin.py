from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PortalAnnouncementRecord, PortalSchoolProfile, Tenant, User
from app.db.session import get_db
from app.schemas.contracts import (
    LLMConfigResponse,
    LLMConfigUpdateRequest,
    PortalAdminDashboardResponse,
    PortalAnnouncement,
    PortalAnnouncementUpsertRequest,
    PortalHeroSettings,
    PortalHeroUpdateRequest,
    PortalSchoolUpdateRequest,
    QuickStat,
)
from app.services.portal_content import (
    build_portal_admin_school_items,
    get_or_create_portal_config,
)
from app.services.llm_config import (
    build_llm_config_response,
    get_decrypted_api_key,
    get_or_create_llm_config,
    set_encrypted_api_key,
)

router = APIRouter()


def _get_admin(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=404, detail="管理员不存在。")
    return user


@router.get("/portal/dashboard/{user_id}", response_model=PortalAdminDashboardResponse)
def get_portal_admin_dashboard(user_id: int, db: Session = Depends(get_db)):
    admin = _get_admin(user_id, db)
    config = get_or_create_portal_config(db)
    llm_config = get_or_create_llm_config(db)
    schools = build_portal_admin_school_items(db)
    announcements = db.scalars(
        select(PortalAnnouncementRecord)
        .order_by(PortalAnnouncementRecord.display_order.asc(), PortalAnnouncementRecord.published_at.desc())
    ).all()
    active_school_count = len([school for school in schools if school.code])

    return PortalAdminDashboardResponse(
        admin_name=admin.display_name,
        hero=PortalHeroSettings(
            hero_title=config.hero_title,
            hero_subtitle=config.hero_subtitle,
            featured_school_code=config.featured_school_code,
        ),
        schools=schools,
        announcements=[
            PortalAnnouncement(
                id=item.id,
                title=item.title,
                tag=item.tag,
                summary=item.summary,
                published_at=item.published_at,
                is_active=item.is_active,
            )
            for item in announcements
        ],
        quick_stats=[
            QuickStat(title="学校门户", value=str(active_school_count), hint="支持在同一后台维护多校门户资料"),
            QuickStat(title="门户公告", value=str(len(announcements)), hint="可上架、下架和调整公告顺序"),
            QuickStat(title="当前主推学校", value=config.featured_school_code or "--", hint="首页首屏默认展示学校"),
            QuickStat(title="当前模型", value=llm_config.model_name, hint="后台可统一维护大模型连接参数"),
        ],
        llm_config=build_llm_config_response(llm_config),
    )


@router.put("/portal/hero", response_model=PortalHeroSettings)
def update_portal_hero(payload: PortalHeroUpdateRequest, db: Session = Depends(get_db)):
    _get_admin(payload.admin_user_id, db)
    config = get_or_create_portal_config(db)
    config.hero_title = payload.hero_title.strip()
    config.hero_subtitle = payload.hero_subtitle.strip()
    config.featured_school_code = payload.featured_school_code
    db.commit()
    db.refresh(config)
    return PortalHeroSettings(
        hero_title=config.hero_title,
        hero_subtitle=config.hero_subtitle,
        featured_school_code=config.featured_school_code,
    )


@router.put("/portal/schools/{school_code}")
def update_portal_school(
    school_code: str,
    payload: PortalSchoolUpdateRequest,
    db: Session = Depends(get_db),
):
    _get_admin(payload.admin_user_id, db)
    tenant = db.scalar(select(Tenant).where(Tenant.code == school_code).limit(1))
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
    tenant.theme_json = payload.theme.model_dump()
    profile.district = payload.district.strip()
    profile.slogan = payload.slogan.strip()
    profile.grade_scope = payload.grade_scope.strip()
    profile.features_json = [item.model_dump() for item in payload.features]
    profile.metrics_json = [item.model_dump() for item in payload.metrics]
    db.commit()

    return {"message": f"已更新 {tenant.name} 的门户资料。"}


@router.post("/portal/announcements", response_model=PortalAnnouncement)
def create_portal_announcement(payload: PortalAnnouncementUpsertRequest, db: Session = Depends(get_db)):
    _get_admin(payload.admin_user_id, db)
    max_order = db.scalar(select(PortalAnnouncementRecord.display_order).order_by(PortalAnnouncementRecord.display_order.desc()).limit(1))
    announcement = PortalAnnouncementRecord(
        title=payload.title.strip(),
        tag=payload.tag.strip(),
        summary=payload.summary.strip(),
        published_at=payload.published_at,
        display_order=(max_order or 0) + 1,
        is_active=payload.is_active,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return PortalAnnouncement(
        id=announcement.id,
        title=announcement.title,
        tag=announcement.tag,
        summary=announcement.summary,
        published_at=announcement.published_at,
        is_active=announcement.is_active,
    )


@router.put("/portal/announcements/{announcement_id}", response_model=PortalAnnouncement)
def update_portal_announcement(
    announcement_id: int,
    payload: PortalAnnouncementUpsertRequest,
    db: Session = Depends(get_db),
):
    _get_admin(payload.admin_user_id, db)
    announcement = db.get(PortalAnnouncementRecord, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在。")
    announcement.title = payload.title.strip()
    announcement.tag = payload.tag.strip()
    announcement.summary = payload.summary.strip()
    announcement.published_at = payload.published_at
    announcement.is_active = payload.is_active
    db.commit()
    db.refresh(announcement)
    return PortalAnnouncement(
        id=announcement.id,
        title=announcement.title,
        tag=announcement.tag,
        summary=announcement.summary,
        published_at=announcement.published_at,
        is_active=announcement.is_active,
    )


@router.put("/llm/config", response_model=LLMConfigResponse)
def update_llm_config(payload: LLMConfigUpdateRequest, db: Session = Depends(get_db)):
    _get_admin(payload.admin_user_id, db)
    config = get_or_create_llm_config(db)
    existing_api_key = get_decrypted_api_key(config)
    next_api_key = None if payload.clear_api_key else (payload.api_key.strip() if payload.api_key and payload.api_key.strip() else existing_api_key)

    if payload.is_enabled and not next_api_key:
        raise HTTPException(status_code=422, detail="启用大模型前请先配置 API Key。")

    config.provider_name = payload.provider_name
    config.base_url = str(payload.base_url).rstrip("/")
    config.model_name = payload.model_name
    config.temperature = payload.temperature
    config.max_tokens = payload.max_tokens
    config.is_enabled = payload.is_enabled
    config.notes = payload.notes.strip() if payload.notes and payload.notes.strip() else None

    if payload.clear_api_key:
        config.api_key = None
    elif payload.api_key and payload.api_key.strip():
        set_encrypted_api_key(config, payload.api_key.strip())

    db.commit()
    db.refresh(config)
    return build_llm_config_response(config)
