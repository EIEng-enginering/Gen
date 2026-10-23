"""WP-007 authenticated local read-only Gramps preflight, no accepted-tree edits."""
from typing import Annotated
import hashlib
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import main
from app.research.api import mutation_guard, audit
from app.research.db import session
from app.research.graph_api import latest
from app.research.gramps_live_read import read_plan_snapshot, UpstreamBlocked
from app.research.models import (GrampsChangePlan, GrampsPlanDecision,
                                  GrampsReadValidation, HypothesisSet, BranchReview)

DB = Annotated[Session, Depends(session)]
router = APIRouter(prefix='/api/v1/research/gramps', tags=['Gramps GET-only live validation'],
                   dependencies=[Depends(main.authenticate)])


def _approved_current(db, plan):
    decision = db.scalar(select(GrampsPlanDecision).where(GrampsPlanDecision.plan_id == plan.id))
    if decision is None or decision.decision != 'approve_for_future_validation':
        raise HTTPException(409, 'Human-approved research plan required for live validation')
    group = db.get(HypothesisSet, plan.hypothesis_set_id)
    if (group is None or group.status != 'draft' or
        group.version != plan.set_version_after_creation + 1):
        raise HTTPException(409, 'Research set changed; regenerate a new plan')
    current = latest(db, plan.option_id)
    if current is None or current.id != plan.branch_revision_id:
        raise HTTPException(409, 'Branch revision is no longer current')
    review = db.scalar(select(BranchReview).where(BranchReview.revision_id == current.id)
                       .order_by(BranchReview.created_at.desc(), BranchReview.id.desc()).limit(1))
    if review is None or review.decision != 'research_supported':
        raise HTTPException(409, 'Research review is no longer supportive')
    payload = dict(plan.preview_json)
    stored_digest = payload.pop('digest_sha256', None)
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    computed_digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    if stored_digest != plan.digest_sha256 or computed_digest != plan.digest_sha256:
        raise HTTPException(409, 'Stored plan digest is inconsistent')


@router.post('/plans/{plan_id}/read-validate', dependencies=[Depends(mutation_guard)])
def validate_plan_read_only(plan_id: UUID, db: DB,
                            actor: Annotated[str, Depends(main.authenticate)]):
    plan = db.get(GrampsChangePlan, plan_id)
    if plan is None:
        raise HTTPException(404, 'Plan not found')
    _approved_current(db, plan)
    try:
        result = read_plan_snapshot(plan.preview_json)
    except UpstreamBlocked as exc:
        # Never relay transport details, credentials or private Gramps metadata.
        raise HTTPException(503, {'code':exc.code, 'accepted_tree_write':False}) from None
    entry = GrampsReadValidation(plan_id=plan.id, plan_digest=plan.digest_sha256,
                                 checked_by=actor, result_json=result)
    db.add(entry)
    db.flush()
    audit(db, actor, 'gramps_read_only_validation', 'gramps_change_plan', plan.id,
          {'validation_id':str(entry.id), 'snapshot_sha256':result['snapshot_sha256'],
           'accepted_tree_write':False})
    db.commit()
    return {'validation_id':str(entry.id), **result}


@router.get('/plans/{plan_id}/read-validations')
def list_plan_validations(plan_id: UUID, db: DB):
    if db.get(GrampsChangePlan, plan_id) is None:
        raise HTTPException(404, 'Plan not found')
    rows = db.scalars(select(GrampsReadValidation).where(GrampsReadValidation.plan_id == plan_id)
                      .order_by(GrampsReadValidation.created_at.desc(), GrampsReadValidation.id.desc())
                      .limit(25)).all()
    return [{'id':str(row.id), 'checked_at':row.created_at.isoformat(),
             'plan_digest':row.plan_digest,
             **row.result_json} for row in rows]
