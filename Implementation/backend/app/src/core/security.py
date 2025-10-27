# src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..core.settings import settings
from ..db.database import get_db
from ..repositories.admin_sqlalchemy import AdminRepository
from ..models.admin import AdminRole

ALGORITHM = "HS256"


pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
)

# ---------------- Passwords ----------------
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def maybe_upgrade_password(admin, plain_password: str, db_session) -> None:
    """
    If the stored hash uses a deprecated scheme (e.g. pbkdf2_sha256),
    transparently rehash to bcrypt after a successful login.
    """
    if pwd_context.needs_update(admin.password):
        admin.password = pwd_context.hash(plain_password)
        db_session.add(admin)
        db_session.commit()

# ---------------- JWT ----------------
def create_access_token(*, subject: str | int, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": str(subject), "exp": expire}

    secret = settings.SECRET_KEY.get_secret_value() if hasattr(settings.SECRET_KEY, "get_secret_value") else settings.SECRET_KEY
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)

# ---------------- Current user ----------------
async def get_current_admin(request: Request, db=Depends(get_db)):
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        secret = settings.SECRET_KEY.get_secret_value() if hasattr(settings.SECRET_KEY, "get_secret_value") else settings.SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    repo = AdminRepository(db)
    admin = repo.get(int(sub))
    if not admin:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return admin

# ---------------- RBAC ----------------
ROLE_ORDER = {
    AdminRole.viewer: 1,
    AdminRole.admin: 2,
    AdminRole.owner: 3,
}

def require_role(min_role: AdminRole):
    def dependency(current=Depends(get_current_admin)):
        if ROLE_ORDER[current.role] < ROLE_ORDER[min_role]:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current
    return dependency
