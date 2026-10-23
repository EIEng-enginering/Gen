"""WP-015 authenticated source-grounded assistant API (offline, no model calls)."""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.research_assistant import assist

router=APIRouter(prefix='/api/v1/research/assistant',tags=['WP-015 Guided assistant'],
    dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]

class ResearchQuestion(BaseModel):
    question:str=Field(min_length=4,max_length=1000)
    mode:Literal['autonomous','guided','conventional']='guided'
    observation_ids:list[UUID]=Field(default_factory=list,max_length=6)

@router.post('/answer')
def answer(body:ResearchQuestion,db:DB):
    return assist(db,body.question,body.mode,body.observation_ids)

@router.get('/capabilities')
def capabilities():
    return {'local_rules_available':True,'llm_model_active':False,'llm_provider':None,
            'external_processing':False,'data_sent_to_cloud':False,
            'accepted_tree_mutation_enabled':False,
            'modes':['autonomous','guided','conventional'],
            'mode_note':'Autonomous mode presently generates a plan; no executor is enabled.'}
