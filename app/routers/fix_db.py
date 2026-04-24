"""临时数据库修复接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text

from app.core.database import engine

router = APIRouter(tags=["数据库修复"])

FIX_TOKEN = "fix2026"


@router.get("/fix-item-type", summary="修复 items.item_type 列类型")
async def fix_item_type(token: str = Query(default=FIX_TOKEN)):
    """临时修复 ``items.item_type`` 从旧 ENUM 到 VARCHAR。"""
    if token != FIX_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

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
        before = row[0] if row else None

        if before in {"character varying", "varchar"}:
            return {"message": "already varchar", "type": "varchar"}

        await conn.execute(
            text(
                "ALTER TABLE items ALTER COLUMN item_type TYPE VARCHAR(16) USING item_type::text"
            )
        )

        result_after = await conn.execute(
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
        row_after = result_after.first()
        after = row_after[0] if row_after else "unknown"

        return {"before": before, "after": after, "success": True}
