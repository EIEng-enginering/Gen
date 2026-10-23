"""WP-011 supervised local task queue with idempotency, finite leases and cents budgets.

No internet requests, billable services, provider APIs or Gramps mutations occur.
All 'approved_api_request' tasks remain non-executable in this release.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated, Literal
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app import main
from app.research.api import audit, mutation_guard
from app.research.db import session
from app.research.models import ResearchJob, ResearchTask

router=APIRouter(prefix='/api/v1/research',tags=['WP-011 Supervised jobs'],dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]


def utc_now():return datetime.now(timezone.utc)


def due(value):
    if value is None:return True
    if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
    return value<=utc_now()


class TaskIn(BaseModel):
    task_key:str=Field(min_length=3,max_length=160,pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]+$')
    kind:Literal['local_review','manual_lookup','approved_api_request']='local_review'
    source_provider:str=Field(min_length=2,max_length=120)
    reserved_cost_cents:int=Field(default=0,ge=0,le=1_000_000)
    input_json:dict=Field(default_factory=dict)


class ClaimIn(BaseModel):
    worker_name:str=Field(min_length=3,max_length=120,pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]+$')
    lease_seconds:int=Field(default=300,ge=30,le=1800)


class FinishIn(BaseModel):
    lease_token:str=Field(min_length=30,max_length=250)
    completion_key:str=Field(min_length=3,max_length=160)
    spent_cost_cents:int=Field(default=0,ge=0,le=1_000_000)
    result:Literal['complete','failed']='complete'


def cents_limit(job:ResearchJob):
    return int((Decimal(str(job.cost_limit_usd))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


def snapshot(task:ResearchTask):
    return {'id':str(task.id),'job_id':str(task.job_id),'task_key':task.task_key,'kind':task.kind,
            'source_provider':task.source_provider,'status':task.status,
            'reserved_cost_cents':task.reserved_cost_cents,'spent_cost_cents':task.spent_cost_cents,
            'attempt':task.attempt,'lease_expires_at':task.lease_expires_at.isoformat() if task.lease_expires_at else None,
            'executed_external_request':False,'gramps_written':False}


def lock_job(db,id):
    # PostgreSQL serialises cost reservations per job across concurrent callers.
    job=db.scalar(select(ResearchJob).where(ResearchJob.id==id).with_for_update())
    if not job:raise HTTPException(404,'Research job not found')
    return job


@router.post('/jobs/{job_id}/tasks',dependencies=[Depends(mutation_guard)],status_code=201)
def create_task(job_id:UUID,body:TaskIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    job=lock_job(db,job_id)
    if job.status in ('cancelled','complete','failed'):
        raise HTTPException(409,'Cannot add task to a terminal research job')
    prior=db.scalar(select(ResearchTask).where(ResearchTask.job_id==job_id,ResearchTask.task_key==body.task_key))
    if prior:
        if any(getattr(prior,k)!=v for k,v in body.model_dump().items()):
            raise HTTPException(409,'Task idempotency key conflicts with an existing task')
        return {'created':False,**snapshot(prior)}
    # Existing job cost limit is authoritative. Count charges and all pending reservations.
    tasks=db.scalars(select(ResearchTask).where(ResearchTask.job_id==job_id)).all()
    committed=sum(x.spent_cost_cents if x.status in ('complete','failed') else x.reserved_cost_cents for x in tasks if x.status!='cancelled')
    if committed+body.reserved_cost_cents>cents_limit(job):
        raise HTTPException(409,'Job budget exhausted or reserved; no charge was made')
    task=ResearchTask(job_id=job_id,**body.model_dump(),status='queued')
    db.add(task);db.flush()
    audit(db,user,'task_created','research_task',task.id,{'job_id':str(job_id),'kind':body.kind})
    db.commit()
    return {'created':True,**snapshot(task)}


@router.get('/jobs/{job_id}/tasks')
def list_tasks(job_id:UUID,db:DB,limit:int=Query(100,ge=1,le=200)):
    if db.get(ResearchJob,job_id) is None:raise HTTPException(404,'Research job not found')
    return [snapshot(x) for x in db.scalars(select(ResearchTask).where(ResearchTask.job_id==job_id)
           .order_by(ResearchTask.created_at,ResearchTask.id).limit(limit))]


@router.post('/jobs/{job_id}/tasks/{task_id}/claim',dependencies=[Depends(mutation_guard)])
def claim_task(job_id:UUID,task_id:UUID,body:ClaimIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    job=lock_job(db,job_id)
    task=db.scalar(select(ResearchTask).where(ResearchTask.id==task_id,ResearchTask.job_id==job_id).with_for_update())
    if task is None:raise HTTPException(404,'Research task not found')
    if job.status!='queued':raise HTTPException(409,'Research job not queued (paused or terminal)')
    if task.kind!='local_review':
        raise HTTPException(403,'External and manual source tasks cannot be claimed by the local executor')
    if task.status=='leased' and not due(task.lease_expires_at):
        raise HTTPException(409,'Research task already leased')
    if task.status not in ('queued','leased'):
        raise HTTPException(409,'Task is not eligible to be claimed')
    # If a prior lease expires, the caller must check the local operation's
    # idempotency key before redoing any side effect. No external side effects exist here.
    token=token_urlsafe(32)
    task.lease_token_sha256=sha256(token.encode()).hexdigest()
    task.lease_owner=body.worker_name
    task.lease_expires_at=utc_now()+timedelta(seconds=body.lease_seconds)
    task.status='leased';task.attempt+=1;task.updated_at=utc_now()
    audit(db,user,'local_task_leased','research_task',task.id,{'attempt':task.attempt})
    db.commit()
    return {**snapshot(task),'lease_token':token}


@router.post('/jobs/{job_id}/tasks/{task_id}/finish',dependencies=[Depends(mutation_guard)])
def finish_task(job_id:UUID,task_id:UUID,body:FinishIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    job=lock_job(db,job_id)
    task=db.scalar(select(ResearchTask).where(ResearchTask.id==task_id,ResearchTask.job_id==job_id).with_for_update())
    if task is None:raise HTTPException(404,'Research task not found')
    if task.status in ('complete','failed'):
        if task.completed_key==body.completion_key and task.spent_cost_cents==body.spent_cost_cents and task.status==body.result:
            return {'idempotent':True,**snapshot(task)}
        raise HTTPException(409,'Task already finalised with different completion details')
    if job.status in ('paused','cancelled','failed','complete'):
        raise HTTPException(409,'Research job is paused or terminal')
    if task.status!='leased' or due(task.lease_expires_at):
        raise HTTPException(409,'Task lease missing or expired')
    if sha256(body.lease_token.encode()).hexdigest()!=task.lease_token_sha256:
        raise HTTPException(403,'Invalid lease token')
    if body.spent_cost_cents>task.reserved_cost_cents:
        raise HTTPException(409,'Reported cost exceeds reserved budget')
    task.status=body.result;task.completed_key=body.completion_key
    task.spent_cost_cents=body.spent_cost_cents
    task.lease_token_sha256=None;task.lease_owner=None;task.lease_expires_at=None
    task.updated_at=utc_now()
    job.spent_usd=float(Decimal(str(job.spent_usd))+Decimal(body.spent_cost_cents)/100)
    job.progress_current+=1
    audit(db,user,'task_finalised','research_task',task.id,
          {'result':body.result,'spent_cost_cents':body.spent_cost_cents})
    db.commit()
    return {'idempotent':False,**snapshot(task)}


@router.get('/jobs/{job_id}/budget')
def budget(job_id:UUID,db:DB):
    job=db.get(ResearchJob,job_id)
    if not job:raise HTTPException(404,'Research job not found')
    tasks=db.scalars(select(ResearchTask).where(ResearchTask.job_id==job_id)).all()
    spent=sum(x.spent_cost_cents for x in tasks)
    reserved=sum(x.reserved_cost_cents for x in tasks if x.status in ('queued','leased','paused'))
    return {'budget_limit_cents':cents_limit(job),'task_charges_cents':spent,
            'outstanding_reservations_cents':reserved,'available_cents':max(0,cents_limit(job)-spent-reserved),
            'job_total_tasks':len(tasks),'external_execution_enabled':False}

from app.research.models import SourceProviderPolicy


class ProviderPolicyIn(BaseModel):
    provider:str=Field(min_length=2,max_length=120,pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]+$')
    access_mode:Literal['manual_only','approved_api','licensed_local_dataset']='manual_only'
    permission_reference:str=Field(min_length=10,max_length=500)
    requests_per_day:int=Field(default=0,ge=0,le=100000)
    cooldown_seconds:int=Field(default=0,ge=0,le=86400)
    daily_budget_cents:int=Field(default=0,ge=0,le=1_000_000)


@router.post('/source-provider-policies',dependencies=[Depends(mutation_guard)],status_code=201)
def source_provider_policy(body:ProviderPolicyIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    existing=db.scalar(select(SourceProviderPolicy).where(SourceProviderPolicy.provider==body.provider))
    if existing:
        if any(getattr(existing,k)!=v for k,v in body.model_dump().items()):
            raise HTTPException(409,'Provider policy is immutable; changes require a separately reviewed policy revision')
        return {'id':str(existing.id),'created':False,'execution_enabled':False}
    policy=SourceProviderPolicy(**body.model_dump(),created_by=user)
    db.add(policy);db.flush()
    audit(db,user,'source_provider_policy_created','source_provider',policy.id,
          {'provider':policy.provider,'access_mode':policy.access_mode})
    db.commit()
    return {'id':str(policy.id),'created':True,'execution_enabled':False}


@router.get('/source-provider-policies')
def list_provider_policies(db:DB,limit:int=Query(50,ge=1,le=100)):
    rows=db.scalars(select(SourceProviderPolicy).order_by(SourceProviderPolicy.provider).limit(limit)).all()
    return [{'provider':r.provider,'access_mode':r.access_mode,
             'permission_reference':r.permission_reference,'requests_per_day':r.requests_per_day,
             'cooldown_seconds':r.cooldown_seconds,'daily_budget_cents':r.daily_budget_cents,
             'execution_enabled':False,'requests_used_today':0,'limiter':'not_activated_without_live_connector'}
            for r in rows]
