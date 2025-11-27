from fastapi import Depends, Header, HTTPException, status
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from functools import lru_cache
from typing import Optional

from .config import settings
from ..models.user import AuthenticatedUser


@lru_cache(maxsize=1)
def _init_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    project_id = settings.fb_project_id
    client_email = settings.fb_client_email
    private_key = settings.fb_private_key

    if private_key:
        private_key = (
            private_key.replace("\\n", "\n")
            .replace("\\r", "\n")
            .replace('"', "")
            .strip()
        )

    cred = None
    if project_id and client_email and private_key:
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": project_id,
                "client_email": client_email,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
    else:
        cred = credentials.ApplicationDefault()

    return firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)


def _decode_token(token: str) -> AuthenticatedUser:
    _init_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from exc

    raw_role: Optional[str] = decoded.get("role")
    role = raw_role if raw_role in {"admin", "pm"} else "user"
    return AuthenticatedUser(uid=decoded.get("uid"), email=decoded.get("email"), role=role)


async def get_current_user(authorization: Optional[str] = Header(None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    return _decode_token(token)


async def require_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user
