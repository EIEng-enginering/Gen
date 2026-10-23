"""WP-007 append-only read-only validation audit.

Revision ID: 20261023_004
Revises: 20261023_003
"""
from alembic import op
import sqlalchemy as sa

revision = '20261023_004'
down_revision = '20261023_003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('gramps_read_validations',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('plan_id', sa.Uuid(as_uuid=True), sa.ForeignKey('gramps_change_plans.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('plan_digest', sa.String(64), nullable=False),
        sa.Column('checked_by', sa.String(120), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_gramps_read_plan_time', 'gramps_read_validations', ['plan_id','created_at'])


def downgrade():
    from sqlalchemy import text
    bind=op.get_bind()
    if bind.scalar(text('SELECT COUNT(*) FROM gramps_read_validations')):
        raise RuntimeError('Refusing destructive WP-007 downgrade with recorded Gramps read validations')
    op.drop_index('ix_gramps_read_plan_time', table_name='gramps_read_validations')
    op.drop_table('gramps_read_validations')
