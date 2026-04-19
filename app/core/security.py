"""密码哈希与 JWT 编解码工具。"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码是否与哈希一致。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """使用 bcrypt 对密码进行哈希。"""
    return pwd_context.hash(password)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """生成 JWT access_token，subject 通常为用户 ID。"""
    to_encode: dict[str, Any] = {"sub": str(subject)}
    expire = datetime.now(tz=UTC) + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """解析 JWT；无效或过期时抛出 jwt.PyJWTError。"""
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    return payload
