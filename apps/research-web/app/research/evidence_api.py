"""WP-014 authenticated, bounded, read-only evidence comparison API."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.evidence_comparison import dossiers, compare_dossiers

router = APIRouter(prefix='/api/v1/research/evidence', tags=['WP-014 Evidence comparison'],
                   dependencies=[Depends(main.authenticate)])
DB = Annotated[Session,Depends(session)]

class EvidenceCompareIn(BaseModel):
    observation_ids:list[UUID]=Field(min_length=2,max_length=6)

@router.get('/observations/{observation_id}/dossier')
def dossier(observation_id:UUID,db:DB):
    return dossiers(db,[observation_id])[0]

@router.post('/compare')
def compare(body:EvidenceCompareIn,db:DB):
    return compare_dossiers(db,body.observation_ids)

@router.get('/capabilities')
def capabilities():
    return {'local_image_preview_only':True,'source_image_server_fetch_enabled':False,
            'source_image_server_storage_enabled':False,'transcription_revisions_read_only':True,
            'accepted_tree_mutation_enabled':False}
