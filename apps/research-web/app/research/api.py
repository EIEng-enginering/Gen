"""WP-002 research endpoints. All mutations remain in the provisional DB."""
from datetime import date
from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.models import (SourceDocument, Observation, TranscriptionRevision,
    IdentityCandidate, HypothesisSet, HypothesisOption, ResearchJob, AuditEvent)
from app.research.schemas import (DocumentIn, ObservationIn, RevisionIn,
    HypothesisIn, JobIn, JobUpdate, DecisionIn)
from app.research.matching import compare

router=APIRouter(prefix='/api/v1/research',tags=['Provisional research'],dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]


def mutation_guard(request:Request, intent:Annotated[str|None,Header(alias='X-24Gen-Intent')]=None):
    # HTTP Basic browsers may reuse cached credentials; custom header stops
    # cross-site forms from silently invoking a local write endpoint.
    if intent!='research':
        raise HTTPException(403,'Explicit research mutation header required')
    origin=request.headers.get('origin')
    if origin:
        from urllib.parse import urlparse
        parsed=urlparse(origin)
        if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1','[::1]'):
            raise HTTPException(403,'Cross-origin mutation prohibited')


def audit(db,actor,action,obj,oid,details=None):
    db.add(AuditEvent(actor=actor,action=action,target_type=obj,target_id=str(oid),details_json=details or {}))


def obj_dict(record,fields):
    out={}
    for f in fields:
        v=getattr(record,f)
        out[f]=str(v) if isinstance(v,(UUID,date)) else v
    return out


def required(db,model,ident):
    result=db.get(model,ident)
    if result is None:
        raise HTTPException(404,'Object not found')
    return result


@router.get('/summary')
def summary(db:DB):
    return {name:db.scalar(select(func.count()).select_from(model)) for name,model in (
        ('documents',SourceDocument),('observations',Observation),
        ('identity_candidates',IdentityCandidate),('hypothesis_sets',HypothesisSet),
        ('jobs',ResearchJob))}


