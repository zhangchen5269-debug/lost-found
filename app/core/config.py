"""应用配置：使用 pydantic-settings 从环境变量加载。"""

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _async_to_sync_database_url(async_url: str) -> str:
    """
    将异步驱动数据库 URL 转为 Alembic / 同步引擎可用的 URL。

    例如 ``sqlite+aiosqlite:///dev.db`` → ``sqlite:///dev.db``；
    ``postgresql+asyncpg://...`` → ``postgresql+psycopg://...``。
    """
    if async_url.startswith("sqlite+aiosqlite"):
        return async_url.replace("sqlite+aiosqlite", "sqlite", 1)
    if async_url.startswith("postgresql+asyncpg"):
        return async_url.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
    return async_url


class Settings(BaseSettings):
    """全局配置项；数据库连接统一由 ``DATABASE_URL`` 提供。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = Field(default="失物招领系统", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")

    secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        description="JWT 签名密钥",
    )
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(default=60 * 24, description="访问令牌过期分钟数")

    database_url: str = Field(
        default="sqlite+aiosqlite:///dev.db",
        description="异步 SQLAlchemy 数据库 URL（环境变量 DATABASE_URL）",
    )

    upload_dir: str = Field(default="./uploads", description="上传文件保存目录（占位）")
    public_upload_base_url: str = Field(
        default="",
        description="对外暴露的上传资源 URL 前缀；为空时在 Railway 自动推导",
    )
    railway_public_domain: str | None = Field(
        default=None,
        validation_alias="RAILWAY_PUBLIC_DOMAIN",
        description="Railway 自动注入的公网域名（通常为 RAILWAY_PUBLIC_DOMAIN）",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def public_upload_base_url_effective(self) -> str:
        """最终对外上传 URL 前缀：优先 public_upload_base_url，其次 Railway 域名。"""
        if self.public_upload_base_url:
            return self.public_upload_base_url.rstrip("/")
        if self.railway_public_domain:
            # Railway 通常提供形如 xxx.up.railway.app
            return f"https://{self.railway_public_domain}/static/uploads"
        return "http://127.0.0.1:8000/static/uploads"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """异步 SQLAlchemy 使用的数据库 URL（与 ``database_url`` 一致）。"""
        return self.database_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri_sync(self) -> str:
        """Alembic 等同步迁移使用的数据库 URL。"""
        return _async_to_sync_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """返回单例 Settings，便于依赖注入与测试。"""
    return Settings()


settings = get_settings()
