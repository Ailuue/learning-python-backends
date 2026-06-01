"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-01
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "urls",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("short_code", sa.String(10), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("click_count", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("short_code", name="uq_urls_short_code"),
    )
    # Partial index: only active rows — redirect hot path hits this, not the full unique index
    op.create_index(
        "idx_urls_active_short_code",
        "urls",
        ["short_code"],
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("idx_urls_active_short_code", table_name="urls")
    op.drop_table("urls")
