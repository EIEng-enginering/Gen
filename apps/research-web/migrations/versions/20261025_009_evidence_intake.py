"""WP026 quarantine and human review records. Never touches Gramps."""
from alembic import op
import sqlalchemy as sa
revision='20261025_009'
down_revision='20261024_008'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('acquisition_batches',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('batch_key',sa.String(120),nullable=False,unique=True),
        sa.Column('input_kind',sa.String(30),nullable=False),
        sa.Column('created_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('rights_attested',sa.Integer(),nullable=False),
        sa.Column('row_count',sa.Integer(),nullable=False,server_default='0'),
        sa.CheckConstraint('row_count >= 0'))
    op.create_table('staged_evidence',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('batch_id',sa.Uuid(as_uuid=True),sa.ForeignKey('acquisition_batches.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('row_number',sa.Integer(),nullable=False),
        sa.Column('sha256',sa.String(64),nullable=False),
        sa.Column('payload',sa.JSON(),nullable=False),
        sa.Column('surname_key',sa.String(160),nullable=False,server_default=''),
        sa.Column('place_key',sa.String(200),nullable=False,server_default=''),
        sa.Column('year_hint',sa.Integer()),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('import_document_id',sa.Uuid(as_uuid=True),sa.ForeignKey('source_documents.id',ondelete='RESTRICT')),
        sa.Column('import_observation_id',sa.Uuid(as_uuid=True),sa.ForeignKey('observations.id',ondelete='RESTRICT')),
        sa.Column('reviewed_by',sa.String(120)),
        sa.Column('reviewed_at',sa.DateTime(timezone=True)),
        sa.UniqueConstraint('batch_id','row_number'))
    op.create_index('ix_staged_evidence_batch','staged_evidence',['batch_id','status'])
    op.create_index('ix_staged_evidence_surname_year','staged_evidence',['surname_key','year_hint'])
    op.create_table('staged_person_links',
        sa.Column('id',sa.Uuid(as_uuid=True),primary_key=True),
        sa.Column('staged_id',sa.Uuid(as_uuid=True),sa.ForeignKey('staged_evidence.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('gramps_handle',sa.String(100),nullable=False),
        sa.Column('rationale',sa.Text(),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('created_by',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_staged_link_staged','staged_person_links',['staged_id'])

def downgrade():
    from sqlalchemy import text
    bind=op.get_bind()
    for table in ('staged_person_links','staged_evidence','acquisition_batches'):
        if bind.scalar(text('SELECT COUNT(*) FROM '+table)):
            raise RuntimeError('Refusing downgrade: evidence intake/review history exists')
    op.drop_index('ix_staged_link_staged',table_name='staged_person_links')
    op.drop_table('staged_person_links')
    op.drop_index('ix_staged_evidence_surname_year',table_name='staged_evidence')
    op.drop_index('ix_staged_evidence_batch',table_name='staged_evidence')
    op.drop_table('staged_evidence')
    op.drop_table('acquisition_batches')
