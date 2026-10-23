"""WP-009 provenance-linked historical places; no automatic accepted-tree edits.

Revision ID: 20261023_005
Revises: 20261023_004
"""
from alembic import op
import sqlalchemy as sa

revision = '20261023_005'
down_revision = '20261023_004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('historical_places',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('source_document_id', sa.Uuid(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('place_key', sa.String(140), nullable=False),
        sa.Column('label', sa.String(300), nullable=False),
        sa.Column('county_label', sa.String(160), nullable=False),
        sa.Column('jurisdiction_type', sa.String(50), nullable=False),
        sa.Column('valid_from_year', sa.Integer()),
        sa.Column('valid_to_year', sa.Integer()),
        sa.Column('aliases_json', sa.JSON(), nullable=False),
        sa.Column('evidence_note', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('source_document_id', 'place_key', name='uq_historical_place_source_key'),
        sa.CheckConstraint('valid_from_year IS NULL OR (valid_from_year >= 1000 AND valid_from_year <= 2100)', name='ck_historical_place_start'),
        sa.CheckConstraint('valid_to_year IS NULL OR (valid_to_year >= 1000 AND valid_to_year <= 2100)', name='ck_historical_place_end'),
        sa.CheckConstraint('valid_from_year IS NULL OR valid_to_year IS NULL OR valid_from_year <= valid_to_year', name='ck_historical_place_interval'),
    )
    op.create_index('ix_historical_place_county', 'historical_places', ['county_label', 'label'])


def downgrade():
    from sqlalchemy import text
    if op.get_bind().scalar(text('SELECT COUNT(*) FROM historical_places')):
        raise RuntimeError('Refusing destructive WP-009 downgrade; historical place evidence exists')
    op.drop_index('ix_historical_place_county', table_name='historical_places')
    op.drop_table('historical_places')
