"""JWT 与令牌相关 Schema。"""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """登录成功返回的访问令牌。"""

    access_token: str = Field(..., description="JWT access_token")
    token_type: str = Field(default="bearer", description="令牌类型，固定为 bearer")


class TokenPayload(BaseModel):
    """JWT 载荷解析结果（内部使用）。"""

    sub: str | None = Field(default=None, description="主题，一般为用户 ID")
