"""分页参数解析。"""

from dataclasses import dataclass


@dataclass(slots=True)
class PageParams:
    """分页查询参数。"""

    page: int
    page_size: int
    skip: int
    limit: int


def resolve_pagination(
    page: int = 1,
    page_size: int = 20,
    *,
    max_page_size: int = 100,
) -> PageParams:
    """
    将页码与每页数量转换为 skip/limit。

    :param page: 页码，从 1 开始。
    :param page_size: 每页条数。
    :param max_page_size: 每页最大条数上限。
    """
    safe_page = max(page, 1)
    safe_size = min(max(page_size, 1), max_page_size)
    skip = (safe_page - 1) * safe_size
    return PageParams(page=safe_page, page_size=safe_size, skip=skip, limit=safe_size)
