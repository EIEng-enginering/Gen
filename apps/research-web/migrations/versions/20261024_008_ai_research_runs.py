"""Local AI research history; revision 20261024_008 after 20261023_007."""
from alembic import op
import sqlalchemy as sa
revision='20261024_008'
down_revision='20261023_007'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('ai_research_runs',
      sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
      sa.Column('created_by',sa.String(120),nullable=False),
      sa.Column('question',sa.Text(),nullable=False),
      sa.Column('mode',sa.String(20),nullable=False),
      sa.Column('surname',sa.String(160),nullable=False),
      sa.Column('county',sa.String(160),nullable=False),
      sa.Column('scope_json',sa.JSON(),nullable=False),
      sa.Column('answer_json',sa.JSON(),nullable=False),
      sa.Column('execution_status',sa.String(50),nullable=False),
      sa.Column('model_name',sa.String(120)),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
      sa.CheckConstraint("mode IN ('guided','conventional','autonomous')",name='ck_ai_run_mode'))
    op.create_index('ix_ai_runs_created','ai_research_runs',['created_at'])

def downgrade():
    from sqlalchemy import text
    if op.get_bind().scalar(text('SELECT COUNT(*) FROM ai_research_runs')):
        raise RuntimeError('Refusing destructive downgrade: AI research history exists')
    op.drop_index('ix_ai_runs_created',table_name='ai_research_runs')
    op.drop_table('ai_research_runs')
