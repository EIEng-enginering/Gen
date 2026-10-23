"""WP-008 local-only offline Gramps contract and read-only plan readiness API."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.gramps_contract import inspect_openapi, plan_readiness
from app.research.gramps_live_read_api import _approved_current
from app.research.models import GrampsChangePlan, GrampsPlanDecision, GrampsReadValidation

router = APIRouter(prefix='/api/v1/research/gramps', tags=['WP-008 Gramps contract (non-writing)'],
                   dependencies=[Depends(main.authenticate)])
DB = Annotated[Session, Depends(session)]


@router.post('/contracts/review')
async def review_contract(request: Request):
    # This never proxies URLs or sends tokens to any service. It accepts a manually
    # exported schema only, capped independently of Content-Length.
    total = 0
    parts = []
    async for chunk in request.stream():
        total += len(chunk)
        if total > 1024 * 1024:
            raise HTTPException(413, 'OpenAPI export too large')
        parts.append(chunk)
    try:
        import json
        doc = json.loads(b''.join(parts))
        return inspect_openapi(doc)
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(422, 'Invalid or unsupported OpenAPI export') from None


@router.get('/plans/{plan_id}/execution-readiness')
def execution_readiness(plan_id: UUID, db: DB):
    plan = db.get(GrampsChangePlan, plan_id)
    if plan is None:
        raise HTTPException(404, 'Plan not found')
    decision = db.scalar(select(GrampsPlanDecision).where(GrampsPlanDecision.plan_id == plan.id))
    validation = db.scalar(select(GrampsReadValidation).where(GrampsReadValidation.plan_id == plan.id)
        .order_by(GrampsReadValidation.created_at.desc(), GrampsReadValidation.id.desc()).limit(1))
    try:
        _approved_current(db, plan)
        current = True
    except HTTPException:
        current = False
    return plan_readiness(plan, decision, validation, current=current)


@router.get('/execution-policy')
def execution_policy():
    return {'write_adapter_installed': False, 'accepted_tree_mutation_enabled': False,
            'supported_actions': ['preview', 'approve_for_future_validation', 'read_only_validation'],
            'forbidden_actions': ['create_family', 'update_person', 'merge_person', 'accepted_tree_write'],
            'required_live_gates': ['instance_specific_openapi_review', 'authenticated_read_shape_checks',
                                    'immutable_image_version_lock', 'recovery_verified',
                                    'upstream_concurrency_strategy'],
            'note': 'This API provides NO route that can commit genealogical changes to Gramps'}
