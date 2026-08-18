"""Authentication routes.

Actual login/signup is handled client-side via Supabase Auth. This backend
only verifies the resulting token and exposes the resolved identity.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's identity and role",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's id, email, and server-assigned role."""
    return current_user