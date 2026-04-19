"""认证与用户资料路由。"""

from datetime import timedelta

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.response import Responder, get_responder
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import SuccessResponse
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=SuccessResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="使用用户名、邮箱、密码注册；手机号可选。",
    response_description="统一响应：data 为用户信息（不含密码）。",
    responses={
        201: {
            "description": "注册成功",
            "content": {
                "application/json": {
                    "examples": {
                        "注册成功": {
                            "summary": "注册成功示例",
                            "value": {
                                "success": True,
                                "code": 201,
                                "message": "注册成功",
                                "data": {
                                    "id": 1,
                                    "username": "u1",
                                    "email": "u1@example.com",
                                    "phone": None,
                                    "is_active": True,
                                    "created_at": "2026-04-13T12:00:00Z",
                                },
                            },
                        }
                    }
                }
            },
        },
        409: {
            "description": "用户名/邮箱冲突",
            "content": {
                "application/json": {
                    "examples": {
                        "用户名已占用": {
                            "summary": "用户名冲突",
                            "value": {"success": False, "code": 409, "message": "用户名已被占用", "data": None},
                        },
                        "邮箱已注册": {
                            "summary": "邮箱冲突",
                            "value": {"success": False, "code": 409, "message": "邮箱已被注册", "data": None},
                        },
                    }
                }
            },
        },
    },
)
async def register_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    r: Responder = Depends(get_responder),
):
    """注册新用户；用户名或邮箱冲突时返回 409。"""
    if await user_crud.get_user_by_username(db, body.username):
        return r.error(message="用户名已被占用", code=status.HTTP_409_CONFLICT)
    if await user_crud.get_user_by_email(db, str(body.email)):
        return r.error(message="邮箱已被注册", code=status.HTTP_409_CONFLICT)
    try:
        user = await user_crud.create_user(db, body)
    except IntegrityError as exc:
        await db.rollback()
        _ = exc
        return r.error(message="数据冲突", code=status.HTTP_409_CONFLICT)
    await db.commit()
    await db.refresh(user)
    return r.success(data=UserRead.model_validate(user), message="注册成功", code=status.HTTP_201_CREATED)


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    summary="用户登录",
    description="使用 OAuth2 密码流表单提交用户名/邮箱与密码，返回 JWT。",
    response_description="统一响应：data.access_token 为 JWT；后续请求用 Authorization: Bearer <token>。",
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "examples": {
                        "登录成功": {
                            "summary": "登录成功示例",
                            "value": {
                                "success": True,
                                "code": 200,
                                "message": "登录成功",
                                "data": {
                                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                    "token_type": "bearer",
                                },
                            },
                        }
                    }
                }
            },
        },
        401: {
            "description": "用户名或密码错误",
            "content": {
                "application/json": {
                    "examples": {
                        "登录失败": {
                            "summary": "账号或密码错误",
                            "value": {"success": False, "code": 401, "message": "用户名或密码错误", "data": None},
                        }
                    }
                }
            },
        },
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    r: Responder = Depends(get_responder),
):
    """
    登录接口。

    表单字段 ``username`` 可填写用户名或邮箱；``password`` 为明文密码。
    """
    user = await user_crud.authenticate_user(
        db,
        login=form_data.username,
        password=form_data.password,
    )
    if user is None:
        return r.error(message="用户名或密码错误", code=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return r.error(message="用户已被禁用", code=status.HTTP_403_FORBIDDEN)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return r.success(data=Token(access_token=access_token, token_type="bearer"), message="登录成功", code=200)


@router.get(
    "/me",
    response_model=SuccessResponse[UserRead],
    summary="获取当前用户信息",
    description="需要携带有效的 Bearer Token。",
)
async def read_me(
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """返回当前登录用户的基本资料。"""
    return r.success(data=UserRead.model_validate(current_user))
