"""Separate quarantined AI/bulk intake tables. Import this module in route startup."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, Uuid, CheckConstraint
from .models import Base, uuid, now

class AcquisitionBatch(Base):
    __tablename__='acquisition_batches'
    id=Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    batch_key=Column(String(120),nullable=False,unique=True)
    input_kind=Column(String(30),nullable=False)
    created_by=Column(String(120),nullable=False)
    created_at=Column(DateTime(timezone=True),default=now,nullable=False)
    rights_attested=Column(Integer,nullable=False)
    row_count=Column(Integer,nullable=False,default=0)
    __table_args__=(CheckConstraint('row_count >= 0'),)

class StagedEvidence(Base):
    __tablename__='staged_evidence'
    id=Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    batch_id=Column(Uuid(as_uuid=True),ForeignKey('acquisition_batches.id',ondelete='RESTRICT'),nullable=False)
    row_number=Column(Integer,nullable=False)
    sha256=Column(String(64),nullable=False)
    payload=Column(JSON,nullable=False)
    surname_key=Column(String(160),nullable=False,default='')
    place_key=Column(String(200),nullable=False,default='')
    year_hint=Column(Integer)
    status=Column(String(30),nullable=False,default='awaiting_human_review')
    reason=Column(Text,nullable=False,default='')
    import_document_id=Column(Uuid(as_uuid=True),ForeignKey('source_documents.id',ondelete='RESTRICT'))
    import_observation_id=Column(Uuid(as_uuid=True),ForeignKey('observations.id',ondelete='RESTRICT'))
    reviewed_by=Column(String(120))
    reviewed_at=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint('batch_id','row_number'), Index('ix_staged_evidence_batch','batch_id','status'),
        Index('ix_staged_evidence_surname_year','surname_key','year_hint'))

class StagedPersonLink(Base):
    __tablename__='staged_person_links'
    id=Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    staged_id=Column(Uuid(as_uuid=True),ForeignKey('staged_evidence.id',ondelete='RESTRICT'),nullable=False)
    gramps_handle=Column(String(100),nullable=False)
    rationale=Column(Text,nullable=False)
    status=Column(String(30),nullable=False,default='proposed')
    created_by=Column(String(120),nullable=False)
    created_at=Column(DateTime(timezone=True),default=now,nullable=False)
    __table_args__=(Index('ix_staged_link_staged','staged_id'),)
