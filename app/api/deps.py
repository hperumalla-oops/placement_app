"""Reusable FastAPI dependencies: DB session, authentication, and role checks.

Every protected route depends on `get_current_user` (or one of the
role-restricted wrappers below) so that authorization is enforced
server-side, never trusted from the client.
"""

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.enums import UserRole
from app.models.student import Student
from app.models.user import User
from app.repositories.student import StudentRepository
from app.services.auth_serivce import AuthService

# Does not auto-error so we can raise our own UnauthorizedError with a
# consistent JSON shape instead of FastAPI's default 403.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a verified Supabase JWT.

    Raises:
        UnauthorizedError: If no token is supplied, or it is invalid/expired,
                            or the user has no matching row in public.users.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token.")

    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials.credentials)


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Dependency factory that restricts an endpoint to specific roles.

    Usage:
        @router.post("/drives", dependencies=[Depends(require_roles(UserRole.SPC, UserRole.ADMIN))])
    """

    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                f"This action requires one of the following roles: "
                f"{', '.join(r.value for r in allowed_roles)}."
            )
        return current_user

    return _check_role


# Convenience pre-built dependencies for the common cases.
require_student = require_roles(UserRole.STUDENT)
require_spc = require_roles(UserRole.SPC, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)


async def get_current_student(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Student:
    """Resolve the Student profile belonging to the authenticated user.

    Raises:
        ForbiddenError: If the authenticated user is not a STUDENT.
        NotFoundError: If the user has no student profile row yet.
    """
    if current_user.role != UserRole.STUDENT:
        raise ForbiddenError("This action is only available to students.")

    student = await StudentRepository(db).get_by_user_id(current_user.id)
    if student is None:
        raise NotFoundError("No student profile found for this account.")
    return student