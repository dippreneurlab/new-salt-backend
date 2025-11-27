from firebase_admin import auth as firebase_auth

from ..core.auth import _init_firebase_app


async def set_user_role(uid: str, role: str):
    _init_firebase_app()
    firebase_auth.set_custom_user_claims(uid, {"role": role})
