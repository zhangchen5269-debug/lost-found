"""FastAPI 应用入口：中间件、路由注册与全局异常处理。"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine
from app.core.response import error_response, success_response
from app.db.init_db import ensure_item_type_varchar
from app.routers import auth, fix_db, items

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：确保上传目录存在并修复数据库列类型。"""
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    try:
        await ensure_item_type_varchar(engine)
    except Exception as exc:
        logger.warning("启动时跳过 item_type 自动修复：%s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="失物招领系统后端 API：用户认证、物品发布、筛选分页与认领流程。",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(items.router, prefix="/items", tags=["物品"])
app.include_router(fix_db.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """将 HTTPException 转为统一错误响应。"""
    detail = exc.detail
    message = detail if isinstance(detail, str) else str(detail)
    resp = error_response(message=message, code=exc.status_code)
    if exc.headers:
        for k, v in exc.headers.items():
            resp.headers[k] = v
    return resp


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """请求参数校验失败（422）。"""
    _ = exc
    return error_response(message="参数错误", code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    """未捕获异常，返回 500（生产环境可接入日志系统）。"""
    _ = exc
    return error_response(message="服务器内部错误", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/health", summary="健康检查", tags=["系统"])
async def health() -> dict[str, str]:
    """用于负载均衡或本地探活。"""
    return success_response(data={"status": "ok"})
