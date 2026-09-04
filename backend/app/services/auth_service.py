"""Authentication service."""

import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_access_token(token: str) -> dict | None:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate an API key and its hash.

        Returns:
            Tuple of (plain_key, hashed_key)
        """
        plain_key = secrets.token_urlsafe(32)
        hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
        return plain_key, hashed_key

    @staticmethod
    def hash_api_key(key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    async def get_user_by_api_key(db: AsyncSession, api_key: str) -> User | None:
        """Get user by API key."""
        hashed_key = AuthService.hash_api_key(api_key)
        result = await db.execute(
            select(User).where(User.api_key_hash == hashed_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_github_id(db: AsyncSession, github_id: int) -> User | None:
        """Get user by GitHub ID."""
        result = await db.execute(
            select(User).where(User.github_id == github_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update_user(
        db: AsyncSession,
        github_id: int,
        username: str,
        email: str | None = None,
        avatar_url: str | None = None,
        display_name: str | None = None,
    ) -> User:
        """Create or update a user from GitHub OAuth."""
        user = await AuthService.get_user_by_github_id(db, github_id)

        if user:
            # Update existing user
            user.username = username
            user.email = email
            user.avatar_url = avatar_url
            user.display_name = display_name
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                github_id=github_id,
                username=username,
                email=email,
                avatar_url=avatar_url,
                display_name=display_name,
                last_login=datetime.utcnow(),
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user
