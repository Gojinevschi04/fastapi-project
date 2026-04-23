"""add deferred to task status enum

Revision ID: 8d89c7173bff
Revises: 706b6921ee97
Create Date: 2026-04-23 10:38:47.418269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8d89c7173bff'
down_revision: Union[str, Sequence[str], None] = '706b6921ee97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres stores the enum with uppercase NAMES (PENDING, COMPLETED, ...),
    # see earlier widen migration. Add the new DEFERRED value.
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'DEFERRED'")


def downgrade() -> None:
    # Postgres does NOT support removing a single value from an enum type.
    # A downgrade requires recreating the enum without DEFERRED and re-mapping
    # column usages — out of scope for this migration. Deliberate no-op.
    pass
