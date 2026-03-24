from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.contracts import PortalResponse
from app.services.portal_content import build_portal_response

router = APIRouter()


@router.get("/portal", response_model=PortalResponse)
def get_portal(db: Session = Depends(get_db)):
    return build_portal_response(db)
