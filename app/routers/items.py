"""失物招领物品与上传路由。"""

import uuid
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.response import Responder, get_responder
from app.crud import item as item_crud
from app.dependencies.auth import get_current_user
from app.models.item import ItemCategory, ItemStatus, ItemType
from app.models.user import User
from app.schemas.response import SuccessResponse
from app.schemas.item import (
    ClaimedItemsListData,
    ItemCreate,
    ItemRead,
    ItemStatusSchema,
    ItemUpdate,
    MyItemsListData,
)
from app.utils.pagination import resolve_pagination

router = APIRouter()


class UploadImageData(BaseModel):
    """上传图片返回数据。"""

    url: str = Field(..., description="图片访问 URL")


class ItemsListData(BaseModel):
    """物品列表返回数据。"""

    items: list[ItemRead]
    total: int
    page: int
    page_size: int


@router.post(
    "/upload/image",
    response_model=SuccessResponse[UploadImageData],
    summary="上传图片",
    description="multipart 上传图片文件，返回可访问的 URL（占位实现，后续可对接对象存储）。",
    response_description="统一响应：data.url 为图片可访问地址。",
)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """保存文件到本地目录并拼接对外 URL。"""
    if not file.filename:
        return r.error(message="文件名无效", code=status.HTTP_400_BAD_REQUEST)

    content_type = (file.content_type or "").lower().strip()
    if not content_type.startswith("image/"):
        return r.error(message="仅允许上传图片类型文件", code=status.HTTP_400_BAD_REQUEST)
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return r.error(message="仅支持常见图片格式", code=status.HTTP_400_BAD_REQUEST)

    safe_suffix = suffix
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}{safe_suffix}"
    dest = upload_root / new_name

    max_bytes = 5 * 1024 * 1024
    written = 0
    try:
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    try:
                        dest.unlink(missing_ok=True)
                    except Exception:
                        pass
                    return r.error(message="文件过大（最大 5MB）", code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                f.write(chunk)
    finally:
        await file.close()

    base = settings.public_upload_base_url_effective.rstrip("/")
    url = f"{base}/{new_name}"
    return r.success(data=UploadImageData(url=url), message="上传成功", code=200)


@router.get(
    "/my/published",
    response_model=SuccessResponse[MyItemsListData],
    summary="我的发布列表",
    description="需要登录；返回当前用户发布的物品列表（带分页）。",
    response_description="统一响应：data.items 为我的发布列表，data.total 为总数。",
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "examples": {
                        "我的发布": {
                            "summary": "我的发布列表示例",
                            "value": {
                                "success": True,
                                "code": 200,
                                "message": "操作成功",
                                "data": {
                                    "items": [
                                        {
                                            "id": 1,
                                            "title": "钱包",
                                            "description": "黑色皮质钱包",
                                            "item_type": "lost",
                                            "location": "图书馆二楼",
                                            "event_date": "2026-04-01",
                                            "category": "other",
                                            "image_url": None,
                                            "status": "open",
                                            "user_id": 1,
                                            "claimant_id": None,
                                            "created_at": "2026-04-13T12:00:00Z",
                                        }
                                    ],
                                    "total": 1,
                                },
                            },
                        }
                    }
                }
            },
        }
    },
)
async def my_published_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    r: Responder = Depends(get_responder),
):
    """获取当前用户发布的物品列表。"""
    p = resolve_pagination(page, page_size)
    items, total = await item_crud.get_user_items(
        db,
        user_id=current_user.id,
        skip=p.skip,
        limit=p.limit,
    )
    data = MyItemsListData(items=[ItemRead.model_validate(i) for i in items], total=total)
    return r.success(data=data)


@router.get(
    "/my/claimed",
    response_model=SuccessResponse[ClaimedItemsListData],
    summary="我认领的物品列表",
    description="需要登录；返回当前用户认领的物品列表（带分页）。",
)
async def my_claimed_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    r: Responder = Depends(get_responder),
):
    """获取当前用户认领的物品列表。"""
    p = resolve_pagination(page, page_size)
    items, total = await item_crud.get_user_claimed_items(
        db,
        claimant_id=current_user.id,
        skip=p.skip,
        limit=p.limit,
    )
    data = ClaimedItemsListData(items=[ItemRead.model_validate(i) for i in items], total=total)
    return r.success(data=data)


