"""add strategy runtime tables

Revision ID: b1f2c8f061b7
Revises: 5e470f33fbe2
Create Date: 2025-09-19 10:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1f2c8f061b7"
down_revision = "5e470f33fbe2"
branch_labels = None
depends_on = None


strategy_mode_enum = sa.Enum("backtest", "paper", "live", name="strategy_mode")
strategy_run_status_enum = sa.Enum(
    "queued", "running", "completed", "failed", "stopped", name="strategy_run_status"
)
strategy_log_level_enum = sa.Enum("info", "warning", "error", name="strategy_log_level")


def upgrade() -> None:
    bind = op.get_bind()
    strategy_mode_enum.create(bind, checkfirst=True)
    strategy_run_status_enum.create(bind, checkfirst=True)
    strategy_log_level_enum.create(bind, checkfirst=True)

    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_id", sa.UUID(), nullable=False),
        sa.Column("mode", strategy_mode_enum, nullable=False),
        sa.Column("status", strategy_run_status_enum, nullable=False, server_default="running"),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("result_metrics", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "strategy_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=True),
        sa.Column("level", strategy_log_level_enum, nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["strategy_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("strategy_logs")
    op.drop_table("strategy_runs")
    bind = op.get_bind()
    strategy_log_level_enum.drop(bind, checkfirst=True)
    strategy_run_status_enum.drop(bind, checkfirst=True)
    strategy_mode_enum.drop(bind, checkfirst=True)
