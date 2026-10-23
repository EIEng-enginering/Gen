"""WP-005 append-only alternative family graph, with versioned revisions.

Revision ID: 20261023_002
Revises: 20261023_001
No existing source or observation data is modified by this upgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261023_002'
down_revision = '20261023_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('hypothesis_branch_revisions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('hypothesis_set_id', sa.Uuid(as_uuid=True), sa.ForeignKey('hypothesis_sets.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('option_id', sa.Uuid(as_uuid=True), sa.ForeignKey('hypothesis_options.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('option_id', 'revision_number', name='uq_branch_option_revision'),
        sa.CheckConstraint('revision_number >= 1', name='ck_branch_revision_positive'))
    op.create_index('ix_branch_revision_set', 'hypothesis_branch_revisions', ['hypothesis_set_id','option_id'])
    op.create_table('hypothesis_branch_edges',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('revision_id',sa.Uuid(as_uuid=True),sa.ForeignKey('hypothesis_branch_revisions.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('edge_key',sa.String(100),nullable=False),
        sa.Column('from_observation_id',sa.Uuid(as_uuid=True),sa.ForeignKey('observations.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('to_observation_id',sa.Uuid(as_uuid=True),sa.ForeignKey('observations.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('relationship_type',sa.String(40),nullable=False),
        sa.Column('supporting_observation_ids',sa.JSON(),nullable=False),
        sa.Column('contradicting_observation_ids',sa.JSON(),nullable=False),
        sa.Column('reasoning',sa.Text(),nullable=False),
        sa.UniqueConstraint('revision_id','edge_key',name='uq_branch_edge_key'),
        sa.CheckConstraint('from_observation_id <> to_observation_id',name='ck_branch_distinct_nodes'),
        sa.CheckConstraint("relationship_type IN ('biological_parent','adoptive_parent','step_parent','spouse','sibling','same_person','household_association')",name='ck_branch_relationship'))
    op.create_table('hypothesis_branch_reviews',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('revision_id',sa.Uuid(as_uuid=True),sa.ForeignKey('hypothesis_branch_revisions.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('decision',sa.String(30),nullable=False),
        sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('reviewer',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint("decision IN ('research_supported','rejected','deferred')",name='ck_branch_review'))
    op.create_index('ix_branch_review_revision','hypothesis_branch_reviews',['revision_id','created_at'])


def downgrade():
    """No silent loss of branch review or evidence history; throw before DDL."""
    from sqlalchemy import text
    bind = op.get_bind()
    for table in ('hypothesis_branch_reviews','hypothesis_branch_edges','hypothesis_branch_revisions'):
        if bind.scalar(text('SELECT COUNT(*) FROM '+table)):
            raise RuntimeError('Refusing destructive WP-005 downgrade: branch history exists')
    op.drop_index('ix_branch_review_revision',table_name='hypothesis_branch_reviews')
    op.drop_table('hypothesis_branch_reviews')
    op.drop_table('hypothesis_branch_edges')
    op.drop_index('ix_branch_revision_set',table_name='hypothesis_branch_revisions')
    op.drop_table('hypothesis_branch_revisions')
