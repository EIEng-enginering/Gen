"""WP-010 conservative original-source provenance grouping.

Source documents are never merged or deleted. Groupings are human-attested
claims that different catalogue entries reproduce ONE original source, not
an assertion that two historical people are identical.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app import main
from app.research.api import audit, mutation_guard
from app.research.db import session
from app.research.models import OriginalSourceFamily, OriginalSourceMember, SourceDocument

router=APIRouter(prefix='/api/v1/research',tags=['WP-010 Source independence'],dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]


class FamilyIn(BaseModel):
    family_key:str=Field(min_length=3,max_length=180,pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]+$')
    description:str=Field(min_length=5,max_length=500)
    rationale:str=Field(min_length=15,max_length=3000)


class MemberIn(BaseModel):
    document_id:UUID
    justification:str=Field(min_length=15,max_length=3000)


class DependenceIn(BaseModel):
    document_ids:list[UUID]=Field(min_length=1,max_length=100)


@router.post('/source-families',dependencies=[Depends(mutation_guard)],status_code=201)
def create_family(body:FamilyIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    existing=db.scalar(select(OriginalSourceFamily).where(OriginalSourceFamily.family_key==body.family_key))
    if existing:
        if existing.description!=body.description or existing.rationale!=body.rationale:
            raise HTTPException(409,'Family key collision with different provenance rationale')
        return {'id':str(existing.id),'created':False}
    obj=OriginalSourceFamily(**body.model_dump(),created_by=user)
    db.add(obj);db.flush()
    audit(db,user,'source_family_created','source_family',obj.id,{'family_key':obj.family_key})
    db.commit()
    return {'id':str(obj.id),'created':True}


@router.post('/source-families/{family_id}/members',dependencies=[Depends(mutation_guard)],status_code=201)
def add_member(family_id:UUID,body:MemberIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    family=db.get(OriginalSourceFamily,family_id)
    doc=db.get(SourceDocument,body.document_id)
    if not family or not doc:
        raise HTTPException(404,'Source family or document not found')
    old=db.scalar(select(OriginalSourceMember).where(OriginalSourceMember.document_id==doc.id))
    if old:
        if old.family_id!=family_id or old.justification!=body.justification:
            raise HTTPException(409,'Document already assigned; changes require a separately reviewed correction')
        return {'id':str(old.id),'created':False}
    entry=OriginalSourceMember(family_id=family_id,document_id=doc.id,
                              justification=body.justification,created_by=user)
    db.add(entry);db.flush()
    audit(db,user,'source_family_member_added','source_document',doc.id,
          {'family_id':str(family_id),'member_id':str(entry.id)})
    db.commit()
    return {'id':str(entry.id),'created':True}


@router.get('/source-families')
def list_families(db:DB,limit:int=Query(50,ge=1,le=100)):
    rows=db.scalars(select(OriginalSourceFamily).order_by(OriginalSourceFamily.family_key).limit(limit)).all()
    return [{'id':str(x.id),'family_key':x.family_key,'description':x.description,
             'rationale':x.rationale} for x in rows]


def classification(db:Session, docs:list[SourceDocument]):
    """Conservative connected-component warnings over documentary origins.

    A manually attested grouping, exact reported origin, or identical SHA-256
    links the *evidence-source* group for double-count detection, not people.
    Never interpret separate groups as conclusively independent evidence.
    """
    doc_ids=[d.id for d in docs]
    memberships=dict(db.execute(select(OriginalSourceMember.document_id,OriginalSourceMember.family_id)
                                .where(OriginalSourceMember.document_id.in_(doc_ids))).all())
    parent={d.id:d.id for d in docs}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb:parent[max(ra,rb,key=str)]=min(ra,rb,key=str)
    seen={}
    for d in docs:
        for key in (('attested',str(memberships[d.id])) if d.id in memberships else None,
                    ('reported_origin',d.origin_group.strip().casefold()) if d.origin_group.strip() else None,
                    ('sha256',d.checksum_sha256.lower()) if d.checksum_sha256 else None):
            if key is not None:
                if key in seen:union(d.id,seen[key])
                else:seen[key]=d.id
    result={}
    for d in docs:
        root=find(d.id)
        result.setdefault(root,[]).append(d)
    out=[]
    for records in result.values():
        ids=sorted(str(d.id) for d in records)
        member_families=[memberships[d.id] for d in records if d.id in memberships]
        manual=any(member_families.count(family_id)>1 for family_id in set(member_families))
        classification_name=('contains_human_attested_shared_original' if manual else
               'possible_dependent_originals' if len(records)>1 else
               'original_relationship_unknown')
        out.append({'group_id':ids[0],'classification':classification_name,
                    'document_ids':ids})
    return sorted(out,key=lambda g:g['group_id'])


@router.post('/source-dependence/assess',dependencies=[Depends(mutation_guard)])
def assess_dependence(body:DependenceIn,db:DB):
    if len(set(body.document_ids))!=len(body.document_ids):
        raise HTTPException(422,'Duplicate input document IDs not permitted')
    docs=db.scalars(select(SourceDocument).where(SourceDocument.id.in_(body.document_ids))).all()
    if len(docs)!=len(body.document_ids):
        raise HTTPException(404,'Unknown document ID')
    groups=classification(db,docs)
    return {'document_count':len(docs),'origin_group_count':len(groups),'groups':groups,
            'independence_verified':False, 'probability_assigned':False,
            'warning':'Grouping only flags possible dependent evidence; separate documents do not prove independent originals.'}


@router.get('/documents/{document_id}/possible-copies')
def possible_copies(document_id:UUID,db:DB,limit:int=Query(25,ge=1,le=100)):
    focus=db.get(SourceDocument,document_id)
    if not focus:raise HTTPException(404,'Document not found')
    # No fuzzy bulk scan or automatic cross-provider merge.
    hints=[SourceDocument.origin_group==focus.origin_group]
    if focus.checksum_sha256: hints.append(SourceDocument.checksum_sha256==focus.checksum_sha256)
    rows=db.scalars(select(SourceDocument).where(SourceDocument.id!=document_id,or_(*hints))
                   .order_by(SourceDocument.id).limit(limit)).all()
    return {'possible_copies':[{'document_id':str(d.id),'provider':d.provider,
        'reported_origin_group_equal':d.origin_group==focus.origin_group,
        'checksum_equal':bool(focus.checksum_sha256 and focus.checksum_sha256==d.checksum_sha256)}
        for d in rows], 'automatically_merged':False,
        'warning':'These are candidates for human source-origin review, not identity matches.'}

# Cache tracking is metadata only. Actual licensed content is not stored here.
from datetime import datetime
from typing import Literal
from pydantic import field_validator
from app.research.models import SourceCacheReceipt


class CacheReceiptIn(BaseModel):
    source_document_id:UUID
    cache_key:str=Field(min_length=3,max_length=250)
    checksum_sha256:str|None=Field(default=None,pattern=r'^[0-9a-fA-F]{64}$')
    rights_basis:str=Field(min_length=5,max_length=200)
    acquisition_method:Literal['user_import','approved_api','licensed_dataset']
    expires_at:datetime|None=None


@router.post('/source-cache-receipts',dependencies=[Depends(mutation_guard)],status_code=201)
def create_cache_receipt(body:CacheReceiptIn,db:DB,user:Annotated[str,Depends(main.authenticate)]):
    doc=db.get(SourceDocument,body.source_document_id)
    if not doc:raise HTTPException(404,'Registered source document is required')
    if body.acquisition_method!=doc.access_method:
        raise HTTPException(422,'Cache acquisition must match the document access method')
    if doc.checksum_sha256 and body.checksum_sha256 and doc.checksum_sha256.lower()!=body.checksum_sha256.lower():
        raise HTTPException(409,'Cache checksum differs from immutable source record')
    prior=db.scalar(select(SourceCacheReceipt).where(SourceCacheReceipt.cache_key==body.cache_key))
    values=body.model_dump()
    if prior:
        if any(getattr(prior,k)!=v for k,v in values.items()):
            raise HTTPException(409,'Cache key collision; add a new receipt for a changed source')
        return {'id':str(prior.id),'created':False}
    receipt=SourceCacheReceipt(**values,stored_by=user)
    db.add(receipt);db.flush()
    audit(db,user,'source_cache_receipt_created','source_cache_receipt',receipt.id,
          {'source_document_id':str(doc.id)})
    db.commit()
    return {'id':str(receipt.id),'created':True}


@router.get('/source-cache-receipts')
def cache_receipts(source_document_id:UUID,db:DB,limit:int=Query(25,ge=1,le=100)):
    if not db.get(SourceDocument,source_document_id):raise HTTPException(404,'Source not found')
    rows=db.scalars(select(SourceCacheReceipt).where(SourceCacheReceipt.source_document_id==source_document_id)
                    .order_by(SourceCacheReceipt.created_at.desc()).limit(limit)).all()
    return [{'id':str(r.id),'cache_key':r.cache_key,'checksum_sha256':r.checksum_sha256,
             'acquisition_method':r.acquisition_method,'rights_basis':r.rights_basis,
             'expires_at':r.expires_at.isoformat() if r.expires_at else None}
            for r in rows]
