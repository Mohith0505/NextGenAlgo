"""add scheduler jobs table

Revision ID: c2f1d0b4a123
Revises: b1f2c8f061b7
Create Date: 2025-09-20 08:38:51
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2f1d0b4a123"
down_revision = "b1f2c8f061b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'scheduler_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('strategy_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('cron_expression', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduler_jobs_user_id'), 'scheduler_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_scheduler_jobs_strategy_id'), 'scheduler_jobs', ['strategy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduler_jobs_strategy_id'), table_name='scheduler_jobs')
    op.drop_index(op.f('ix_scheduler_jobs_user_id'), table_name='scheduler_jobs')
    op.drop_table('scheduler_jobs')
