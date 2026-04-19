"""用户 CRUD。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """按主键查询用户。"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """按邮箱查询用户。"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """按用户名查询用户。"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, *, login: str, password: str) -> User | None:
    """
    使用用户名或邮箱 + 密码校验用户。

    :param login: 用户名或邮箱（与注册时一致）。
    """
    user = await get_user_by_username(db, login)
    if user is None:
        user = await get_user_by_email(db, login)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, obj_in: UserCreate) -> User:
    """创建用户并持久化。"""
    user = User(
        username=obj_in.username,
        email=str(obj_in.email),
        phone=obj_in.phone,
        hashed_password=get_password_hash(obj_in.password),
    )
    db.add(user)
    await db.flush()
    return user
