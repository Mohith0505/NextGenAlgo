"""expand rms rules with operational limits

Revision ID: 2c4c7df7ea09
Revises: b1f2c8f061b7
Create Date: 2025-09-19 11:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2c4c7df7ea09"
down_revision = "b1f2c8f061b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rms_rules", sa.Column("max_daily_loss", sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column("rms_rules", sa.Column("max_daily_lots", sa.Integer(), nullable=True))
    op.add_column("rms_rules", sa.Column("exposure_limit", sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column("rms_rules", sa.Column("margin_buffer_pct", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column(
        "rms_rules",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("rms_rules", "updated_at")
    op.drop_column("rms_rules", "margin_buffer_pct")
    op.drop_column("rms_rules", "exposure_limit")
    op.drop_column("rms_rules", "max_daily_lots")
    op.drop_column("rms_rules", "max_daily_loss")
