from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.auth_service import get_user_from_token
from app.services.dashboard_service import get_dashboard_summary

security = HTTPBearer(auto_error=False)

router = APIRouter()


@router.get('/summary', response_model=DashboardSummaryResponse)
def summary(
    start_date: date | None = None,
    end_date: date | None = None,
    department_id: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='start_date must be before end_date')

    # Auth check; response shape can be used by role-aware frontend widgets.
    get_user_from_token(credentials.credentials, db=db)

    return get_dashboard_summary(
        db=db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
    )
