"""Authentication middleware and dependencies."""

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_agent_secret: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current authenticated user.

    Supports:
    1. JWT Bearer token (from web UI)
    2. x-agent-secret header (for MCP agents)
    """
    # Try API key first (for agents)
    if x_agent_secret:
        user = await AuthService.get_user_by_api_key(db, x_agent_secret)
        if user and user.is_active:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Try JWT token
    if credentials:
        payload = AuthService.decode_access_token(credentials.credentials)
        if payload:
            user_id = int(payload.get("sub", 0))
            user = await AuthService.get_user_by_id(db, user_id)
            if user and user.is_active:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_agent_secret: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get the current user if authenticated, otherwise None.

    This allows endpoints to work for both authenticated and anonymous users.
    """
    # Try API key first (for agents)
    if x_agent_secret:
        user = await AuthService.get_user_by_api_key(db, x_agent_secret)
        if user and user.is_active:
            return user
        return None

    # Try JWT token
    if credentials:
        payload = AuthService.decode_access_token(credentials.credentials)
        if payload:
            user_id = int(payload.get("sub", 0))
            user = await AuthService.get_user_by_id(db, user_id)
            if user and user.is_active:
                return user

    return None


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
