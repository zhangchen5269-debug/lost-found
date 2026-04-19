"""初始表结构：users、items

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260412_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


item_type_enum = sa.Enum("lost", "found", name="itemtype", native_enum=False)
item_category_enum = sa.Enum(
    "id_document",
    "electronics",
    "clothing",
    "keys",
    "backpack",
    "other",
    name="itemcategory",
    native_enum=False,
)
item_status_enum = sa.Enum("open", "claimed", "resolved", name="itemstatus", native_enum=False)


def upgrade() -> None:
    bind = op.get_bind()
    item_type_enum.create(bind, checkfirst=True)
    item_category_enum.create(bind, checkfirst=True)
    item_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("item_type", item_type_enum, nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("category", item_category_enum, nullable=False),
        sa.Column(
            "status",
            item_status_enum,
            nullable=False,
            server_default=sa.text("'open'"),
        ),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("claimant_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["claimant_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_id"), "items", ["id"], unique=False)
    op.create_index(op.f("ix_items_title"), "items", ["title"], unique=False)
    op.create_index(op.f("ix_items_item_type"), "items", ["item_type"], unique=False)
    op.create_index(op.f("ix_items_event_date"), "items", ["event_date"], unique=False)
    op.create_index(op.f("ix_items_category"), "items", ["category"], unique=False)
    op.create_index(op.f("ix_items_status"), "items", ["status"], unique=False)
    op.create_index(op.f("ix_items_claimant_id"), "items", ["claimant_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index(op.f("ix_items_claimant_id"), table_name="items")
    op.drop_index(op.f("ix_items_status"), table_name="items")
    op.drop_index(op.f("ix_items_category"), table_name="items")
    op.drop_index(op.f("ix_items_event_date"), table_name="items")
    op.drop_index(op.f("ix_items_item_type"), table_name="items")
    op.drop_index(op.f("ix_items_title"), table_name="items")
    op.drop_index(op.f("ix_items_id"), table_name="items")
    op.drop_table("items")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    item_status_enum.drop(bind, checkfirst=True)
    item_category_enum.drop(bind, checkfirst=True)
    item_type_enum.drop(bind, checkfirst=True)
