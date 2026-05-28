"""rename hashed_password to password_hash

Revision ID: 1503cb4cee63
Revises: 259e700a3fc8
Create Date: 2026-05-17 19:44:57.563878

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1503cb4cee63"
down_revision: Union[str, Sequence[str], None] = "259e700a3fc8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("user", "hashed_password", new_column_name="password_hash")


def downgrade() -> None:
    op.alter_column("user", "password_hash", new_column_name="hashed_password")
