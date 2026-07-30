from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.user import User
from schemas.model_call_dashboard import (
    ModelCallDashboardResponse,
)
from services.model_call_dashboard_service import (
    get_model_call_dashboard,
)


router = APIRouter(
    prefix="/model-calls",
    tags=["Model Calls"],
)


@router.get(
    "/dashboard",
    response_model=ModelCallDashboardResponse,
)
def read_model_call_dashboard(
    limit: int = Query(
        default=25,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return routing, usage, latency and estimated-cost metrics for the
    currently authenticated user.
    """

    return get_model_call_dashboard(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
