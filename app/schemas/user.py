"""用户相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """用户公共字段。"""

    username: str = Field(..., min_length=2, max_length=64, description="登录用户名")
    email: EmailStr = Field(..., description="电子邮箱")
    phone: str | None = Field(default=None, max_length=32, description="手机号，可选")


class UserCreate(UserBase):
    """注册请求体。"""

    password: str = Field(..., min_length=6, max_length=128, description="明文密码")


class UserUpdate(BaseModel):
    """更新个人资料（预留扩展）。"""

    phone: str | None = Field(default=None, max_length=32, description="手机号")


class UserRead(UserBase):
    """用户信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户主键")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="注册时间")