@router.post('/documents',status_code=201,dependencies=[Depends(mutation_guard)])
def create_document(body:DocumentIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    existing=db.scalar(select(SourceDocument).where(SourceDocument.provider==body.provider,
                                                   SourceDocument.provider_record_id==body.provider_record_id))
    if existing:
        # Idempotent only for identical identifying provenance; otherwise collision.
        if (existing.reference,existing.origin_group,existing.licence,existing.access_method)!=(body.reference,body.origin_group,body.licence,body.access_method):
            raise HTTPException(409,'Existing provider ID has conflicting provenance')
        return {'id':str(existing.id),'created':False}
    doc=SourceDocument(**body.model_dump(),acquisition_operator=user)
    db.add(doc)
    db.flush()
    audit(db,user,'document_created','source_document',doc.id,{'provider':doc.provider})
    db.commit()
    return {'id':str(doc.id),'created':True}


@router.get('/documents')
def documents(db:DB,q:str='',limit:int=Query(50,ge=1,le=200),offset:int=Query(0,ge=0)):
    stmt=select(SourceDocument).order_by(SourceDocument.acquired_at.desc()).limit(limit).offset(offset)
    if q:
        stmt=stmt.where(or_(SourceDocument.title.ilike('%'+q+'%'),SourceDocument.reference.ilike('%'+q+'%'),SourceDocument.provider.ilike('%'+q+'%')))
    rows=db.scalars(stmt).all()
    return [obj_dict(x,['id','provider','provider_record_id','title','reference','origin_group','licence','access_method','original_url','source_class']) for x in rows]


@router.get('/documents/{document_id}')
def document_detail(document_id:UUID,db:DB):
    d=required(db,SourceDocument,document_id)
    return obj_dict(d,['id','provider','provider_record_id','title','reference','origin_group','licence','rights_note','access_method','original_url','source_class','document_kind','checksum_sha256'])


@router.post('/documents/{document_id}/observations',status_code=201,dependencies=[Depends(mutation_guard)])
def add_observation(document_id:UUID,body:ObservationIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    required(db,SourceDocument,document_id)
    old=db.scalar(select(Observation).where(Observation.document_id==document_id,Observation.observation_key==body.observation_key))
    if old:
        if any(getattr(old,k)!=v for k,v in [('person_name_verbatim',body.person_name_verbatim),('event_type',body.event_type),('event_date_verbatim',body.event_date_verbatim),('location_verbatim',body.location_verbatim) ]):
            raise HTTPException(409,'Observation key conflict; record a transcription revision instead')
        return {'id':str(old.id),'created':False}
    d=body.model_dump(mode='json')
    obj=Observation(document_id=document_id,**d)
    db.add(obj);db.flush()
    if body.transcription_verbatim:
        db.add(TranscriptionRevision(observation_id=obj.id,text=body.transcription_verbatim,
                                    editor=user,reason='Initial transcription'))
    audit(db,user,'observation_created','observation',obj.id,{'document_id':str(document_id)})
    db.commit()
    return {'id':str(obj.id),'created':True}


@router.get('/observations')
def observations(db:DB,q:str='',limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
    stmt=select(Observation).order_by(Observation.captured_at.desc()).limit(limit).offset(offset)
    if q:
        stmt=stmt.where(or_(Observation.person_name_verbatim.ilike('%'+q+'%'),Observation.location_verbatim.ilike('%'+q+'%'),Observation.event_type.ilike('%'+q+'%')))
    return [obj_dict(o,['id','document_id','observation_key','person_name_verbatim','surname_verbatim','given_names_verbatim','event_type','event_date_verbatim','earliest_iso','latest_iso','location_verbatim','occupation_verbatim']) for o in db.scalars(stmt)]


@router.get('/observations/{observation_id}')
def observation_detail(observation_id:UUID,db:DB):
    o=required(db,Observation,observation_id)
    return obj_dict(o,['id','document_id','observation_key','person_name_verbatim','surname_verbatim','given_names_verbatim','event_type','event_date_verbatim','earliest_iso','latest_iso','location_verbatim','occupation_verbatim','transcription_verbatim','additional_json'])


@router.post('/observations/{observation_id}/transcriptions',status_code=201,dependencies=[Depends(mutation_guard)])
def revise_transcription(observation_id:UUID,body:RevisionIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    required(db,Observation,observation_id)
    previous=db.scalar(select(TranscriptionRevision).where(TranscriptionRevision.observation_id==observation_id)
                    .order_by(TranscriptionRevision.created_at.desc(),TranscriptionRevision.id.desc()))
    if previous and previous.text==body.text:
        return {'id':str(previous.id),'created':False}
    revision=TranscriptionRevision(observation_id=observation_id,supersedes_id=previous.id if previous else None,
                                  editor=user,text=body.text,reason=body.reason,model_id=body.model_id)
    db.add(revision);db.flush()
    audit(db,user,'transcription_revised','observation',observation_id,{'revision_id':str(revision.id)})
    db.commit()
    return {'id':str(revision.id),'created':True}


@router.get('/observations/{observation_id}/transcriptions')
def transcription_history(observation_id:UUID,db:DB):
    required(db,Observation,observation_id)
    rows=db.scalars(select(TranscriptionRevision).where(TranscriptionRevision.observation_id==observation_id)
                    .order_by(TranscriptionRevision.created_at.asc())).all()
    return [obj_dict(x,['id','supersedes_id','text','editor','reason','model_id','created_at']) for x in rows]


@router.post('/observations/{observation_id}/suggest-matches',dependencies=[Depends(mutation_guard)])
def suggest_matches(observation_id:UUID,db:DB,user:Annotated[str,Depends(main.authenticate)],limit:int=Query(15,ge=1,le=50)):
    focus=required(db,Observation,observation_id)
    focus_doc=required(db,SourceDocument,focus.document_id)
    # Bound database retrieval on named candidates; fuzzy ranking applies only
    # after the SQL query, never exhaustive full-table scans.
    surname=focus.surname_verbatim.strip()
    stmt=select(Observation).where(Observation.id!=focus.id).limit(600)
    if surname:
        stmt=stmt.where(or_(Observation.surname_verbatim.ilike('%'+surname[:4]+'%'),
                            Observation.person_name_verbatim.ilike('%'+surname[:4]+'%')))
    candidates=[]
    for other in db.scalars(stmt):
        other_doc=db.get(SourceDocument,other.document_id)
        score,features,explanation=compare(focus,other,focus_doc.origin_group,other_doc.origin_group)
        if score >= 0.30:
            candidates.append((score,other,features,explanation))
    candidates.sort(key=lambda x:x[0],reverse=True)
    output=[]
    for score,other,features,explanation in candidates[:limit]:
        a,b=sorted([focus.id,other.id],key=str)
        old=db.scalar(select(IdentityCandidate).where(IdentityCandidate.observation_a_id==a,
             IdentityCandidate.observation_b_id==b))
        if old is None:
            old=IdentityCandidate(observation_a_id=a,observation_b_id=b,
                    ranking_score=score,calibrated_probability=None,algorithm='conservative-name-place-v1',
                    features_json=features,explanation=explanation)
            db.add(old)
        elif old.status=='proposed':
            old.ranking_score=score;old.features_json=features;old.explanation=explanation
        db.flush()
        output.append({'candidate_id':str(old.id),'observation_id':str(other.id),
                       'person_name_verbatim':other.person_name_verbatim,
                       'ranking_score':score,'calibrated_probability':None,
                       'calibration_status':'unscored','features':features,'explanation':explanation})
    audit(db,user,'matching_suggested','observation',observation_id,{'candidate_count':len(output)})
    db.commit()
    return {'warning':'Ranking scores are NOT probabilities or genealogical proof', 'candidates':output}


@router.get('/identity-candidates')
def identity_candidates(db:DB,limit:int=Query(50,ge=1,le=200)):
    return [obj_dict(x,['id','observation_a_id','observation_b_id','status','ranking_score',
                      'calibrated_probability','calibration_model','explanation']) for x in
            db.scalars(select(IdentityCandidate).order_by(IdentityCandidate.created_at.desc()).limit(limit))]


@router.post('/identity-candidates/{candidate_id}/review',dependencies=[Depends(mutation_guard)])
def review_candidate(candidate_id:UUID,body:DecisionIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    item=required(db,IdentityCandidate,candidate_id)
    if item.status not in ('proposed','deferred'):
        raise HTTPException(409,'Final research decision already exists')
    item.status={'accept_as_research':'research_supported','reject':'rejected','defer':'deferred'}[body.decision]
    audit(db,user,'identity_candidate_reviewed','identity_candidate',candidate_id,
          {'decision':body.decision,'reason':body.reason,'note':'Never writes to Gramps'})
    db.commit()
    return {'status':item.status,'gramps_written':False}


@router.post('/hypotheses',status_code=201,dependencies=[Depends(mutation_guard)])
def create_hypothesis(body:HypothesisIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    # All evidence and related observations must exist, preventing invented source IDs.
    needed=set()
    for opt in body.options:
        for ident in [opt.subject_observation_id,opt.related_observation_id,*opt.evidence_observation_ids]:
            if ident: needed.add(ident)
    if needed:
        have=set(db.scalars(select(Observation.id).where(Observation.id.in_(needed))))
        if have!=needed:
            raise HTTPException(422,'Unknown observation cited by hypothesis')
    obj=HypothesisSet(title=body.title,subject_description=body.subject_description,
                      relation_type=body.relation_type,created_by=user)
    db.add(obj);db.flush()
    for option in body.options:
        fields=option.model_dump(mode='json')
        fields['evidence_observation_ids']=[str(x) for x in option.evidence_observation_ids]
        db.add(HypothesisOption(hypothesis_set_id=obj.id,**fields))
    audit(db,user,'hypothesis_created','hypothesis_set',obj.id,{'options':len(body.options)})
    db.commit()
    return {'id':str(obj.id),'status':'draft','gramps_written':False}


@router.get('/hypotheses')
def hypotheses(db:DB,limit:int=Query(50,ge=1,le=200)):
    result=[]
    for group in db.scalars(select(HypothesisSet).order_by(HypothesisSet.created_at.desc()).limit(limit)):
        options=db.scalars(select(HypothesisOption).where(HypothesisOption.hypothesis_set_id==group.id)).all()
        result.append({'id':str(group.id),'title':group.title,'relation_type':group.relation_type,
                       'status':group.status,'options':[obj_dict(x,['option_key','description','is_unknown',
                       'calibrated_probability','model_id','evidence_observation_ids','reasoning']) for x in options]})
    return result


@router.post('/jobs',status_code=201,dependencies=[Depends(mutation_guard)])
def create_job(body:JobIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    if body.mode=='autonomous':
        # Persisting a planned job does NOT launch unattended web scraping or cloud API calls.
        state='paused'
    else:
        state='queued'
    job=ResearchJob(mode=body.mode,objective=body.objective,status=state,
                    cost_limit_usd=body.cost_limit_usd,created_by=user)
    db.add(job);db.flush()
    audit(db,user,'job_created','research_job',job.id,{'mode':job.mode,'status':state})
    db.commit()
    return {'id':str(job.id),'status':state,'execution_engine':'not_yet_implemented'}


@router.get('/jobs')
def jobs(db:DB):
    return [obj_dict(j,['id','mode','objective','status','progress_current',
                        'progress_total','cost_limit_usd','spent_usd','last_error']) for j in
            db.scalars(select(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(100))]


@router.post('/jobs/{job_id}/control',dependencies=[Depends(mutation_guard)])
def control_job(job_id:UUID,body:JobUpdate,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    job=required(db,ResearchJob,job_id)
    allowed={'pause':('queued','running'),'resume':('paused',),'cancel':('queued','paused','running')}
    if job.status not in allowed[body.action]:
        raise HTTPException(409,'Illegal job state transition')
    # Until worker exists, resume puts the job back into queued, NOT running.
    job.status={'pause':'paused','resume':'queued','cancel':'cancelled'}[body.action]
    audit(db,user,'job_controlled','research_job',job_id,{'action':body.action})
    db.commit()
    return {'id':str(job.id),'status':job.status,'execution_engine':'not_yet_implemented'}


@router.get('/audit')
def recent_audit(db:DB,limit:int=Query(50,ge=1,le=200)):
    return [obj_dict(x,['id','actor','action','target_type','target_id','details_json','created_at']) for x in
            db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit))]


@router.get('/gramps-compatibility')
def gramps_compatibility():
    from app.research.gramps_readonly import probe
    return probe()
