"""WP-009: user-curated English place register and bounded identity-candidate retrieval.

No network ingestion, no cross-service scraping, no automatic tree merge.
"""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app import main
from app.research.api import audit, mutation_guard, obj_dict
from app.research.db import session
from app.research.models import HistoricalPlace, Observation, SourceDocument
from app.research.historical_linkage import candidate_assessment
from app.research.matching import standardise

router = APIRouter(prefix='/api/v1/research', tags=['WP-009 English historical matching'],
                   dependencies=[Depends(main.authenticate)])
DB = Annotated[Session, Depends(session)]


class PlaceIn(BaseModel):
    source_document_id: UUID
    place_key: str = Field(min_length=1, max_length=140)
    label: str = Field(min_length=1, max_length=300)
    county_label: str = Field(default='', max_length=160)
    jurisdiction_type: Literal['parish', 'county', 'registration_district', 'chapelry', 'settlement', 'undetermined'] = 'undetermined'
    valid_from_year: int|None = Field(default=None, ge=1000, le=2100)
    valid_to_year: int|None = Field(default=None, ge=1000, le=2100)
    aliases_json: list[str] = Field(default_factory=list, max_length=20)
    evidence_note: str = Field(min_length=5, max_length=3000)

    @field_validator('aliases_json')
    @classmethod
    def unique_aliases(cls, names):
        names = [x.strip() for x in names]
        if any(not x or len(x) > 160 for x in names) or len(set(x.casefold() for x in names)) != len(names):
            raise ValueError('Aliases must be unique, non-empty and at most 160 characters')
        return names

    @model_validator(mode='after')
    def interval(self):
        if (self.valid_from_year is not None and self.valid_to_year is not None and
                self.valid_from_year > self.valid_to_year):
            raise ValueError('Historical date interval is reversed')
        return self


@router.post('/historical-places', status_code=201, dependencies=[Depends(mutation_guard)])
def add_historical_place(body: PlaceIn, db: DB, actor: Annotated[str, Depends(main.authenticate)]):
    if db.get(SourceDocument, body.source_document_id) is None:
        raise HTTPException(422, 'A registered historical source is required')
    existing = db.scalar(select(HistoricalPlace).where(
        HistoricalPlace.source_document_id == body.source_document_id,
        HistoricalPlace.place_key == body.place_key))
    fields = body.model_dump()
    if existing:
        if any(getattr(existing, key) != value for key, value in fields.items() if key!='source_document_id'):
            raise HTTPException(409, 'Place source/key collision; original evidence is immutable')
        return {'id':str(existing.id), 'created':False}
    place = HistoricalPlace(**fields, created_by=actor)
    db.add(place);db.flush()
    audit(db,actor,'historical_place_created','historical_place',place.id,
          {'source_document_id':str(place.source_document_id),'place_key':place.place_key})
    db.commit()
    return {'id':str(place.id),'created':True}


@router.get('/historical-places')
def historical_places(db: DB,q:str=Query('',max_length=160), year:int|None=Query(None,ge=1000,le=2100),
                      limit:int=Query(25,ge=1,le=100)):
    # Bound results and keep all original sources separate, even when labels agree.
    stmt=select(HistoricalPlace).order_by(HistoricalPlace.label,HistoricalPlace.place_key).limit(limit)
    if q:
        escaped=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        stmt=stmt.where(or_(HistoricalPlace.label.ilike('%'+escaped+'%',escape='\\'),
                            HistoricalPlace.county_label.ilike('%'+escaped+'%',escape='\\')))
    if year is not None:
        stmt=stmt.where(or_(HistoricalPlace.valid_from_year.is_(None),HistoricalPlace.valid_from_year <= year),
                        or_(HistoricalPlace.valid_to_year.is_(None),HistoricalPlace.valid_to_year >= year))
    return [obj_dict(x,['id','source_document_id','place_key','label','county_label',
             'jurisdiction_type','valid_from_year','valid_to_year','aliases_json','evidence_note']) for x in db.scalars(stmt)]


@router.get('/observations/{observation_id}/historical-candidates')
def historical_candidates(observation_id: UUID, db: DB,limit:int=Query(20,ge=1,le=50)):
    """No mutation and no misleading probability. Indexed blocking followed by bounded ranking."""
    focus=db.get(Observation,observation_id)
    if focus is None:raise HTTPException(404,'Observation not found')
    surname=(focus.surname_verbatim or '').strip()
    if len(surname)<2:
        return {'candidates':[],'warning':'Surname too short to retrieve candidates reliably',
                'calibration_status':'NOT_CALIBRATED', 'accepted_tree_written':False}
    # A conservative bounded candidate set. Common names may be truncated, and
    # the UI is told this is NOT exhaustive matching. Do not run unbounded searches.
    surname_prefix=standardise(surname).replace(' ','')[:2]
    if len(surname_prefix)<2:
        raise HTTPException(422,'Insufficient surname characters for bounded search')
    stmt=select(Observation,SourceDocument.origin_group).join(
        SourceDocument, Observation.document_id == SourceDocument.id).where(
        Observation.id != observation_id,
        Observation.surname_verbatim.ilike(surname_prefix+'%')).order_by(Observation.id).limit(500)
    other_rows=db.execute(stmt).all()
    focus_source=db.get(SourceDocument,focus.document_id)
    matches=[]
    for candidate,origin in other_rows:
        result=candidate_assessment(focus,candidate,focus_source.origin_group,origin)
        if result['ranking_score']>=0.20:
            matches.append({'observation_id':str(candidate.id),
                 'name_as_recorded':candidate.person_name_verbatim,
                 'event_type':candidate.event_type,**result})
    matches.sort(key=lambda item:(-item['ranking_score'],item['observation_id']))
    return {'candidates':matches[:limit], 'examined':len(other_rows),
        'retrieval_complete':len(other_rows)<500,
        'warning':'Heuristic rankings are NOT probabilities. Prefix blocking may miss spelling variants; incomplete retrieval may require manual broad searches.',
        'calibration_status':'NOT_CALIBRATED','accepted_tree_written':False}
