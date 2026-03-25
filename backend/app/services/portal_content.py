from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.demo_blueprints import PLATFORM_HIGHLIGHTS, PORTAL_ANNOUNCEMENTS, TENANT_BLUEPRINTS
from app.db.models import PortalAnnouncementRecord, PortalConfig, PortalSchoolProfile, SchoolRegistrationApplication, Tenant
from app.schemas.contracts import (
    PortalAnnouncement,
    PortalFeature,
    PortalHeroSettings,
    PortalResponse,
    PortalSchool,
    PortalSchoolAdminItem,
    QuickStat,
    SchoolApplication,
    ThemePalette,
)


DEFAULT_HERO_TITLE = "义务教育阶段信息科技课程综合平台"
DEFAULT_HERO_SUBTITLE = "学校门户展示、多校课程运营、机房课堂管理、AI 作业生成与成长分析在同一平台闭环协作。"
DEFAULT_FEATURED_SCHOOL_CODE = "xingzhi-school"
DEFAULT_SCHOOL_THEME = {"primary": "#2F6FED", "secondary": "#14B8A6", "accent": "#F59E0B"}


def _blueprint_by_code() -> dict[str, dict]:
    return {blueprint["code"]: blueprint for blueprint in TENANT_BLUEPRINTS}


def _fallback_school_blueprint(tenant: Tenant) -> dict:
    return {
        "theme": tenant.theme_json or DEFAULT_SCHOOL_THEME,
        "district": "待完善",
        "slogan": f"{tenant.name} 正在完善学校门户资料。",
        "grade_scope": "义务教育阶段",
        "features": [
            ("学校门户", "支持学校展示、统一登录和学校专属主题风格。"),
            ("课程运营", "后续可由学校管理员维护本校教师、课程与课堂入口。"),
            ("AI 教学能力", "可结合学校侧后台持续补充智能体、作业与分析能力。"),
        ],
        "metrics": [
            ("课程目录", "待配置", "学校开通后可逐步补齐课程目录与专题模块"),
            ("教师账号", "待配置", "学校管理员可在后台继续添加教师账号"),
            ("学校状态", tenant.status, "通过入驻审核后会自动出现在门户学校列表中"),
        ],
    }


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
    source = {**_fallback_school_blueprint(tenant), **(blueprint or {})}
    theme_source = tenant.theme_json if tenant.theme_json else source["theme"]
    features_source = profile.features_json if profile else [
        {"title": title, "description": description}
        for title, description in source["features"]
    ]
    metrics_source = profile.metrics_json if profile else [
        {"title": title, "value": value, "hint": hint}
        for title, value, hint in source["metrics"]
    ]

    return PortalSchoolAdminItem(
        id=tenant.id,
        code=tenant.code,
        name=tenant.name,
        district=profile.district if profile else source["district"],
        slogan=profile.slogan if profile else source["slogan"],
        grade_scope=profile.grade_scope if profile else source["grade_scope"],
        theme=ThemePalette.model_validate(theme_source),
        features=[PortalFeature.model_validate(item) for item in features_source],
        metrics=[QuickStat.model_validate(item) for item in metrics_source],
    )


def build_portal_response(db: Session) -> PortalResponse:
    tenants = db.scalars(select(Tenant).order_by(Tenant.id.asc())).all()
    profiles = db.scalars(select(PortalSchoolProfile)).all()
    profile_map = {profile.tenant_id: profile for profile in profiles}
    config = get_or_create_portal_config(db)
    blueprints = _blueprint_by_code()

    schools: list[PortalSchool] = []
    for tenant in tenants:
        payload = portal_school_payload(tenant, profile_map.get(tenant.id), blueprints.get(tenant.code, {}))
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
    ]


def serialize_school_application(application: SchoolRegistrationApplication) -> SchoolApplication:
    return SchoolApplication(
        id=application.id,
        school_name=application.school_name,
        school_code=application.school_code,
        district=application.district,
        grade_scope=application.grade_scope,
        slogan=application.slogan,
        contact_name=application.contact_name,
        contact_phone=application.contact_phone,
        applicant_display_name=application.applicant_display_name,
        applicant_username=application.applicant_username,
        note=application.note,
        status=application.status,
        review_note=application.review_note,
        created_at=application.created_at,
        reviewed_at=application.reviewed_at,
        approved_tenant_id=application.approved_tenant_id,
    )


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
