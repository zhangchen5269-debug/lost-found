"""merge heads

Revision ID: 0078b9060afd
Revises: 1c4ca54554fd, 20260424_0002
Create Date: 2026-04-25 11:18:21.878561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0078b9060afd'
down_revision: Union[str, Sequence[str], None] = ('1c4ca54554fd', '20260424_0002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
