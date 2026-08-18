"""Authentication service — verifies Supabase JWTs and returns user records."""

import logging

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import extract_supabase_user_id, verify_supabase_token
from app.models.user import User
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Verifies Supabase tokens and resolves authenticated users.

    The user's role is ALWAYS retrieved from public.users — never trusted
    from the JWT payload.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._user_repo = UserRepository(db)

    async def get_current_user(self, token: str) -> User:
        """Verify a Bearer token and return the corresponding User.

        Args:
            token: Raw JWT string (without 'Bearer ' prefix).

        Returns:
            The authenticated User from public.users.

        Raises:
            UnauthorizedError: If the token is invalid, expired, or the
                               user cannot be found in public.users.
        """
        # Step 1: Verify JWT signature and expiry
        try:
            payload = verify_supabase_token(token)
        except JWTError as exc:
            logger.warning("Invalid JWT received: %s", exc)
            raise UnauthorizedError("Invalid or expired authentication token.")

        # Step 2: Extract the user ID (sub claim)
        try:
            user_id_str = extract_supabase_user_id(payload)
        except ValueError:
            raise UnauthorizedError("Malformed authentication token: missing user ID.")

        # Step 3: Look up user in public.users by UUID
        import uuid
        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise UnauthorizedError("Malformed authentication token: invalid user ID format.")

        user = await self._user_repo.get_by_id(user_uuid)
        if user is None:
            logger.warning(
                "Authenticated Supabase user %s not found in public.users. "
                "User may not have completed registration.",
                user_id_str,
            )
            raise UnauthorizedError(
                "User account not found. Please complete registration."
            )

        return user
