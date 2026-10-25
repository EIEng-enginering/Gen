"""Authenticated, bounded, review-before-import source intake APIs. No provider requests."""
import hashlib
import json
from datetime import datetime,timezone
import re
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import main
from .api import DB,mutation_guard,audit
from .models import Observation,SourceDocument,TranscriptionRevision
from .acquisition_models import AcquisitionBatch,StagedEvidence,StagedPersonLink
from .acquisition_core import IntakeRequest,IntakeRecord,PROVIDER_POLICIES,make_prompt

router=APIRouter(prefix='/api/v1/research/acquisition',tags=['Evidence acquisition'],dependencies=[Depends(main.authenticate)])

class PromptRequest(BaseModel):
    surname: str=Field(min_length=2,max_length=100)
    county: str=Field(min_length=2,max_length=140)
    year_start:int=Field(ge=1500,le=2026)
    year_end:int=Field(ge=1500,le=2026)
    mode:str='guided'
    max_records:int=Field(default=40,ge=1,le=100)
    record_types:list[str]=Field(default_factory=list,max_length=8)

class ReviewRequest(BaseModel):
    decision: str=Field(pattern=r'^(import_verified|reject|defer)$')
    rationale:str=Field(min_length=12,max_length=1800)
    independently_checked:bool=False