@router.post(
    "",
    response_model=SuccessResponse[ItemRead],
    status_code=status.HTTP_201_CREATED,
    summary="发布物品",
    description="创建一条失物或招领信息，初始状态为 open。",
    response_description="统一响应：data 为物品详情。",
    responses={
        201: {
            "description": "发布成功",
            "content": {
                "application/json": {
                    "examples": {
                        "发布成功": {
                            "summary": "发布物品示例",
                            "value": {
                                "success": True,
                                "code": 201,
                                "message": "发布成功",
                                "data": {
                                    "id": 1,
                                    "title": "校园卡",
                                    "description": "在食堂附近丢失",
                                    "item_type": "lost",
                                    "location": "一食堂门口",
                                    "event_date": "2026-04-02",
                                    "category": "id_document",
                                    "image_url": None,
                                    "status": "open",
                                    "user_id": 1,
                                    "claimant_id": None,
                                    "created_at": "2026-04-13T12:00:00Z",
                                },
                            },
                        }
                    }
                }
            },
        }
    },
)
async def create_item_endpoint(
    body: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """当前登录用户发布物品。"""
    item = await item_crud.create_item(db, obj_in=body, owner_id=current_user.id)
    await db.commit()
    await db.refresh(item)
    return r.success(
        data=ItemRead.model_validate(item),
        message="发布成功",
        code=status.HTTP_201_CREATED,
    )


@router.get(
    "",
    response_model=SuccessResponse[ItemsListData],
    summary="物品列表",
    description="支持分页与多条件筛选；无需登录。",
    response_description="统一响应：data.items 为列表，data.total 为总数，data.page/page_size 为分页信息。",
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "examples": {
                        "列表查询": {
                            "summary": "列表查询示例",
                            "value": {
                                "success": True,
                                "code": 200,
                                "message": "操作成功",
                                "data": {
                                    "items": [],
                                    "total": 0,
                                    "page": 1,
                                    "page_size": 20,
                                },
                            },
                        }
                    }
                }
            },
        }
    },
)
async def list_items_endpoint(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    item_type: ItemType | None = Query(default=None, description="lost 或 found"),
    category: ItemCategory | None = Query(default=None, description="物品分类"),
    location: str | None = Query(default=None, description="地点模糊搜索"),
    event_date_from: str | None = Query(default=None, description="事件日期起 YYYY-MM-DD"),
    event_date_to: str | None = Query(default=None, description="事件日期止 YYYY-MM-DD"),
    keyword: str | None = Query(default=None, description="标题或描述关键词"),
    sort_by: Literal["newest", "oldest", "event_date"] = Query(
        default="newest",
        description="排序：newest=最新发布，oldest=最早发布，event_date=按事件日期",
    ),
    near: str | None = Query(
        default=None,
        description="可选：用于“简易距离排序”的地点关键字（字符串匹配；后续可升级为真实距离）",
    ),
    r: Responder = Depends(get_responder),
):
    """分页返回物品列表与总数。"""
    try:
        d_from = date.fromisoformat(event_date_from) if event_date_from else None
        d_to = date.fromisoformat(event_date_to) if event_date_to else None
    except ValueError:
        return r.error(message="日期格式应为 YYYY-MM-DD", code=status.HTTP_400_BAD_REQUEST)

    p = resolve_pagination(page, page_size)
    items, total = await item_crud.list_items(
        db,
        skip=p.skip,
        limit=p.limit,
        item_type=item_type,
        category=category,
        location=location,
        event_date_from=d_from,
        event_date_to=d_to,
        keyword=keyword,
        sort_by=sort_by,
        near=near,
    )
    data = ItemsListData(
        items=[ItemRead.model_validate(i) for i in items],
        total=total,
        page=p.page,
        page_size=p.page_size,
    )
    return r.success(data=data)


@router.get(
    "/{item_id}",
    response_model=SuccessResponse[ItemRead],
    summary="物品详情",
    description="按主键获取物品信息；无需登录。",
)
async def get_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    r: Responder = Depends(get_responder),
):
    """返回单条物品详情。"""
    item = await item_crud.get_item(db, item_id)
    if item is None:
        return r.error(message="物品不存在", code=status.HTTP_404_NOT_FOUND)
    return r.success(data=ItemRead.model_validate(item))


@router.patch(
    "/{item_id}",
    response_model=SuccessResponse[ItemRead],
    summary="更新物品",
    description="仅发布者可更新；若将状态设为 resolved，需当前为 claimed。",
)
async def update_item_endpoint(
    item_id: int,
    body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """更新物品字段或状态（发布者权限与状态流转校验）。"""
    item = await item_crud.get_item(db, item_id)
    if item is None:
        return r.error(message="物品不存在", code=status.HTTP_404_NOT_FOUND)
    if item.user_id != current_user.id:
        return r.error(message="只有发布者可以修改物品", code=status.HTTP_403_FORBIDDEN)

    if body.status is not None:
        if body.status != ItemStatusSchema.resolved:
            return r.error(message="状态字段仅允许由发布者更新为 resolved", code=status.HTTP_400_BAD_REQUEST)
        if item.status != ItemStatus.claimed:
            return r.error(message="只有已认领（claimed）的物品可标记为已解决（resolved）", code=status.HTTP_400_BAD_REQUEST)

    updated = await item_crud.update_item(db, db_obj=item, obj_in=body)
    await db.commit()
    await db.refresh(updated)
    return r.success(data=ItemRead.model_validate(updated), message="更新成功", code=200)


@router.delete(
    "/{item_id}",
    response_model=SuccessResponse[None],
    status_code=200,
    summary="删除物品",
    description="仅发布者可删除自己的物品。",
)
async def delete_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """删除物品记录。"""
    item = await item_crud.get_item(db, item_id)
    if item is None:
        return r.error(message="物品不存在", code=status.HTTP_404_NOT_FOUND)
    if item.user_id != current_user.id:
        return r.error(message="只有发布者可以删除物品", code=status.HTTP_403_FORBIDDEN)
    await item_crud.delete_item(db, db_obj=item)
    await db.commit()
    return r.success(data=None, message="删除成功", code=200)


@router.post(
    "/{item_id}/claim",
    response_model=SuccessResponse[ItemRead],
    summary="认领物品",
    description="登录用户对 open 状态的物品发起认领，成功后状态变为 claimed。",
)
async def claim_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    r: Responder = Depends(get_responder),
):
    """认领流程：不可认领自己的物品；仅 open 可认领。"""
    item = await item_crud.get_item(db, item_id)
    if item is None:
        return r.error(message="物品不存在", code=status.HTTP_404_NOT_FOUND)
    if item.user_id == current_user.id:
        return r.error(message="不能认领自己发布的物品", code=status.HTTP_400_BAD_REQUEST)
    if item.status != ItemStatus.open:
        return r.error(message="该物品当前不可认领", code=status.HTTP_400_BAD_REQUEST)
    claimed = await item_crud.claim_item(db, db_obj=item, claimant=current_user)
    await db.commit()
    await db.refresh(claimed)
    return r.success(data=ItemRead.model_validate(claimed), message="认领成功", code=200)
