from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.demo_blueprints import PLATFORM_HIGHLIGHTS, PORTAL_ANNOUNCEMENTS, TENANT_BLUEPRINTS
from app.db.models import PortalAnnouncementRecord, PortalConfig, PortalSchoolProfile, Tenant
from app.schemas.contracts import (
    PortalAnnouncement,
    PortalFeature,
    PortalHeroSettings,
    PortalResponse,
    PortalSchool,
    PortalSchoolAdminItem,
    QuickStat,
    ThemePalette,
)


DEFAULT_HERO_TITLE = "义务教育阶段信息科技课程综合平台"
DEFAULT_HERO_SUBTITLE = "学校门户展示、多校课程运营、机房课堂管理、AI 作业生成与成长分析在同一平台闭环协作。"
DEFAULT_FEATURED_SCHOOL_CODE = "xingzhi-school"


def _blueprint_by_code() -> dict[str, dict]:
    return {blueprint["code"]: blueprint for blueprint in TENANT_BLUEPRINTS}


def get_or_create_portal_config(db: Session) -> PortalConfig:
    config = db.scalar(select(PortalConfig).order_by(PortalConfig.id.asc()).limit(1))
    if not config:
        config = PortalConfig(
            hero_title=DEFAULT_HERO_TITLE,
            hero_subtitle=DEFAULT_HERO_SUBTITLE,
            featured_school_code=DEFAULT_FEATURED_SCHOOL_CODE,
        )
        db.add(config)
        db.flush()
    return config


def portal_school_payload(tenant: Tenant, profile: PortalSchoolProfile | None, blueprint: dict) -> PortalSchoolAdminItem:
    theme_source = tenant.theme_json if tenant.theme_json else blueprint["theme"]
    features_source = profile.features_json if profile else [
        {"title": title, "description": description}
        for title, description in blueprint["features"]
    ]
    metrics_source = profile.metrics_json if profile else [
        {"title": title, "value": value, "hint": hint}
        for title, value, hint in blueprint["metrics"]
    ]

    return PortalSchoolAdminItem(
        id=tenant.id,
        code=tenant.code,
        name=tenant.name,
        district=profile.district if profile else blueprint["district"],
        slogan=profile.slogan if profile else blueprint["slogan"],
        grade_scope=profile.grade_scope if profile else blueprint["grade_scope"],
        theme=ThemePalette.model_validate(theme_source),
        features=[PortalFeature.model_validate(item) for item in features_source],
        metrics=[QuickStat.model_validate(item) for item in metrics_source],
    )


def build_portal_response(db: Session) -> PortalResponse:
    tenants = db.scalars(select(Tenant).order_by(Tenant.id.asc())).all()
    tenant_map = {tenant.code: tenant for tenant in tenants}
    profiles = db.scalars(select(PortalSchoolProfile)).all()
    profile_map = {profile.tenant_id: profile for profile in profiles}
    config = get_or_create_portal_config(db)

    schools: list[PortalSchool] = []
    for blueprint in TENANT_BLUEPRINTS:
        tenant = tenant_map.get(blueprint["code"])
        if not tenant:
            continue
        payload = portal_school_payload(tenant, profile_map.get(tenant.id), blueprint)
        schools.append(
            PortalSchool(
                id=payload.id,
                code=payload.code,
                name=payload.name,
                district=payload.district,
                slogan=payload.slogan,
                grade_scope=payload.grade_scope,
                theme=payload.theme,
                features=payload.features,
                metrics=payload.metrics,
            )
        )

    announcements = db.scalars(
        select(PortalAnnouncementRecord)
        .where(PortalAnnouncementRecord.is_active.is_(True))
        .order_by(PortalAnnouncementRecord.display_order.asc(), PortalAnnouncementRecord.published_at.desc())
    ).all()

    return PortalResponse(
        hero_title=config.hero_title,
        hero_subtitle=config.hero_subtitle,
        featured_school_code=config.featured_school_code,
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
        platform_highlights=[PortalFeature.model_validate(item) for item in PLATFORM_HIGHLIGHTS],
    )


def build_portal_admin_school_items(db: Session) -> list[PortalSchoolAdminItem]:
    blueprints = _blueprint_by_code()
    tenants = db.scalars(select(Tenant).order_by(Tenant.id.asc())).all()
    profiles = db.scalars(select(PortalSchoolProfile)).all()
    profile_map = {profile.tenant_id: profile for profile in profiles}

    return [
        portal_school_payload(tenant, profile_map.get(tenant.id), blueprints.get(tenant.code, {}))
        for tenant in tenants
        if tenant.code in blueprints
    ]


def build_default_announcement_payloads() -> list[dict]:
    return [
        {
            "title": item["title"],
            "tag": item["tag"],
            "summary": item["summary"],
            "published_at": item["published_at"],
            "display_order": index,
            "is_active": True,
        }
        for index, item in enumerate(PORTAL_ANNOUNCEMENTS, start=1)
    ]

