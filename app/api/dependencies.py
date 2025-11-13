"""Shared FastAPI dependencies for authentication and authorization."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, UserType
from app.services.auth_service import auth_service

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the currently authenticated user using a JWT bearer token."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.get(User, user_id_int)
    if user is None or not bool(user.is_active):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    return user


def require_role(required_role: UserType):
    """Create a dependency that ensures the current user has the given role."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        current_role = getattr(current_user, "user_type", None)
        if not isinstance(current_role, UserType):
            try:
                current_role = UserType(str(current_role))
            except ValueError:
                current_role = None

        if current_role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


def require_any_role(*allowed_roles: UserType):
    """Ensure the current user matches one of the allowed roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        current_role = getattr(current_user, "user_type", None)
        if not isinstance(current_role, UserType):
            try:
                current_role = UserType(str(current_role))
            except ValueError:
                current_role = None

        if allowed_roles and current_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


