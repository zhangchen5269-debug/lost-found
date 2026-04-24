"""将 items.item_type 从 ENUM 改为 VARCHAR

Revision ID: 20260424_0002
Revises: 20260412_0001
Create Date: 2026-04-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260424_0002"
down_revision: Union[str, Sequence[str], None] = "20260412_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE items ALTER COLUMN item_type TYPE VARCHAR(16) USING item_type::text"
    )
    op.alter_column(
        "items",
        "item_type",
        existing_type=sa.Enum("lost", "found", name="itemtype", native_enum=False),
        type_=sa.String(length=16),
        existing_nullable=False,
    )


def downgrade() -> None:
    item_type_enum = sa.Enum("lost", "found", name="itemtype", native_enum=False)
    bind = op.get_bind()
    item_type_enum.create(bind, checkfirst=True)
    op.execute(
        "ALTER TABLE items ALTER COLUMN item_type TYPE itemtype USING item_type::text::itemtype"
    )
    op.alter_column(
        "items",
        "item_type",
        existing_type=sa.String(length=16),
        type_=item_type_enum,
        existing_nullable=False,
    )
