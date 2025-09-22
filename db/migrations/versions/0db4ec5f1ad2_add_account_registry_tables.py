"""add account registry tables

Revision ID: 0db4ec5f1ad2
Revises: 2c4c7df7ea09
Create Date: 2025-09-19 12:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0db4ec5f1ad2"
down_revision = "2c4c7df7ea09"
branch_labels = None
depends_on = None


account_policy_type_enum = sa.Enum(
    "proportional",
    "fixed",
    "weighted",
    name="lot_allocation_policy",
)

execution_mode_enum = sa.Enum(
    "sync",
    "parallel",
    "staggered",
    name="execution_mode",
)


def upgrade() -> None:
    bind = op.get_bind()
    account_policy_type_enum.create(bind, checkfirst=True)
    execution_mode_enum.create(bind, checkfirst=True)

    op.create_table(
        "execution_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mode", execution_mode_enum, nullable=False, server_default="parallel"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "execution_group_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("allocation_policy", account_policy_type_enum, nullable=False, server_default="proportional"),
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("fixed_lots", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["execution_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "account_id", name="uq_group_account"),
    )

    op.create_table(
        "execution_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("strategy_run_id", sa.UUID(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["execution_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("execution_runs")
    op.drop_table("execution_group_accounts")
    op.drop_table("execution_groups")
    bind = op.get_bind()
    execution_mode_enum.drop(bind, checkfirst=True)
    account_policy_type_enum.drop(bind, checkfirst=True)