class PersonLinkRequest(BaseModel):
    gramps_handle:str=Field(min_length=2,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    rationale:str=Field(min_length=12,max_length=1000)

@router.get('/provider-policies')
def policies():
    return {'advisory_only':True,'provider_execution_enabled':False,'policies':PROVIDER_POLICIES}

@router.post('/prompt',dependencies=[Depends(mutation_guard)])
def build_prompt(body:PromptRequest):
    try:
        text=make_prompt(body.surname,body.county,body.year_start,body.year_end,body.mode,body.max_records,body.record_types or None)
    except ValueError as err:raise HTTPException(422,str(err))
    return {'prompt':text,'model_independent':True,'external_requests_executed':0,
            'instructions':'Copy prompt into a chatbot you choose. Save only legally retainable JSONL results. Validate each entry before import.'}

@router.post('/batches',status_code=201,dependencies=[Depends(mutation_guard)])
def stage(body:IntakeRequest,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    old=db.scalar(select(AcquisitionBatch).where(AcquisitionBatch.batch_key==body.batch_key))
    hashes=[r.sha256() for r in body.records]
    if old:
        old_rows=db.scalars(select(StagedEvidence).where(StagedEvidence.batch_id==old.id).order_by(StagedEvidence.row_number)).all()
        if old.created_by!=user or old.input_kind!=body.input_kind or old.row_count!=len(hashes) or [x.sha256 for x in old_rows]!=hashes:
            raise HTTPException(409,'Batch key reused with different content or operator')
        return {'batch_id':str(old.id),'created':False,'received':old.row_count,'promoted':sum(x.status=='imported' for x in old_rows)}
    # Strict validation is performed before a DB write; a model cannot silently insert accepted observations.
    batch=AcquisitionBatch(batch_key=body.batch_key,input_kind=body.input_kind,
            created_by=user,rights_attested=1,row_count=len(hashes))
    db.add(batch)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Concurrent batch insertion; verify the existing batch key') from None
    for index,(rec,sha) in enumerate(zip(body.records,hashes),start=1):
        db.add(StagedEvidence(batch_id=batch.id,row_number=index,sha256=sha,payload=rec.canonical_dict(),
             surname_key=rec.surname_verbatim.casefold()[:160],
             place_key=rec.location_verbatim.casefold()[:200],
             year_hint=(int(re.search(r'(?<!\d)(?:1[5-9]\d{2}|20[0-2]\d)(?!\d)',rec.event_date_verbatim).group())
                  if re.search(r'(?<!\d)(?:1[5-9]\d{2}|20[0-2]\d)(?!\d)',rec.event_date_verbatim) else None),
             status='awaiting_human_review',reason='Not verified against original source'))
    audit(db,user,'acquisition_staged','acquisition_batch',batch.id,{'rows':len(hashes),'input_kind':body.input_kind})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Concurrent batch insertion; verify the existing batch key')
    return {'batch_id':str(batch.id),'created':True,'received':batch.row_count,'imported':0,
            'note':'All data quarantined; no accepted Gramps objects or verified research observations created.'}

@router.get('/batches')
def batches(db:DB,limit:int=Query(30,ge=1,le=100)):
    items=db.scalars(select(AcquisitionBatch).order_by(AcquisitionBatch.created_at.desc()).limit(limit)).all()
    return [{'id':str(x.id),'batch_key':x.batch_key,'input_kind':x.input_kind,'received':x.row_count,'created_at':x.created_at.isoformat()} for x in items]

@router.get('/batches/{batch_id}/rows')
def batch_rows(batch_id:UUID,db:DB,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0)):
    if not db.get(AcquisitionBatch,batch_id):raise HTTPException(404,'Batch not found')
    rows=db.scalars(select(StagedEvidence).where(StagedEvidence.batch_id==batch_id).order_by(StagedEvidence.row_number).limit(limit).offset(offset)).all()
    return [{'id':str(x.id),'row_number':x.row_number,'status':x.status,'payload':x.payload,'sha256':x.sha256,'reason':x.reason,'import_observation_id':str(x.import_observation_id) if x.import_observation_id else None} for x in rows]

@router.post('/rows/{row_id}/review',dependencies=[Depends(mutation_guard)])
def review(row_id:UUID,body:ReviewRequest,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    staged=db.scalar(select(StagedEvidence).where(StagedEvidence.id==row_id).with_for_update())
    if not staged:raise HTTPException(404,'Staged record not found')
    if staged.status in ('imported','rejected'):
        raise HTTPException(409,'Final decision already recorded')
    if body.decision in ('reject','defer'):
        staged.status={'reject':'rejected','defer':'deferred'}[body.decision]
        staged.reason=body.rationale;staged.reviewed_by=user;staged.reviewed_at=datetime.now(timezone.utc)
        audit(db,user,'staged_record_'+staged.status,'staged_evidence',staged.id,{'reason':body.rationale[:150]})
        db.commit()
        return {'status':staged.status,'gramps_written':False}
    if not body.independently_checked:
        raise HTTPException(422,'Human confirmation of exact original source required before import')
    rec=IntakeRecord.model_validate(staged.payload)
    if rec.extraction_status=='lead_only' or rec.record_type=='catalogue_lead':
        raise HTTPException(422,'Catalogue/search leads cannot become source observations')
    # The staged source_viewed field is untrusted. independently_checked is a
    # fresh operator attestation given after inspecting the retained source.
    existing_doc=db.scalar(select(SourceDocument).where(SourceDocument.provider==rec.provider,
                     SourceDocument.provider_record_id==rec.provider_record_id))
    if existing_doc:
        expected=(rec.source_title,rec.source_reference,rec.origin_group,rec.licence,rec.access_method)
        actual=(existing_doc.title,existing_doc.reference,existing_doc.origin_group,existing_doc.licence,existing_doc.access_method)
        if expected!=actual:raise HTTPException(409,'Source identifier collision with different provenance')
        doc=existing_doc
    else:
        doc=SourceDocument(provider=rec.provider,provider_record_id=rec.provider_record_id,
            title=rec.source_title,reference=rec.source_reference,original_url=rec.source_url,
            access_method=rec.access_method,licence=rec.licence,rights_note=rec.rights_note,
            acquisition_operator=user,origin_group=rec.origin_group,document_kind=rec.record_type,
            source_class=rec.source_class,metadata_json={'import_batch':str(staged.batch_id),
               'permission_reference':rec.permission_reference,
               'operator_source_check_attested':True,
               'original_source_independence_verified':False})
        db.add(doc);db.flush()
    old=db.scalar(select(Observation).where(Observation.document_id==doc.id,Observation.observation_key==rec.record_entry_key))
    fields={'event_type':rec.record_type,'person_name_verbatim':rec.person_name_verbatim,
        'surname_verbatim':rec.surname_verbatim,'given_names_verbatim':rec.given_names_verbatim,
        'event_date_verbatim':rec.event_date_verbatim,'earliest_iso':str(rec.earliest_iso) if rec.earliest_iso else None,
        'latest_iso':str(rec.latest_iso) if rec.latest_iso else None,
        'location_verbatim':rec.location_verbatim,'occupation_verbatim':rec.occupation_verbatim,
        'transcription_verbatim':rec.transcription_verbatim,
        'additional_json':{'intake_sha256':staged.sha256,'review':body.rationale,'ai_extraction_status':rec.extraction_status}}
    if old:
        # Compare immutable genealogy attributes, not review/batch metadata.
        for k in ('event_type','person_name_verbatim','surname_verbatim','given_names_verbatim','event_date_verbatim','earliest_iso','latest_iso','location_verbatim','occupation_verbatim','transcription_verbatim'):
            if getattr(old,k)!=fields[k]:raise HTTPException(409,'Existing observation differs; do not overwrite; use transcription revisions')
        obj=old
    else:
        obj=Observation(document_id=doc.id,observation_key=rec.record_entry_key,**fields)
        db.add(obj);db.flush()
        if rec.transcription_verbatim:
            db.add(TranscriptionRevision(observation_id=obj.id,text=rec.transcription_verbatim,editor=user,
                    reason='Human reviewed external record extraction'))
    staged.import_document_id=doc.id;staged.import_observation_id=obj.id;staged.status='imported'
    staged.reason=body.rationale;staged.reviewed_by=user;staged.reviewed_at=datetime.now(timezone.utc)
    audit(db,user,'staged_record_imported','staged_evidence',staged.id,
          {'document_id':str(doc.id),'observation_id':str(obj.id),'gramps_written':False})
    db.commit()
    return {'status':'imported','source_document_id':str(doc.id),'observation_id':str(obj.id),
            'accepted_tree_mutation':False,'review':'verified_by_operator_not_independent_genealogical_proof'}

@router.post('/rows/{row_id}/proposed-person-link',dependencies=[Depends(mutation_guard)])
def propose_person_link(row_id:UUID,body:PersonLinkRequest,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    staged=db.get(StagedEvidence,row_id)
    if not staged or staged.status!='imported':raise HTTPException(409,'Only reviewed imported evidence can be proposed for linkage')
    link=StagedPersonLink(staged_id=staged.id,gramps_handle=body.gramps_handle,rationale=body.rationale,
                          created_by=user,status='proposed')
    db.add(link);db.flush()
    audit(db,user,'provisional_gramps_person_link','staged_person_link',link.id,
          {'accepted_tree_mutation':False})
    db.commit()
    return {'id':str(link.id),'status':'proposed','gramps_written':False,'gramps_handle_verified':False}

@router.get('/stats')
def intake_stats(db:DB):
    result={'batches':db.scalar(select(func.count()).select_from(AcquisitionBatch))}
    for status in ('awaiting_human_review','deferred','rejected','imported'):
        result[status]=db.scalar(select(func.count()).select_from(StagedEvidence).where(StagedEvidence.status==status))
    result['external_sites_contacted']=0
    result['gramps_writes_enabled']=False
    return result

@router.get('/leads')
def staged_search(db:DB,surname:str=Query(min_length=2,max_length=100),
                  year_start:int|None=Query(default=None,ge=1500,le=2026),
                  year_end:int|None=Query(default=None,ge=1500,le=2026),
                  limit:int=Query(default=30,ge=1,le=100)):
    """Read bounded, unverified staging leads; never confirms identity or proof."""
    if year_start and year_end and year_start>year_end:
        raise HTTPException(422,'Invalid year range')
    query=select(StagedEvidence).where(StagedEvidence.surname_key==surname.casefold()).order_by(StagedEvidence.id).limit(limit)
    if year_start:query=query.where(StagedEvidence.year_hint>=year_start)
    if year_end:query=query.where(StagedEvidence.year_hint<=year_end)
    rows=db.scalars(query).all()
    return {'selection_is_exhaustive':False,'calibrated_probability':None,
            'candidates':[{'id':str(x.id),'status':x.status,
              'surname':x.payload.get('surname_verbatim'),'person_name':x.payload.get('person_name_verbatim'),
              'year_hint':x.year_hint,'place':x.payload.get('location_verbatim'),
              'source_reference':x.payload.get('source_reference')}
                for x in rows]}
