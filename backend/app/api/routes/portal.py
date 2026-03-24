from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.demo_blueprints import PLATFORM_HIGHLIGHTS, PORTAL_ANNOUNCEMENTS, TENANT_BLUEPRINTS
from app.db.models import Tenant
from app.db.session import get_db
from app.schemas.contracts import (
    PortalAnnouncement,
    PortalFeature,
    PortalResponse,
    PortalSchool,
    QuickStat,
    ThemePalette,
)

router = APIRouter()


@router.get("/portal", response_model=PortalResponse)
def get_portal(db: Session = Depends(get_db)):
    tenants = db.scalars(select(Tenant).order_by(Tenant.id.asc())).all()
    tenant_map = {tenant.code: tenant for tenant in tenants}

    schools: list[PortalSchool] = []
    for blueprint in TENANT_BLUEPRINTS:
        tenant = tenant_map.get(blueprint["code"])
        school_id = tenant.id if tenant else 0
        theme_source = tenant.theme_json if tenant else blueprint["theme"]
        schools.append(
            PortalSchool(
                id=school_id,
                code=blueprint["code"],
                name=blueprint["name"],
                district=blueprint["district"],
                slogan=blueprint["slogan"],
                grade_scope=blueprint["grade_scope"],
                theme=ThemePalette.model_validate(theme_source),
                features=[
                    PortalFeature(title=title, description=description)
                    for title, description in blueprint["features"]
                ],
                metrics=[
                    QuickStat(title=title, value=value, hint=hint)
                    for title, value, hint in blueprint["metrics"]
                ],
            )
        )

    return PortalResponse(
        hero_title="义务教育阶段信息科技课程综合平台",
        hero_subtitle="学校门户展示、多校课程运营、机房课堂管理、AI 作业生成与成长分析在同一平台闭环协作。",
        featured_school_code="xingzhi-school",
        schools=schools,
        announcements=[PortalAnnouncement.model_validate(item) for item in PORTAL_ANNOUNCEMENTS],
        platform_highlights=[PortalFeature.model_validate(item) for item in PLATFORM_HIGHLIGHTS],
    )
