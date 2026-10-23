"""WP-006 immutable Gramps previews and human decision audit.

Revision ID: 20261023_003
Revises: 20261023_002
"""
from alembic import op
import sqlalchemy as sa

revision = '20261023_003'
down_revision = '20261023_002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('gramps_change_plans',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('idempotency_key', sa.String(128), nullable=False, unique=True),
        sa.Column('hypothesis_set_id', sa.Uuid(as_uuid=True), sa.ForeignKey('hypothesis_sets.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('option_id', sa.Uuid(as_uuid=True), sa.ForeignKey('hypothesis_options.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_revision_id', sa.Uuid(as_uuid=True), sa.ForeignKey('hypothesis_branch_revisions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('set_version_after_creation', sa.Integer(), nullable=False),
        sa.Column('digest_sha256', sa.String(64), nullable=False),
        sa.Column('preview_json', sa.JSON(), nullable=False),
        sa.Column('operator_note', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('set_version_after_creation >= 1', name='ck_gramps_plan_set_version'))
    op.create_index('ix_gramps_plan_set', 'gramps_change_plans', ['hypothesis_set_id','created_at'])
    op.create_table('gramps_plan_decisions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('plan_id', sa.Uuid(as_uuid=True), sa.ForeignKey('gramps_change_plans.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('decision', sa.String(45), nullable=False),
        sa.Column('reviewer', sa.String(120), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('approve_for_future_validation','reject')", name='ck_gramps_plan_decision'))


def downgrade():
    from sqlalchemy import text
    bind=op.get_bind()
    for table in ('gramps_plan_decisions','gramps_change_plans'):
        if bind.scalar(text('SELECT COUNT(*) FROM '+table)):
            raise RuntimeError('Refusing destructive WP-006 downgrade: human approval history exists')
    op.drop_table('gramps_plan_decisions')
    op.drop_index('ix_gramps_plan_set',table_name='gramps_change_plans')
    op.drop_table('gramps_change_plans')
