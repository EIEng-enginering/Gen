"""Add materialized search index; does not change source or accepted Gramps data."""
from alembic import op
import sqlalchemy as sa
revision='20261025_010'
down_revision='20261025_009'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('general_search_mentions',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('source_kind',sa.String(20),nullable=False),
        sa.Column('source_id',sa.String(40),nullable=False),
        sa.Column('name_literal',sa.String(300),nullable=False),
        sa.Column('surname_literal',sa.String(160),nullable=False),
        sa.Column('surname_key',sa.String(160),nullable=False),
        sa.Column('surname_soundex',sa.String(4),nullable=False),
        sa.Column('given_literal',sa.String(160),nullable=False),
        sa.Column('given_key',sa.String(160),nullable=False),
        sa.Column('place_literal',sa.String(300),nullable=False),
        sa.Column('place_key',sa.String(200),nullable=False),
        sa.Column('county_key',sa.String(100),nullable=False),
        sa.Column('event_type',sa.String(60),nullable=False),
        sa.Column('year_hint',sa.Integer()),sa.Column('year_end_hint',sa.Integer()),
        sa.Column('provider',sa.String(120),nullable=False),
        sa.Column('source_reference',sa.String(500),nullable=False),
        sa.Column('source_document_id',sa.String(40),nullable=False),
        sa.Column('possible_original',sa.String(250),nullable=False),
        sa.Column('rights_label',sa.String(200),nullable=False),
        sa.Column('status',sa.String(40),nullable=False),
        sa.UniqueConstraint('source_kind','source_id',name='uq_general_search_source'),
        sa.CheckConstraint("source_kind IN ('observed','staged')"))
    op.create_index('ix_general_search_surname_year','general_search_mentions',['surname_key','year_hint','id'])
    op.create_index('ix_general_search_soundex_year','general_search_mentions',['surname_soundex','year_hint'])
    op.create_index('ix_general_search_county_year','general_search_mentions',['county_key','year_hint'])
    op.create_index('ix_general_search_status','general_search_mentions',['status','id'])

def downgrade():
    # This table is derivative, but require explicit review before rollback.
    conn=op.get_bind()
    if conn.scalar(sa.text('SELECT COUNT(*) FROM general_search_mentions')):
        raise RuntimeError('Refusing populated search-index downgrade; explicit purge/rebuild approval required')
    for idx in ['ix_general_search_status','ix_general_search_county_year',
                'ix_general_search_soundex_year','ix_general_search_surname_year']:
        op.drop_index(idx,table_name='general_search_mentions')
    op.drop_table('general_search_mentions')
