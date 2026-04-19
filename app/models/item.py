"""失物招领物品 ORM 模型。"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ItemType(str, enum.Enum):
    """物品类型：丢失或拾获。"""

    lost = "lost"
    found = "found"


class ItemCategory(str, enum.Enum):
    """物品分类。"""

    id_document = "id_document"  # 证件
    electronics = "electronics"  # 电子产品
    clothing = "clothing"  # 衣物
    keys = "keys"  # 钥匙
    backpack = "backpack"  # 背包
    other = "other"  # 其他


class ItemStatus(str, enum.Enum):
    """处理状态。"""

    open = "open"
    claimed = "claimed"
    resolved = "resolved"


class Item(Base):
    """失物或招领条目。"""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[ItemCategory] = mapped_column(Enum(ItemCategory), nullable=False, index=True)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus),
        nullable=False,
        default=ItemStatus.open,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    claimant_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="items", foreign_keys=[user_id])
    claimant: Mapped["User | None"] = relationship(
        "User",
        back_populates="claims",
        foreign_keys=[claimant_id],
    )
