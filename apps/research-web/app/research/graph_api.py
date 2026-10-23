"""WP-005 append-only, competing-branch API. No accepted-tree writes.

The optimistic version check is enforced inside the database UPDATE transaction.
Researchers may support a hypothesis *as research*; never automatically merge it
into the authoritative Gramps tree.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app import main
from app.research.api import mutation_guard, audit
from app.research.db import session
from app.research.models import (HypothesisSet, HypothesisOption, Observation, SourceDocument,
                                  BranchRevision, BranchEdge, BranchReview)
from app.research.graph_schemas import RevisionIn, BranchReviewIn
from app.research.graph import canonical_edge, validate_topology, assessment, compare_options

DB = Annotated[Session, Depends(session)]
router = APIRouter(prefix='/api/v1/research', tags=['Research graph (provisional)'],
                   dependencies=[Depends(main.authenticate)])


def get_group_option(db, group_id, key):
    group = db.get(HypothesisSet, group_id)
    if group is None:
        raise HTTPException(404, 'Hypothesis set not found')
    option = db.scalar(select(HypothesisOption).where(HypothesisOption.hypothesis_set_id == group_id,
                                                     HypothesisOption.option_key == key))
    if option is None:
        raise HTTPException(404, 'Hypothesis option not found')
    return group, option


def latest(db, option_id):
    return db.scalar(select(BranchRevision).where(BranchRevision.option_id == option_id)
                     .order_by(BranchRevision.revision_number.desc()).limit(1))


def representation(db, revision):
    if not revision:
        return None
    edges = db.scalars(select(BranchEdge).where(BranchEdge.revision_id == revision.id)
                       .order_by(BranchEdge.edge_key)).all()
    evidence = {UUID(str(x)) for e in edges for x in [e.from_observation_id, e.to_observation_id,
                  *e.supporting_observation_ids, *e.contradicting_observation_ids]}
    observations = {str(o.id): o for o in db.scalars(select(Observation).where(Observation.id.in_(evidence)))} if evidence else {}
    docs = {str(d.id): d for d in db.scalars(select(SourceDocument).where(SourceDocument.id.in_(
        {o.document_id for o in observations.values()})))} if observations else {}
    result = []
    for e in edges:
        result.append({'edge_key': e.edge_key, 'from_observation_id': str(e.from_observation_id),
                       'to_observation_id': str(e.to_observation_id),
                       'relationship_type': e.relationship_type,
                       'supporting_observation_ids': list(e.supporting_observation_ids),
                       'contradicting_observation_ids': list(e.contradicting_observation_ids),
                       'reasoning': e.reasoning,
                       'canonical': list(canonical_edge(e))})
    return {'id': str(revision.id), 'revision_number': revision.revision_number,
            'rationale': revision.rationale, 'created_by': revision.created_by,
            'created_at': revision.created_at.isoformat(), 'edges': result,
            'assessment': assessment(edges, observations, docs),
            'gramps_written': False}


@router.post('/hypotheses/{group_id}/options/{option_key}/revisions',status_code=201,
             dependencies=[Depends(mutation_guard)])
def add_revision(group_id: UUID, option_key: str, body: RevisionIn, db: DB,
                 user: Annotated[str, Depends(main.authenticate)]):
    group, option = get_group_option(db, group_id, option_key)
    if group.status != 'draft':
        raise HTTPException(409, 'Only draft hypothesis sets can be revised')
    if option.is_unknown and body.edges:
        raise HTTPException(422, 'Unknown/other option must have no asserted family edges')
    if not option.is_unknown and not body.edges:
        raise HTTPException(422, 'Named alternative needs at least one explicit edge')
    try:
        validate_topology(body.edges)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    referenced = {v for edge in body.edges for v in [edge.from_observation_id,edge.to_observation_id,
                   *edge.supporting_observation_ids,*edge.contradicting_observation_ids]}
    if referenced:
        found = set(db.scalars(select(Observation.id).where(Observation.id.in_(referenced))))
        if referenced != found:
            raise HTTPException(422, 'Branch references unregistered historical observations')
    # Atomic row version claim: concurrent proposals cannot overwrite each other.
    changed = db.execute(update(HypothesisSet).where(HypothesisSet.id == group_id,
                        HypothesisSet.version == body.expected_set_version,
                        HypothesisSet.status == 'draft').values(version=HypothesisSet.version+1))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Hypothesis set changed; refresh version before editing')
    previous = latest(db, option.id)
    new = BranchRevision(hypothesis_set_id=group.id, option_id=option.id,
                         revision_number=1 if previous is None else previous.revision_number+1,
                         rationale=body.rationale, created_by=user)
    db.add(new); db.flush()
    for e in body.edges:
        db.add(BranchEdge(revision_id=new.id, edge_key=e.edge_key,
                          from_observation_id=e.from_observation_id,
                          to_observation_id=e.to_observation_id,
                          relationship_type=e.relationship_type,
                          supporting_observation_ids=[str(v) for v in e.supporting_observation_ids],
                          contradicting_observation_ids=[str(v) for v in e.contradicting_observation_ids],
                          reasoning=e.reasoning))
    db.flush()
    audit(db, user, 'branch_revision_created', 'branch_revision', new.id,
          {'set_id': str(group_id), 'option_key': option_key, 'number': new.revision_number,
           'edge_count': len(body.edges), 'gramps_written': False})
    db.commit()
    return {'revision_id': str(new.id), 'revision_number': new.revision_number,
            'set_version': body.expected_set_version+1, 'gramps_written': False,
            'calibration_status': 'unscored'}


@router.get('/hypotheses/{group_id}/graph')
def hypothesis_graph(group_id: UUID, db: DB):
    group = db.get(HypothesisSet, group_id)
    if group is None:
        raise HTTPException(404, 'Hypothesis set not found')
    options = db.scalars(select(HypothesisOption).where(HypothesisOption.hypothesis_set_id == group_id)
                         .order_by(HypothesisOption.option_key)).all()
    result = []
    for option in options:
        version = latest(db, option.id)
        branch = representation(db, version)
        result.append({'option_key': option.option_key, 'description': option.description,
                       'is_unknown': bool(option.is_unknown), 'revision': branch,
                       'edges': branch['edges'] if branch else []})
    return {'hypothesis_set_id': str(group.id), 'title': group.title,
            'version': group.version, 'status': group.status, 'options': result,
            'comparison': compare_options(result),
            'calibrated_probabilities': None, 'gramps_written': False,
            'warning': 'Options are unscored evidence hypotheses, not probabilistic family trees'}


@router.get('/hypotheses/{group_id}/options/{option_key}/revisions')
def revisions(group_id: UUID, option_key: str, db: DB, limit: int = Query(30,ge=1,le=100)):
    _, option = get_group_option(db,group_id,option_key)
    rows = db.scalars(select(BranchRevision).where(BranchRevision.option_id == option.id)
                      .order_by(BranchRevision.revision_number.desc()).limit(limit)).all()
    return [representation(db, row) for row in rows]


@router.post('/hypotheses/{group_id}/options/{option_key}/reviews',status_code=201,
             dependencies=[Depends(mutation_guard)])
def review_branch(group_id: UUID,option_key: str,body: BranchReviewIn,db: DB,
                  user: Annotated[str,Depends(main.authenticate)]):
    group, option = get_group_option(db,group_id,option_key)
    if group.version != body.expected_set_version:
        raise HTTPException(409,'Hypothesis set changed before research review')
    current = latest(db,option.id)
    if current is None:
        raise HTTPException(409,'Create a branch revision before reviewing it')
    preceding = db.scalar(select(BranchReview).where(BranchReview.revision_id == current.id)
                          .order_by(BranchReview.created_at.desc(), BranchReview.id.desc()).limit(1))
    if preceding and preceding.decision != 'deferred':
        raise HTTPException(409,'This revision was already reviewed; create a new revision')
    # Single optimistic set-version transaction, serializing competing reviews.
    claimed = db.execute(update(HypothesisSet).where(HypothesisSet.id == group.id,
                         HypothesisSet.version == body.expected_set_version)
                         .values(version=HypothesisSet.version+1))
    if claimed.rowcount != 1:
        db.rollback();raise HTTPException(409,'Concurrent review conflict; reload')
    review = BranchReview(revision_id=current.id,decision=body.decision,reason=body.reason,reviewer=user)
    db.add(review);db.flush()
    audit(db,user,'branch_research_reviewed','branch_revision',current.id,
          {'decision':body.decision, 'reason':body.reason, 'gramps_written':False})
    db.commit()
    return {'review_id':str(review.id),'research_decision':body.decision,
            'set_version':body.expected_set_version+1,'gramps_written':False}


@router.get('/hypotheses/{group_id}/options/{option_key}/reviews')
def branch_reviews(group_id:UUID,option_key:str,db:DB):
    _,option=get_group_option(db,group_id,option_key)
    revisions=db.scalars(select(BranchRevision.id).where(BranchRevision.option_id==option.id)).all()
    if not revisions: return []
    reviews=db.scalars(select(BranchReview).where(BranchReview.revision_id.in_(revisions))
                       .order_by(BranchReview.created_at.desc()).limit(100)).all()
    return [{'id':str(x.id),'revision_id':str(x.revision_id),'decision':x.decision,
             'reason':x.reason,'reviewer':x.reviewer,'created_at':x.created_at.isoformat()}
            for x in reviews]
