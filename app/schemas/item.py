"""物品相关 Schema。"""

from datetime import date, datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """物品公共字段。"""

    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(default="", description="详细描述")
    item_type: Literal["lost", "found"] = Field(..., description="lost | found")
    location: str = Field(default="", max_length=255, description="地点/位置描述")
    event_date: date = Field(..., description="丢失或拾到日期")
    category: str = Field(
        ...,
        description="分类：id_document 证件, electronics 电子产品, clothing 衣物, keys 钥匙, backpack 背包, other 其他",
    )
    image_url: str | None = Field(default=None, max_length=512, description="图片 URL，可选")


class ItemCreate(ItemBase):
    """创建物品请求体。"""


class ItemUpdate(BaseModel):
    """更新物品：均为可选字段。"""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None)
    item_type: Literal["lost", "found"] | None = None
    location: str | None = Field(default=None, max_length=255)
    event_date: date | None = None
    category: Literal["id_document", "electronics", "clothing", "keys", "backpack", "other"] | None = None
    status: Literal["open", "claimed", "resolved"] | None = Field(
        default=None,
        description="发布者可将其更新为 resolved；其他状态由业务接口维护",
    )
    image_url: str | None = Field(default=None, max_length=512)


class ItemRead(ItemBase):
    """物品详情响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    user_id: int = Field(..., description="发布者用户 ID")
    claimant_id: int | None = Field(default=None, description="认领人用户 ID")
    created_at: datetime


class ItemListFilters(BaseModel):
    """列表查询筛选参数（由依赖或路由组装）。"""

    item_type: str | None = None
    category: str | None = None
    location: str | None = None
    event_date_from: date | None = None
    event_date_to: date | None = None
    keyword: str | None = None
    sort_by: str = Field(default="newest", description="排序：newest/oldest/event_date")
    near: str | None = Field(default=None, description="可选：用于简易距离排序的地点关键字")


class MyItemsListData(BaseModel):
    """我的发布列表数据（items + total）。"""

    items: list[ItemRead] = Field(default_factory=list, description="我的发布列表")
    total: int = Field(..., ge=0, description="总数")


class ClaimedItemsListData(BaseModel):
    """我认领的物品列表数据（items + total）。"""

    items: list[ItemRead] = Field(default_factory=list, description="我认领的物品列表")
    total: int = Field(..., ge=0, description="总数")
