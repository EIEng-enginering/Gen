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
    # Explicitly no model control over data selection, mode or external sources.
    @model_validator(mode='after')
    def validate_scope(self):
        if self.from_year and self.to_year and self.from_year>self.to_year:
            raise ValueError('Date interval is reversed')
        if not (self.surname.strip() or self.county.strip() or self.observation_ids):
            raise ValueError('Specify surname, county, or cited observations to bound retrieval')
        if len(set(self.observation_ids))!=len(self.observation_ids):
            raise ValueError('Duplicate observation ID')
        return self

@router.get('/capabilities')
def capabilities():
    state=model_state()
    return {'local_model':state,'model_provider':'local_ollama',
            'local_rule_fallback':True,'optional_cloud_enabled':False,
            'cloud_data_transfer':False,'provider_network_search_enabled':False,
            'accepted_gramps_writes_enabled':False,
            'autonomous_mode':'local_planning_only_no_external_execution',
            'status_note':'Configured is not the same as reachable. A model run is marked local_model only after a checked response.'}

@router.post('/ask',dependencies=[Depends(mutation_guard)])
def ask(body:AskIn,db:DB,user:USER):
    result=research_answer(db,body.question,body.mode,body.surname.strip(),body.county.strip(),
                           body.from_year,body.to_year,body.observation_ids)
    row=AIResearchRun(created_by=user,question=body.question,mode=body.mode,
                       surname=body.surname.strip(),county=body.county.strip(),
                       scope_json={'from_year':body.from_year,'to_year':body.to_year,
                                   'observation_ids':[str(i) for i in body.observation_ids]},
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
