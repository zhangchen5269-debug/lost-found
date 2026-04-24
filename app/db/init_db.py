"""启动时数据库修复任务。"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def ensure_item_type_varchar(engine: AsyncEngine) -> None:
    """确保 ``items.item_type`` 已迁移为 ``VARCHAR(16)``。"""
    logger.info("开始检查 items.item_type 列类型")

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'items'
                  AND column_name = 'item_type'
                """
            )
        )
        row = result.first()
        data_type = row[0] if row else None

        if data_type in {"character varying", "varchar"}:
            logger.info("items.item_type 已是 %s，跳过迁移", data_type)
            return

        if data_type is None:
            logger.warning("未找到 items.item_type 列，跳过迁移")
            return

        logger.info("检测到 items.item_type 当前类型为 %s，开始迁移为 VARCHAR(16)", data_type)
        await conn.execute(
            text(
                "ALTER TABLE items ALTER COLUMN item_type TYPE VARCHAR(16) USING item_type::text"
            )
        )
        logger.info("items.item_type 迁移完成")
