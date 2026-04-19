"""物品相关 Schema。"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class ItemTypeSchema(str, Enum):
    """API 层物品类型枚举。"""

    lost = "lost"
    found = "found"


class ItemCategorySchema(str, Enum):
    """API 层分类枚举（值与 ORM 一致，描述见 Field）。"""

    id_document = "id_document"
    electronics = "electronics"
    clothing = "clothing"
    keys = "keys"
    backpack = "backpack"
    other = "other"


class ItemStatusSchema(str, Enum):
    """API 层状态枚举。"""

    open = "open"
    claimed = "claimed"
    resolved = "resolved"


class ItemBase(BaseModel):
    """物品公共字段。"""

    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(default="", description="详细描述")
    item_type: ItemTypeSchema = Field(..., description="lost=丢失, found=拾获")
    location: str = Field(default="", max_length=255, description="地点/位置描述")
    event_date: date = Field(..., description="丢失或拾到日期")
    category: ItemCategorySchema = Field(
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
    item_type: ItemTypeSchema | None = None
    location: str | None = Field(default=None, max_length=255)
    event_date: date | None = None
    category: ItemCategorySchema | None = None
    status: ItemStatusSchema | None = Field(
        default=None,
        description="发布者可将其更新为 resolved；其他状态由业务接口维护",
    )
    image_url: str | None = Field(default=None, max_length=512)


class ItemRead(ItemBase):
    """物品详情响应。"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    status: ItemStatusSchema
    user_id: int = Field(..., description="发布者用户 ID")
    claimant_id: int | None = Field(default=None, description="认领人用户 ID")
    created_at: datetime


class ItemListFilters(BaseModel):
    """列表查询筛选参数（由依赖或路由组装）。"""

    item_type: ItemTypeSchema | None = None
    category: ItemCategorySchema | None = None
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
