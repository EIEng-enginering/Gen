"""WP-010 attested original-source families; no loss or merging of source rows.

Revision ID: 20261023_006
Revises: 20261023_005
"""
from alembic import op
import sqlalchemy as sa
revision='20261023_006'
down_revision='20261023_005'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('original_source_families',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('family_key',sa.String(180),nullable=False,unique=True),
        sa.Column('description',sa.String(500),nullable=False),
        sa.Column('rationale',sa.Text(),nullable=False),
        sa.Column('created_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('original_source_members',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('family_id',sa.Uuid(as_uuid=True),sa.ForeignKey('original_source_families.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('document_id',sa.Uuid(as_uuid=True),sa.ForeignKey('source_documents.id',ondelete='RESTRICT'),nullable=False,unique=True),
        sa.Column('justification',sa.Text(),nullable=False),
        sa.Column('created_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_source_members_family','original_source_members',['family_id'])
    op.create_table('source_cache_receipts',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('source_document_id',sa.Uuid(as_uuid=True),sa.ForeignKey('source_documents.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('cache_key',sa.String(250),nullable=False,unique=True),
        sa.Column('checksum_sha256',sa.String(64)),
        sa.Column('rights_basis',sa.String(200),nullable=False),
        sa.Column('acquisition_method',sa.String(30),nullable=False),
        sa.Column('expires_at',sa.DateTime(timezone=True)),
        sa.Column('stored_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint("acquisition_method IN ('user_import','approved_api','licensed_dataset')",name='ck_cache_receipt_method'))


def downgrade():
    from sqlalchemy import text
    bind=op.get_bind()
    if (bind.scalar(text('SELECT COUNT(*) FROM original_source_members')) or
        bind.scalar(text('SELECT COUNT(*) FROM original_source_families')) or
        bind.scalar(text('SELECT COUNT(*) FROM source_cache_receipts'))):
        raise RuntimeError('Refusing destructive WP-010 downgrade: source-family evidence exists')
    op.drop_table('source_cache_receipts')
    op.drop_index('ix_source_members_family',table_name='original_source_members')
    op.drop_table('original_source_members')
    op.drop_table('original_source_families')
