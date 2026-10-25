"""Authenticated local-first, citation-checked research conversations.

Research-only database persistence. No Gramps writes or website executors.
"""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.api import mutation_guard, audit
from app.research.models import AIResearchRun
from app.research.ai_research_engine import answer as research_answer, model_state
from app.research.gramps_context import (ContextBlocked, configured as gramps_configured,
                                         search_people, read_person_context)

DB=Annotated[Session,Depends(session)]
USER=Annotated[str,Depends(main.authenticate)]
router=APIRouter(prefix='/api/v1/research/ai',tags=['AI Research (local-first)'],
                 dependencies=[Depends(main.authenticate)])

class AskIn(BaseModel):
    question:str=Field(min_length=4,max_length=1000)
    mode:Literal['guided','conventional','autonomous']='guided'
    surname:str=Field(default='',max_length=100,pattern=r'^[^<>\x00-\x1f]*$')
    county:str=Field(default='',max_length=100,pattern=r'^[^<>\x00-\x1f]*$')
    from_year:int|None=Field(default=None,ge=1000,le=2100)
    to_year:int|None=Field(default=None,ge=1000,le=2100)
    observation_ids:list[UUID]=Field(default_factory=list,max_length=6)
    gramps_person_handle:str|None=Field(default=None,max_length=128)
    # Explicitly no model control over data selection, mode or external sources.
    @model_validator(mode='after')
    def validate_scope(self):
        if self.from_year and self.to_year and self.from_year>self.to_year:
            raise ValueError('Date interval is reversed')
        if not (self.surname.strip() or self.county.strip() or self.observation_ids
                or self.gramps_person_handle):
            raise ValueError('Specify surname, county, cited observations, or a selected Gramps person')
        if len(set(self.observation_ids))!=len(self.observation_ids):
            raise ValueError('Duplicate observation ID')
        return self

@router.get('/capabilities')
def capabilities():
    state=model_state()
    return {'local_model':state,'model_provider':'local_ollama',
            'gramps_guest_context':{'configured':gramps_configured(),
                                    'status':'configured_not_probed' if gramps_configured() else 'not_configured',
                                    'scope':'Guest-visible non-private objects only'},
            'local_rule_fallback':True,'optional_cloud_enabled':False,
            'cloud_data_transfer':False,'provider_network_search_enabled':False,
            'accepted_gramps_writes_enabled':False,
            'autonomous_mode':'local_planning_only_no_external_execution',
            'status_note':'Configured is not the same as reachable. A model run is marked local_model only after a checked response.'}


def _gramps_or_http(operation, value):
    try:
        return operation(value)
    except ContextBlocked as exc:
        if exc.code in ('invalid_person_search', 'invalid_gramps_handle'):
            raise HTTPException(422, exc.code) from None
        if exc.code == 'gramps_object_not_found':
            raise HTTPException(404, exc.code) from None
        raise HTTPException(503, exc.code) from None


@router.get('/gramps/search')
def gramps_person_search(q:str=Query(min_length=2,max_length=80)):
    return _gramps_or_http(search_people, q)


@router.get('/gramps/people/{handle}')
def gramps_person_context(handle:str):
    return _gramps_or_http(read_person_context, handle)

@router.post('/ask',dependencies=[Depends(mutation_guard)])
def ask(body:AskIn,db:DB,user:USER):
    tree_context = (_gramps_or_http(read_person_context, body.gramps_person_handle)
                    if body.gramps_person_handle else None)
    result=research_answer(db,body.question,body.mode,body.surname.strip(),body.county.strip(),
                           body.from_year,body.to_year,body.observation_ids,
                           gramps_context=tree_context)
    row=AIResearchRun(created_by=user,question=body.question,mode=body.mode,
                       surname=body.surname.strip(),county=body.county.strip(),
                       scope_json={'from_year':body.from_year,'to_year':body.to_year,
                                   'observation_ids':[str(i) for i in body.observation_ids],
                                   'gramps_person_handle':body.gramps_person_handle},
                       answer_json=result,execution_status=result['model_execution'],
                       model_name=result['model'])
    db.add(row);db.flush()
    audit(db,user,'ai_research_run_created','ai_research_run',row.id,
          {'execution':row.execution_status,'cited_count':len(result['citations'])})
    db.commit()
    return {'id':str(row.id),'created_at':row.created_at.isoformat(),'question':row.question,
            'mode':row.mode,'scope':{'surname':row.surname,'county':row.county,**row.scope_json},
            'answer':result}

@router.get('/history')
def history(db:DB,user:USER,limit:int=Query(20,ge=1,le=50)):
    rows=db.scalars(select(AIResearchRun).where(AIResearchRun.created_by==user)
                    .order_by(AIResearchRun.created_at.desc(),AIResearchRun.id.desc()).limit(limit)).all()
    return [{'id':str(r.id),'question':r.question[:150], 'mode':r.mode,
             'surname':r.surname,'county':r.county,'execution':r.execution_status,
             'created_at':r.created_at.isoformat()} for r in rows]

@router.get('/history/{run_id}')
def run_detail(run_id:UUID,db:DB,user:USER):
    row=db.get(AIResearchRun,run_id)
    if not row or row.created_by!=user:raise HTTPException(404,'Research run not found')
    return {'id':str(row.id),'question':row.question,'mode':row.mode,
            'created_at':row.created_at.isoformat(),
            'scope':{'surname':row.surname,'county':row.county,**row.scope_json},
            'answer':row.answer_json}
