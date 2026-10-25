"""Authenticated general search and source-respecting provisional correlations."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app import main
from .db import session
from .api import mutation_guard,audit
from .general_search_models import SearchMention
from .general_search_service import sync_page,search,correlate

router=APIRouter(prefix='/api/v1/research/general',tags=['General source search'],dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]

class SyncIn(BaseModel):
    source_kind:str=Field(pattern='^(observed|staged)$')
    after:UUID|None=None
    limit:int=Field(default=200,ge=1,le=500)

@router.post('/index/sync',dependencies=[Depends(mutation_guard)])
def sync_index(body:SyncIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    result=sync_page(db,body.source_kind,body.after,body.limit)
    audit(db,user,'general_search_index_sync','general_search',body.source_kind,
        {'count':result['processed'],'kind':body.source_kind})
    db.commit()
    return result

@router.get('/search')
def search_index(db:DB,surname:str=Query(default='',max_length=120),given:str=Query(default='',max_length=120),
    county:str=Query(default='',max_length=100),year_from:int|None=Query(default=None,ge=1500,le=2026),
    year_to:int|None=Query(default=None,ge=1500,le=2026),record_type:str=Query(default='',max_length=60),
    provider:str=Query(default='',max_length=120),include_staged:bool=True,
    mode:str=Query(default='exact',pattern='^(exact|phonetic|prefix)$'),
    limit:int=Query(default=30,ge=1,le=100),cursor:str|None=Query(default=None,max_length=60)):
    try:return search(db,surname=surname,given=given,county_filter=county,
       year_from=year_from,year_to=year_to,record_type=record_type,provider=provider,
       include_staged=include_staged,mode=mode,limit=limit,after=cursor)
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.get('/mentions/{mention_id}/correlations')
def compare_mention(mention_id:UUID,db:DB,limit:int=Query(default=20,ge=1,le=50)):
    obj=db.get(SearchMention,mention_id)
    if not obj:raise HTTPException(404,'Indexed mention not found')
    return correlate(db,obj,limit)

@router.get('/coverage')
def coverage(db:DB):
    rows=db.execute(select(SearchMention.provider,SearchMention.event_type,SearchMention.source_kind,
        func.count(SearchMention.id)).group_by(SearchMention.provider,SearchMention.event_type,
        SearchMention.source_kind).order_by(SearchMention.provider,SearchMention.event_type).limit(120)).all()
    return {'local_indexed': [{'provider':r[0], 'event_type':r[1], 'source_kind':r[2],
        'rows':r[3]} for r in rows],
        'providers_executed':0,'coverage_complete':False,'permission_to_search_external_sites':False,
        'unknown_collections':'All unindexed or unlicensed collections are outside observed coverage.',
        'notes':['Index counts are not a count of independent original sources.',
            'Catalogues and AI leads are not reviewed evidence.',
            'FreeBMD/FreeCEN/FreeREG public website automation is not authorised.']}
