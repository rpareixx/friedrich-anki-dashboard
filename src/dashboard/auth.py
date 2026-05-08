from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.config import Settings, get_settings
from dashboard.db import get_session
from dashboard.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def require_pipeline_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    if creds is None or creds.credentials != settings.pipeline_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing pipeline token",
        )


def require_state_access(
    request: Request,
    user_slug: str,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    cf_email = request.headers.get("Cf-Access-Authenticated-User-Email")
    if cf_email:
        user = session.execute(select(User).where(User.email == cf_email)).scalar_one_or_none()
        if user is None or user.slug != user_slug:
            raise HTTPException(status_code=403, detail="user mismatch")
        return user

    if creds is not None and creds.credentials == settings.dev_token:
        user = session.execute(select(User).where(User.slug == user_slug)).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        return user

    raise HTTPException(status_code=401, detail="authentication required")
