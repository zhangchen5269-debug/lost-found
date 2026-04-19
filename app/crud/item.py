"""物品 CRUD 与查询。"""

from datetime import date

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item, ItemCategory, ItemStatus, ItemType
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate


async def create_item(db: AsyncSession, *, obj_in: ItemCreate, owner_id: int) -> Item:
    """创建物品。"""
    item = Item(
        title=obj_in.title,
        description=obj_in.description,
        item_type=ItemType(obj_in.item_type.value),
        location=obj_in.location,
        event_date=obj_in.event_date,
        category=ItemCategory(obj_in.category.value),
        status=ItemStatus.open,
        image_url=obj_in.image_url,
        user_id=owner_id,
    )
    db.add(item)
    await db.flush()
    return item


async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    """按主键获取物品。"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


def _apply_filters(
    stmt: Select[tuple[Item]],
    *,
    item_type: ItemType | None,
    category: ItemCategory | None,
    location: str | None,
    event_date_from: date | None,
    event_date_to: date | None,
    keyword: str | None,
) -> Select[tuple[Item]]:
    """为列表查询附加筛选条件。"""
    if item_type is not None:
        stmt = stmt.where(Item.item_type == item_type)
    if category is not None:
        stmt = stmt.where(Item.category == category)
    if location:
        stmt = stmt.where(Item.location.ilike(f"%{location}%"))
    if event_date_from is not None:
        stmt = stmt.where(Item.event_date >= event_date_from)
    if event_date_to is not None:
        stmt = stmt.where(Item.event_date <= event_date_to)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Item.title.ilike(pattern),
                Item.description.ilike(pattern),
                Item.location.ilike(pattern),
            )
        )
    return stmt


async def list_items(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
    item_type: ItemType | None = None,
    category: ItemCategory | None = None,
    location: str | None = None,
    event_date_from: date | None = None,
    event_date_to: date | None = None,
    keyword: str | None = None,
    sort_by: str = "newest",
    near: str | None = None,
) -> tuple[list[Item], int]:
    """分页列出物品，返回 (列表, 总数)。"""
    base = select(Item)
    filtered = _apply_filters(
        base,
        item_type=item_type,
        category=category,
        location=location,
        event_date_from=event_date_from,
        event_date_to=event_date_to,
        keyword=keyword,
    )
    subq = filtered.subquery()
    count_stmt = select(func.count()).select_from(subq)
    total = int((await db.execute(count_stmt)).scalar_one())

    # 排序策略：
    # - newest: created_at desc, event_date desc
    # - oldest: created_at asc, event_date asc
    # - event_date: event_date desc, created_at desc
    # - near(可选): 使用字符串匹配的“简易距离排序”（后续可替换为 PostGIS/向量检索等）
    stmt = filtered
    if near:
        # instr 越小越“近”（0 表示不包含，排到后面）
        near_lower = func.lower(near)
        loc_lower = func.lower(Item.location)
        pos = func.instr(loc_lower, near_lower)
        stmt = stmt.order_by(pos.asc(), Item.created_at.desc())
    else:
        if sort_by == "oldest":
            stmt = stmt.order_by(Item.created_at.asc(), Item.event_date.asc())
        elif sort_by == "event_date":
            stmt = stmt.order_by(Item.event_date.desc(), Item.created_at.desc())
        else:
            stmt = stmt.order_by(Item.created_at.desc(), Item.event_date.desc())

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def get_user_items(
    db: AsyncSession,
    *,
    user_id: int,
    skip: int,
    limit: int,
) -> tuple[list[Item], int]:
    """分页获取“我的发布”列表，返回 (列表, 总数)。"""
    base = select(Item).where(Item.user_id == user_id)
    subq = base.subquery()
    total = int((await db.execute(select(func.count()).select_from(subq))).scalar_one())
    stmt = base.order_by(Item.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def get_user_claimed_items(
    db: AsyncSession,
    *,
    claimant_id: int,
    skip: int,
    limit: int,
) -> tuple[list[Item], int]:
    """分页获取“我认领的物品”列表，返回 (列表, 总数)。"""
    base = select(Item).where(Item.claimant_id == claimant_id)
    subq = base.subquery()
    total = int((await db.execute(select(func.count()).select_from(subq))).scalar_one())
    stmt = base.order_by(Item.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def update_item(db: AsyncSession, *, db_obj: Item, obj_in: ItemUpdate) -> Item:
    """按字段更新物品。"""
    data = obj_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is None:
            continue
        if field == "item_type":
            setattr(db_obj, field, ItemType(str(value)))
        elif field == "category":
            setattr(db_obj, field, ItemCategory(str(value)))
        elif field == "status":
            setattr(db_obj, field, ItemStatus(str(value)))
        else:
            setattr(db_obj, field, value)
    await db.flush()
    return db_obj


async def delete_item(db: AsyncSession, *, db_obj: Item) -> None:
    """删除物品。"""
    db.delete(db_obj)
    await db.flush()


async def claim_item(db: AsyncSession, *, db_obj: Item, claimant: User) -> Item:
    """认领：将状态改为 claimed 并记录认领人。"""
    db_obj.status = ItemStatus.claimed
    db_obj.claimant_id = claimant.id
    await db.flush()
    return db_obj
