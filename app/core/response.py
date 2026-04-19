"""统一 API 响应工具函数与依赖注入封装。"""

from __future__ import annotations

from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.schemas.response import ErrorResponse, SuccessResponse


def simple_success(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200,
) -> dict[str, Any]:
    """构造成功响应的 dict（不包装为 JSONResponse，便于内部调用/复用）。"""
    payload = SuccessResponse[Any](success=True, code=code, message=message, data=data)
    return jsonable_encoder(payload)


def simple_error(
    message: str = "操作失败",
    code: int = 400,
    data: Any = None,
) -> dict[str, Any]:
    """构造失败响应的 dict（不包装为 JSONResponse，便于内部调用/复用）。"""
    payload = ErrorResponse(success=False, code=code, message=message, data=None if data is None else data)  # type: ignore[arg-type]
    payload.data = None
    return jsonable_encoder(payload)


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200,
) -> JSONResponse:
    """构造成功 JSON 响应。"""
    return JSONResponse(status_code=code, content=simple_success(data=data, message=message, code=code))


def error_response(
    message: str = "操作失败",
    code: int = 400,
    data: Any = None,
) -> JSONResponse:
    """构造失败 JSON 响应。"""
    return JSONResponse(status_code=code, content=simple_error(message=message, code=code, data=data))


class Responder:
    """通过依赖注入提供统一响应方法。"""

    def success(self, data: Any = None, message: str = "操作成功", code: int = 200) -> JSONResponse:
        """成功响应。"""
        return success_response(data=data, message=message, code=code)

    def error(self, message: str = "操作失败", code: int = 400, data: Any = None) -> JSONResponse:
        """失败响应。"""
        return error_response(message=message, code=code, data=data)

    def simple_success(self, data: Any = None, message: str = "操作成功", code: int = 200) -> dict[str, Any]:
        """成功响应（dict 版本）。"""
        return simple_success(data=data, message=message, code=code)

    def simple_error(self, message: str = "操作失败", code: int = 400, data: Any = None) -> dict[str, Any]:
        """失败响应（dict 版本）。"""
        return simple_error(message=message, code=code, data=data)


def get_responder() -> Responder:
    """FastAPI 依赖：注入 Responder。"""
    return Responder()

