"""WP-006 Gramps proposal preview and human approval, deliberately NO WRITE adapter.

This module never sends POST/PUT/PATCH/DELETE to Gramps. Approval is permission
for a future separate *validation* phase, not permission to execute an edit.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import main
from app.research.db import session
from app.research.api import mutation_guard, audit
from app.research.graph_api import get_group_option, latest
from app.research.models import (HypothesisSet, BranchEdge, BranchReview,
                                 GrampsChangePlan, GrampsPlanDecision)
from app.research.gramps_plan import build_preview
from app.research.gramps_plan_schemas import PlanPreviewIn, PlanCreateIn, PlanApprovalIn
from app.research.gramps_readonly import probe

DB = Annotated[Session, Depends(session)]
router = APIRouter(prefix='/api/v1/research/gramps', tags=['Gramps change proposals (no writes)'],
                   dependencies=[Depends(main.authenticate)])


def _preview(body, db):
    group, option = get_group_option(db, body.hypothesis_set_id, body.option_key)
    if group.status != 'draft' or group.version != body.expected_set_version:
        raise HTTPException(409, 'Stale or non-editable research set; refresh before proceeding')
    current = latest(db, option.id)
    if current is None or current.id != body.expected_revision_id:
        raise HTTPException(409, 'Branch revision changed; re-review the latest revision')
    edges = db.scalars(select(BranchEdge).where(BranchEdge.revision_id == current.id)
                       .order_by(BranchEdge.edge_key)).all()
    try:
        return build_preview(group, option, current, edges, body.bindings)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _review_supported(db, revision_id):
    review = db.scalar(select(BranchReview).where(BranchReview.revision_id == revision_id)
                       .order_by(BranchReview.created_at.desc(), BranchReview.id.desc()).limit(1))
    if review is None or review.decision != 'research_supported':
        raise HTTPException(409, 'A current research_supported branch review is required before a plan can be recorded')


def _result(plan, decision=None):
    return {
        'id': str(plan.id), 'idempotency_key': plan.idempotency_key,
        'digest_sha256': plan.digest_sha256, 'hypothesis_set_id': str(plan.hypothesis_set_id),
        'branch_revision_id': str(plan.branch_revision_id),
        'set_version_after_creation': plan.set_version_after_creation,
        'created_by': plan.created_by, 'created_at': plan.created_at.isoformat(),
        'operator_note': plan.operator_note, 'preview': plan.preview_json,
        'decision': None if decision is None else {
            'decision': decision.decision, 'reviewer': decision.reviewer,
            'rationale': decision.rationale, 'created_at': decision.created_at.isoformat()},
        'upstream_validation': 'NOT_PERFORMED', 'accepted_tree_write': False,
        'execution_enabled': False,
    }


@router.get('/compatibility')
def compatibility():
    result = probe()
    result['accepted_tree_write_enabled'] = False
    result['note'] = 'Read-only API metadata probe; no accepted-tree objects have been modified'
    return result


@router.post('/plans/preview', dependencies=[Depends(mutation_guard)])
def preview_change(body: PlanPreviewIn, db: DB):
    return _preview(body, db)


@router.post('/plans', status_code=201, dependencies=[Depends(mutation_guard)])
def create_plan(body: PlanCreateIn, db: DB, actor: Annotated[str, Depends(main.authenticate)]):
    old = db.scalar(select(GrampsChangePlan).where(GrampsChangePlan.idempotency_key == body.idempotency_key))
    if old is not None:
        snapshot = old.preview_json
        mappings = {a['edge_key']: (a['from_handle_claimed'], a['to_handle_claimed']) for a in snapshot['actions']}
        submitted = {b.edge_key: (b.from_handle,b.to_handle) for b in body.bindings}
        if (old.hypothesis_set_id != body.hypothesis_set_id or
                old.branch_revision_id != body.expected_revision_id or
                snapshot['option_key'] != body.option_key or
                snapshot['set_version'] != body.expected_set_version or
                old.digest_sha256 != body.expected_preview_digest or
                old.operator_note != body.operator_note or mappings != submitted):
            raise HTTPException(409, 'Idempotency key reused for a different change plan')
        decision = db.scalar(select(GrampsPlanDecision).where(GrampsPlanDecision.plan_id == old.id))
        return _result(old, decision)
    result = _preview(body, db)
    if result['digest_sha256'] != body.expected_preview_digest:
        raise HTTPException(409, 'Preview digest mismatch; generate a fresh preview')
    _review_supported(db, body.expected_revision_id)
    group, option = get_group_option(db, body.hypothesis_set_id, body.option_key)
    # Serialize the approval-planning decision with all graph edits and reviews.
    changed = db.execute(update(HypothesisSet).where(HypothesisSet.id == group.id,
                         HypothesisSet.version == body.expected_set_version,
                         HypothesisSet.status == 'draft').values(version=HypothesisSet.version + 1))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Concurrent change; reload the research set')
    plan = GrampsChangePlan(idempotency_key=body.idempotency_key,
                            hypothesis_set_id=group.id, option_id=option.id,
                            branch_revision_id=body.expected_revision_id,
                            set_version_after_creation=body.expected_set_version + 1,
                            digest_sha256=result['digest_sha256'], preview_json=result,
                            operator_note=body.operator_note, created_by=actor)
    db.add(plan)
    db.flush()
    audit(db, actor, 'gramps_plan_created_no_write', 'gramps_change_plan', plan.id,
          {'digest': plan.digest_sha256, 'revision_id': str(body.expected_revision_id),
           'accepted_tree_write': False})
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, 'Concurrent idempotency conflict; retry with the existing plan key') from exc
    return _result(plan)


@router.get('/plans/{plan_id}')
def get_plan(plan_id: UUID, db: DB):
    plan = db.get(GrampsChangePlan, plan_id)
    if plan is None:
        raise HTTPException(404, 'Plan not found')
    decision = db.scalar(select(GrampsPlanDecision).where(GrampsPlanDecision.plan_id == plan.id))
    return _result(plan, decision)


@router.post('/plans/{plan_id}/decisions', status_code=201, dependencies=[Depends(mutation_guard)])
def decide(plan_id: UUID, body: PlanApprovalIn, db: DB,
           actor: Annotated[str, Depends(main.authenticate)]):
    plan = db.get(GrampsChangePlan, plan_id)
    if plan is None:
        raise HTTPException(404, 'Plan not found')
    if db.scalar(select(GrampsPlanDecision.id).where(GrampsPlanDecision.plan_id == plan.id)):
        raise HTTPException(409, 'Plan already has a recorded human decision')
    group = db.get(HypothesisSet, plan.hypothesis_set_id)
    if (group is None or group.status != 'draft' or group.version != plan.set_version_after_creation
            or body.expected_set_version != group.version):
        raise HTTPException(409, 'Research tree changed after plan creation; make a new preview')
    if latest(db,plan.option_id).id != plan.branch_revision_id:
        raise HTTPException(409, 'Provisional branch revision is stale')
    _review_supported(db, plan.branch_revision_id)
    if body.expected_preview_digest != plan.digest_sha256:
        raise HTTPException(409, 'Digest mismatch')
    phrase = ('APPROVE PLAN ' if body.decision == 'approve_for_future_validation' else 'REJECT PLAN ')
    if body.confirmation != phrase + plan.digest_sha256[:12]:
        raise HTTPException(422, 'Confirmation phrase must contain this plan digest')
    claim = db.execute(update(HypothesisSet).where(HypothesisSet.id == group.id,
                       HypothesisSet.version == body.expected_set_version,
                       HypothesisSet.status == 'draft').values(version=HypothesisSet.version + 1))
    if claim.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Concurrent change; reload and reconsider the plan')
    decision = GrampsPlanDecision(plan_id=plan.id, decision=body.decision,
                                  reviewer=actor, rationale=body.rationale)
    db.add(decision)
    db.flush()
    audit(db, actor, 'gramps_plan_decision_no_write', 'gramps_change_plan', plan.id,
          {'decision': body.decision, 'digest': plan.digest_sha256,
           'accepted_tree_write': False})
    db.commit()
    return {'plan_id': str(plan.id), 'decision_id': str(decision.id),
            'decision': decision.decision, 'reviewer': actor,
            'accepted_tree_write': False, 'execution_enabled': False,
            'next_step': 'Live Gramps preflight, actual API contract, database backup and safe execution design required'}
