"""WP-011 supervised task queue; no external execution or provider credentials.

Revision ID: 20261023_007
Revises: 20261023_006
"""
from alembic import op
import sqlalchemy as sa
revision='20261023_007'
down_revision='20261023_006'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('research_tasks',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('job_id',sa.Uuid(as_uuid=True),sa.ForeignKey('research_jobs.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('task_key',sa.String(160),nullable=False),
        sa.Column('kind',sa.String(40),nullable=False),
        sa.Column('source_provider',sa.String(120),nullable=False),
        sa.Column('input_json',sa.JSON(),nullable=False),
        sa.Column('status',sa.String(25),nullable=False),
        sa.Column('reserved_cost_cents',sa.Integer(),nullable=False),
        sa.Column('spent_cost_cents',sa.Integer(),nullable=False),
        sa.Column('lease_owner',sa.String(120)),
        sa.Column('lease_token_sha256',sa.String(64)),
        sa.Column('lease_expires_at',sa.DateTime(timezone=True)),
        sa.Column('attempt',sa.Integer(),nullable=False),
        sa.Column('completed_key',sa.String(160)),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('job_id','task_key',name='uq_task_job_key'),
        sa.CheckConstraint("kind IN ('local_review','manual_lookup','approved_api_request')",name='ck_task_kind'),
        sa.CheckConstraint("status IN ('queued','leased','paused','complete','failed','cancelled')",name='ck_task_status'),
        sa.CheckConstraint('reserved_cost_cents >= 0 AND spent_cost_cents >= 0',name='ck_task_money'),
        sa.CheckConstraint('attempt >= 0',name='ck_task_attempt'))
    op.create_index('ix_task_job_status','research_tasks',['job_id','status'])
    op.create_table('source_provider_policies',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('provider',sa.String(120),nullable=False,unique=True),
        sa.Column('access_mode',sa.String(35),nullable=False),
        sa.Column('permission_reference',sa.String(500),nullable=False),
        sa.Column('requests_per_day',sa.Integer(),nullable=False),
        sa.Column('cooldown_seconds',sa.Integer(),nullable=False),
        sa.Column('daily_budget_cents',sa.Integer(),nullable=False),
        sa.Column('created_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint("access_mode IN ('manual_only','approved_api','licensed_local_dataset')",name='ck_provider_access_mode'),
        sa.CheckConstraint('requests_per_day >= 0 AND cooldown_seconds >= 0 AND daily_budget_cents >= 0',name='ck_provider_policy_limits'))


def downgrade():
    from sqlalchemy import text
    if (op.get_bind().scalar(text('SELECT COUNT(*) FROM research_tasks')) or
        op.get_bind().scalar(text('SELECT COUNT(*) FROM source_provider_policies'))):
        raise RuntimeError('Refusing destructive WP-011 downgrade: research tasks or provider policies exist')
    op.drop_table('source_provider_policies')
    op.drop_index('ix_task_job_status',table_name='research_tasks')
    op.drop_table('research_tasks')
