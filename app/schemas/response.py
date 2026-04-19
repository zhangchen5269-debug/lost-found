"""统一 API 响应 Schema。

所有接口统一返回：
{
  "success": true/false,
  "code": 200,
  "message": "操作成功",
  "data": {...} 或 null
}
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """通用响应基类（泛型）。"""

    success: bool = Field(..., description="是否成功")
    code: int = Field(..., description="HTTP 状态码或业务码")
    message: str = Field(..., description="中文提示信息")
    data: T | None = Field(default=None, description="响应数据，失败时通常为 null")


class SuccessResponse(BaseResponse[T], Generic[T]):
    """成功响应。"""

    success: bool = Field(default=True)
    code: int = Field(default=200)
    message: str = Field(default="操作成功")


class ErrorResponse(BaseResponse[None]):
    """失败响应。"""

    success: bool = Field(default=False)
    code: int = Field(default=400)
    message: str = Field(default="操作失败")
    data: None = None

