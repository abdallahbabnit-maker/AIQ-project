"""assets table

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), default="ready", index=True),
        sa.Column("meta", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("assets")
