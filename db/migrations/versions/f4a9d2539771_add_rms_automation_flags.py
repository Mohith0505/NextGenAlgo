"""add rms automation flags

Revision ID: f4a9d2539771
Revises: c2f1d0b4a123
Create Date: 2025-09-22 11:47:39
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4a9d2539771"
down_revision = "c2f1d0b4a123"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rms_rules", sa.Column("drawdown_limit", sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column(
        "rms_rules",
        sa.Column(
            "auto_square_off_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "rms_rules",
        sa.Column("auto_square_off_buffer_pct", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "rms_rules",
        sa.Column(
            "auto_hedge_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "rms_rules",
        sa.Column("auto_hedge_ratio", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "rms_rules",
        sa.Column(
            "notify_email",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "rms_rules",
        sa.Column(
            "notify_telegram",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("rms_rules", "notify_telegram")
    op.drop_column("rms_rules", "notify_email")
    op.drop_column("rms_rules", "auto_hedge_ratio")
    op.drop_column("rms_rules", "auto_hedge_enabled")
    op.drop_column("rms_rules", "auto_square_off_buffer_pct")
    op.drop_column("rms_rules", "auto_square_off_enabled")
    op.drop_column("rms_rules", "drawdown_limit")
