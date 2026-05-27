"""remove practice fields from user

Revision ID: a1f3c9e2b847
Revises: d126a395ad92
Create Date: 2026-05-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "a1f3c9e2b847"
down_revision: Union[str, Sequence[str], None] = "d126a395ad92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user", "first_name")
    op.drop_column("user", "last_name")


def downgrade() -> None:
    op.add_column("user", sa.Column("last_name", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default=sa.text("''")))
    op.add_column("user", sa.Column("first_name", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default=sa.text("''")))
    op.alter_column("user", "first_name", server_default=None)
    op.alter_column("user", "last_name", server_default=None)
