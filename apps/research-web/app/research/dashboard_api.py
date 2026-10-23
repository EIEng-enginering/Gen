"""WP-016 authenticated operational summaries and review queue."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.ops_dashboard import overview, review_queue, job_detail

router=APIRouter(prefix='/api/v1/research/ops',tags=['WP-016 Operations'],
                 dependencies=[Depends(main.authenticate)])
DB=Annotated[Session,Depends(session)]

@router.get('/dashboard')
def dashboard(db:DB):return overview(db)

@router.get('/reviews')
def pending_reviews(db:DB,limit:int=Query(default=50,ge=1,le=100)):
    return review_queue(db,limit)

@router.get('/jobs/{job_id}')
def job_status(job_id:UUID,db:DB):return job_detail(db,job_id)
