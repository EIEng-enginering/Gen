"""Materialised, replaceable *search index* only; original evidence stays immutable."""
from sqlalchemy import Column, Index, Integer, String, Uuid, UniqueConstraint, CheckConstraint
from .models import Base,uuid

class SearchMention(Base):
    __tablename__='general_search_mentions'
    id=Column(Uuid(as_uuid=True),primary_key=True,default=uuid)
    source_kind=Column(String(20),nullable=False)  # observed | staged
    source_id=Column(String(40),nullable=False)    # existing UUID, never a Gramps handle
    name_literal=Column(String(300),nullable=False,default='')
    surname_literal=Column(String(160),nullable=False,default='')
    surname_key=Column(String(160),nullable=False,default='')
    surname_soundex=Column(String(4),nullable=False,default='')
    given_literal=Column(String(160),nullable=False,default='')
    given_key=Column(String(160),nullable=False,default='')
    place_literal=Column(String(300),nullable=False,default='')
    place_key=Column(String(200),nullable=False,default='')
    county_key=Column(String(100),nullable=False,default='')
    event_type=Column(String(60),nullable=False,default='')
    year_hint=Column(Integer)
    year_end_hint=Column(Integer)
    provider=Column(String(120),nullable=False,default='')
    source_reference=Column(String(500),nullable=False,default='')
    source_document_id=Column(String(40),nullable=False,default='')
    possible_original=Column(String(250),nullable=False,default='')
    rights_label=Column(String(200),nullable=False,default='')
    status=Column(String(40),nullable=False)
    __table_args__=(UniqueConstraint('source_kind','source_id',name='uq_general_search_source'),
       CheckConstraint("source_kind IN ('observed','staged')"),
       Index('ix_general_search_surname_year','surname_key','year_hint','id'),
       Index('ix_general_search_soundex_year','surname_soundex','year_hint'),
       Index('ix_general_search_county_year','county_key','year_hint'),
       Index('ix_general_search_status','status','id'),)
