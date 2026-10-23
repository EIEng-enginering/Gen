"""Initial provisional research schema, frozen at WP-002/Rev-B candidate.

NEVER update these frozen table definitions after publication. Use a new
revision for all later DDL. Downgrade refuses to destroy populated tables.
"""
import os
from alembic import op
from sqlalchemy import select, func

revision='20261023_001'
down_revision=None
branch_labels=None
depends_on=None

# FROZEN SCHEMA SNAPSHOT (independent of the live ORM models):
"""24 Gen research data model (WP-002). Only accepted Gramps records live in Gramps.

All entities here are provisional or source observations; we deliberately do not
store a writable Gramps accepted-person table. Historical literals are retained.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer,
    JSON, String, Text, UniqueConstraint, Uuid,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def uuid():
    return uuid4()


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SourceDocument(Base):
    __tablename__ = 'source_documents'
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid)
    provider = Column(String(120), nullable=False)
    provider_record_id = Column(String(250), nullable=False)
    title = Column(String(300), nullable=False)
    reference = Column(String(500), nullable=False)
    original_url = Column(Text)
    access_method = Column(String(30), nullable=False)
    licence = Column(String(200), nullable=False)
    rights_note = Column(Text, nullable=False, default='')
    acquisition_operator = Column(String(120), nullable=False)
    acquired_at = Column(DateTime(timezone=True), default=now, nullable=False)
    checksum_sha256 = Column(String(64))
    origin_group = Column(String(250), nullable=False)
    document_kind = Column(String(40), nullable=False, default='undetermined')
    source_class = Column(String(30), nullable=False, default='undetermined')
    metadata_json = Column(JSON, nullable=False, default=dict)
    __table_args__ = (
        UniqueConstraint('provider','provider_record_id',name='uq_provider_record'),
        CheckConstraint("access_method IN ('manual','user_import','approved_api','licensed_dataset')",name='ck_access_method'),
    )


class Observation(Base):
    __tablename__ = 'observations'
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid)
    document_id = Column(Uuid(as_uuid=True), ForeignKey('source_documents.id',ondelete='RESTRICT'), nullable=False)
    observation_key = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    person_name_verbatim = Column(String(300), nullable=False)
    surname_verbatim = Column(String(160), nullable=False, default='')
    given_names_verbatim = Column(String(160), nullable=False, default='')
    event_date_verbatim = Column(String(150), nullable=False, default='')
    earliest_iso = Column(String(10))
    latest_iso = Column(String(10))
    location_verbatim = Column(String(300), nullable=False, default='')
    historical_place_ref = Column(String(140))
    occupation_verbatim = Column(String(200), nullable=False, default='')
    transcription_verbatim = Column(Text, nullable=False, default='')
    additional_json = Column(JSON, nullable=False, default=dict)
    captured_at = Column(DateTime(timezone=True), default=now, nullable=False)
    document = relationship('SourceDocument')
    __table_args__ = (
        UniqueConstraint('document_id','observation_key',name='uq_observation_key'),
        Index('ix_observation_surname_date','surname_verbatim','earliest_iso'),
    )


class TranscriptionRevision(Base):
    __tablename__ = 'transcription_revisions'
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid)
    observation_id = Column(Uuid(as_uuid=True),ForeignKey('observations.id',ondelete='RESTRICT'),nullable=False)
    supersedes_id = Column(Uuid(as_uuid=True),ForeignKey('transcription_revisions.id'))
    text = Column(Text,nullable=False)
    editor = Column(String(120),nullable=False)
    reason = Column(String(500),nullable=False)
    model_id = Column(String(150))
    created_at = Column(DateTime(timezone=True),default=now,nullable=False)
    __table_args__ = (Index('ix_transcription_obs_time','observation_id','created_at'),)


class IdentityCandidate(Base):
    """Unaccepted candidate link between observations. Not a calibrated probability."""
    __tablename__ = 'identity_candidates'
    id = Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    observation_a_id = Column(Uuid(as_uuid=True),ForeignKey('observations.id',ondelete='RESTRICT'),nullable=False)
    observation_b_id = Column(Uuid(as_uuid=True),ForeignKey('observations.id',ondelete='RESTRICT'),nullable=False)
    status = Column(String(30),nullable=False,default='proposed')
    ranking_score = Column(Float,nullable=False)
    calibrated_probability = Column(Float)
    calibration_model = Column(String(150))
    algorithm = Column(String(120),nullable=False)
    features_json = Column(JSON,nullable=False,default=dict)
    explanation = Column(Text,nullable=False,default='')
    created_at = Column(DateTime(timezone=True),default=now,nullable=False)
    updated_at = Column(DateTime(timezone=True),default=now,nullable=False)
    __table_args__ = (
        UniqueConstraint('observation_a_id','observation_b_id',name='uq_candidate_pair'),
        CheckConstraint('ranking_score >= 0 AND ranking_score <= 1', name='ck_ranking_score'),
        CheckConstraint('calibrated_probability IS NULL OR (calibrated_probability >= 0 AND calibrated_probability <= 1)',name='ck_calibrated_probability'),
        CheckConstraint('observation_a_id <> observation_b_id',name='ck_distinct_candidate'),
    )


class HypothesisSet(Base):
    __tablename__='hypothesis_sets'
    id = Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    title = Column(String(250),nullable=False)
    subject_description = Column(String(500),nullable=False)
    relation_type = Column(String(50),nullable=False)
    status = Column(String(30),nullable=False,default='draft')
    created_by = Column(String(120),nullable=False)
    created_at = Column(DateTime(timezone=True),default=now,nullable=False)
    version = Column(Integer,nullable=False,default=1)


class HypothesisOption(Base):
    __tablename__='hypothesis_options'
    id = Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    hypothesis_set_id = Column(Uuid(as_uuid=True),ForeignKey('hypothesis_sets.id',ondelete='RESTRICT'),nullable=False)
    option_key = Column(String(100),nullable=False)
    description = Column(String(600),nullable=False)
    subject_observation_id = Column(Uuid(as_uuid=True),ForeignKey('observations.id'))
    related_observation_id = Column(Uuid(as_uuid=True),ForeignKey('observations.id'))
    is_unknown = Column(Integer,nullable=False,default=0)
    calibrated_probability = Column(Float)
    model_id = Column(String(120))
    evidence_observation_ids = Column(JSON,nullable=False,default=list)
    reasoning = Column(Text,nullable=False,default='')
    __table_args__ = (
        UniqueConstraint('hypothesis_set_id','option_key',name='uq_hyp_option'),
        CheckConstraint('is_unknown IN (0,1)',name='ck_unknown_bool'),
        CheckConstraint('calibrated_probability IS NULL OR (calibrated_probability >= 0 AND calibrated_probability <= 1)',name='ck_hyp_prob'),
    )


class ResearchJob(Base):
    __tablename__ = 'research_jobs'
    id = Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    mode = Column(String(30),nullable=False)
    objective = Column(String(500),nullable=False)
    status = Column(String(30),nullable=False,default='queued')
    progress_current = Column(Integer,nullable=False,default=0)
    progress_total = Column(Integer,nullable=False,default=0)
    cost_limit_usd = Column(Float,nullable=False,default=0)
    spent_usd = Column(Float,nullable=False,default=0)
    created_by = Column(String(120),nullable=False)
    created_at = Column(DateTime(timezone=True),default=now,nullable=False)
    updated_at = Column(DateTime(timezone=True),default=now,nullable=False)
    last_error = Column(Text)
    __table_args__ = (
        CheckConstraint("mode IN ('autonomous','guided','conventional')",name='ck_job_mode'),
        CheckConstraint("status IN ('queued','paused','running','cancelled','complete','failed')",name='ck_job_status'),
        CheckConstraint('spent_usd >= 0 AND cost_limit_usd >= 0',name='ck_job_cost'),
    )


class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id = Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    actor = Column(String(120),nullable=False)
    action = Column(String(120),nullable=False)
    target_type = Column(String(100),nullable=False)
    target_id = Column(String(100),nullable=False)
    details_json = Column(JSON,nullable=False,default=dict)
    created_at = Column(DateTime(timezone=True),default=now,nullable=False)
    __table_args__ = (Index('ix_audit_target','target_type','target_id'),)


def upgrade():
    connection=op.get_bind()
    for table in Base.metadata.sorted_tables:
        table.create(connection,checkfirst=False)


def downgrade():
    connection=op.get_bind()
    # A downgrade destroying nonempty research history violates the Q37/Q49
    # contract. Explicit acknowledgement is required even in development.
    if os.environ.get('GEN_ALLOW_DESTRUCTIVE_DOWNGRADE')!='ISOLATED_TEST_ONLY':
        for table in Base.metadata.sorted_tables:
            if connection.scalar(select(func.count()).select_from(table)):
                raise RuntimeError('Destructive downgrade blocked: populated tables exist')
    for table in reversed(Base.metadata.sorted_tables):
        table.drop(connection,checkfirst=False)
