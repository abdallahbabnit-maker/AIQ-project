import base64
import hashlib
import hmac
import json
import time
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)
PBKDF2_ROUNDS = 120000


def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS)
    return salt + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hexdigest = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS)
    return hmac.compare_digest(digest.hex(), hexdigest)


def _sign(payload_b64: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(),
                    hashlib.sha256).hexdigest()


def create_token(user_id: str, role: str, ttl_seconds: int = 86400) -> str:
    payload = {"sub": user_id, "role": role, "exp": int(time.time()) + ttl_seconds}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return payload_b64 + "." + _sign(payload_b64)


def decode_token(token: str) -> dict:
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        raise HTTPException(401, "invalid_token")
    if not hmac.compare_digest(sig, _sign(payload_b64)):
        raise HTTPException(401, "invalid_token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))
    except Exception:
        raise HTTPException(401, "invalid_token")
    if payload.get("exp", 0) < time.time():
        raise HTTPException(401, "token_expired")
    return payload


async def require_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if credentials is None:
        raise HTTPException(401, "not_authenticated")
    return decode_token(credentials.credentials)


async def require_reviewer(user: dict = Depends(require_user)) -> dict:
    if user.get("role") not in ("founder", "reviewer"):
        raise HTTPException(403, "role_not_allowed")
    return user
