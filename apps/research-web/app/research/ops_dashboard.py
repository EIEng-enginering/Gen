"""WP-016 read-only project operations, approval queues, cost reservations.

No network/provider calls. The budget is a local planning limit, not billing.
All data is capped to prevent unbounded result sets on the Windows website.
"""
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.research.models import (SourceDocument, Observation, HypothesisSet, HypothesisOption,
    BranchRevision, BranchReview, GrampsChangePlan, GrampsPlanDecision, ResearchJob,
    ResearchTask, AuditEvent, SourceProviderPolicy, IdentityCandidate)


def _cent(value):
    return int((Decimal(str(value or 0))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


def _count(db,model):
    return db.scalar(select(func.count()).select_from(model)) or 0


def job_detail(db:Session,job_id:UUID):
    job=db.get(ResearchJob,job_id)
    if job is None:raise HTTPException(404,'Research job not found')
    tasks=db.scalars(select(ResearchTask).where(ResearchTask.job_id==job_id)
                     .order_by(ResearchTask.created_at.desc(),ResearchTask.id.desc()).limit(200)).all()
    # Charge and reservation totals must include ALL tasks. A dashboard detail page
    # may display 200, but must not silently omit spending from total sums.
    task_totals=db.execute(select(ResearchTask.status,func.count(),
                     func.sum(ResearchTask.reserved_cost_cents),func.sum(ResearchTask.spent_cost_cents))
                     .where(ResearchTask.job_id==job_id).group_by(ResearchTask.status)).all()
    charged=sum(int(row[3] or 0) for row in task_totals)
    held=sum(int(row[2] or 0) for row in task_totals if row[0] in ('queued','leased','paused'))
    return {'job_id':str(job.id),'mode':job.mode,'objective':job.objective,
            'status':job.status,'progress_current':job.progress_current,'progress_total':job.progress_total,
            'budget_limit_cents':_cent(job.cost_limit_usd),
            'reported_spent_cents':charged,'reserved_cents':held,
            'available_cents':max(0,_cent(job.cost_limit_usd)-charged-held),
            'task_status_counts':{row[0]:int(row[1]) for row in task_totals},
            'tasks':[{'id':str(t.id),'key':t.task_key,'kind':t.kind,
                      'status':t.status,'reserved_cost_cents':t.reserved_cost_cents,
                      'spent_cost_cents':t.spent_cost_cents,'attempt':t.attempt,
                      'created_at':t.created_at.isoformat()} for t in tasks],
            'tasks_truncated':sum(int(row[1]) for row in task_totals)>len(tasks),
            'billable_requests_executed':False,'external_provider_executor_enabled':False,
            'accepted_tree_mutation_enabled':False}


def review_queue(db:Session,limit:int=50):
    plans=db.scalars(select(GrampsChangePlan).order_by(GrampsChangePlan.created_at.desc()).limit(500)).all()
    decided=set(db.scalars(select(GrampsPlanDecision.plan_id).where(
        GrampsPlanDecision.plan_id.in_([p.id for p in plans])))) if plans else set()
    pending=[{'plan_id':str(p.id),'hypothesis_set_id':str(p.hypothesis_set_id),
              'digest_sha256':p.digest_sha256,'created_at':p.created_at.isoformat(),
              'status':'awaits_human_research_decision_not_write_approval'}
             for p in plans if p.id not in decided]
    # Show latest unreviewed branch snapshots; all research only.
    revision_rows=db.scalars(select(BranchRevision).order_by(BranchRevision.created_at.desc()).limit(500)).all()
    reviewed=set(db.scalars(select(BranchReview.revision_id).where(
        BranchReview.revision_id.in_([r.id for r in revision_rows])))) if revision_rows else set()
    unreviewed=[{'revision_id':str(r.id),'hypothesis_set_id':str(r.hypothesis_set_id),
                 'revision_number':r.revision_number,'status':'research_review_pending'}
                for r in revision_rows if r.id not in reviewed]
    return {'gramps_change_plans':pending[:limit], 'branch_revisions':unreviewed[:limit],
            'results_capped':len(plans)==500 or len(revision_rows)==500,
            'write_permission_granted':False,
            'warning':'A research review decision never authorises an accepted Gramps tree write.'}


def overview(db:Session):
    states=db.execute(select(ResearchJob.status,func.count()).group_by(ResearchJob.status)).all()
    tasks=db.execute(select(ResearchTask.status,func.count()).group_by(ResearchTask.status)).all()
    jobs=db.scalars(select(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(15)).all()
    providers=db.scalars(select(SourceProviderPolicy).order_by(SourceProviderPolicy.provider).limit(25)).all()
    audit=db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(15)).all()
    return {'counts':{'documents':_count(db,SourceDocument),'appearances':_count(db,Observation),
             'hypotheses':_count(db,HypothesisSet),'candidate_matches':_count(db,IdentityCandidate),
             'research_jobs':_count(db,ResearchJob),'research_tasks':_count(db,ResearchTask)},
        'job_states':{status:int(count) for status,count in states},
        'task_states':{status:int(count) for status,count in tasks},
        'recent_jobs':[{'id':str(j.id),'objective':j.objective,'mode':j.mode,'status':j.status,
                        'budget_limit_cents':_cent(j.cost_limit_usd),'reported_spent_cents':_cent(j.spent_usd)} for j in jobs],
        'providers':[{'provider':p.provider,'access_mode':p.access_mode,
                      'requests_per_day':p.requests_per_day,'daily_budget_cents':p.daily_budget_cents,
                      'execution_enabled':False} for p in providers],
        'audit':[{'action':a.action,'target_type':a.target_type,'target_id':a.target_id,
                  'created_at':a.created_at.isoformat()} for a in audit],
        'operations_enabled':{'manual_job_control':True,'manual_research_review':True,
                              'external_providers':False,'cloud_ai':False,'gramps_writes':False},
        'warning':'Queue, costs and provider policies are local planning and reported metadata, not proof of external execution or spending.'}
