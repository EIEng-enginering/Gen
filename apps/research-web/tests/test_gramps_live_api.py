"""WP-007 read-only API integration with synthetic historical identifiers."""
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.research.models import GrampsReadValidation, AuditEvent, HypothesisSet
from test_gramps_plan import setup_client, seed, supported, request, AUTH, WRITE
from test_gramps_live_read import installed
from app.research import gramps_live_read as lib


def approved_plan(c):
    hid,_,rid=seed(c)
    ver=supported(c,hid)
    preview=c.post('/api/v1/research/gramps/plans/preview',json=request(hid,rid,ver),headers=WRITE)
    assert preview.status_code==200,preview.text
    digest=preview.json()['digest_sha256']
    x=c.post('/api/v1/research/gramps/plans', headers=WRITE, json={
       **request(hid,rid,ver),'idempotency_key':'validate-plan-unique-001',
       'expected_preview_digest':digest,'operator_note':'Synthetic family source requires Gramps identity checks'})
    assert x.status_code==201,x.text
    plan=x.json()
    return plan,hid,digest


def approve(c,plan,digest):
    return c.post('/api/v1/research/gramps/plans/'+plan['id']+'/decisions',headers=WRITE,json={
        'decision':'approve_for_future_validation',
        'expected_set_version':plan['set_version_after_creation'],
        'expected_preview_digest':digest,
        'confirmation':'APPROVE PLAN '+digest[:12],
        'rationale':'I reviewed the synthetic genealogy evidence and request read checks only'})


def test_live_validation_needs_approval_before_any_remote_fetch(setup_client,monkeypatch):
    c,_=setup_client;plan,_,digest=approved_plan(c)
    called=[]
    monkeypatch.setattr(lib,'make_client',lambda:called.append('called'))
    url='/api/v1/research/gramps/plans/'+plan['id']+'/read-validate'
    assert c.post(url,headers=WRITE).status_code==409
    assert c.post(url,headers=AUTH).status_code==403
    assert called==[]


def test_live_validation_records_only_local_audit_and_supports_history(setup_client,monkeypatch):
    c,engine=setup_client;plan,_,digest=approved_plan(c)
    assert approve(c,plan,digest).status_code==201
    installed(monkeypatch)
    url='/api/v1/research/gramps/plans/'+plan['id']+'/read-validate'
    response=c.post(url,headers=WRITE)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['mutation_performed'] is False and result['execution_enabled'] is False
    assert result['findings'][0]['observed_upstream_status']=='already_linked'
    assert 'FAKE_PRIVATE_TOKEN' not in response.text
    history=c.get('/api/v1/research/gramps/plans/'+plan['id']+'/read-validations',headers=AUTH)
    assert history.status_code==200 and len(history.json())==1
    assert history.json()[0]['snapshot_sha256']==result['snapshot_sha256']
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(GrampsReadValidation))==1
        assert db.scalar(select(func.count()).select_from(AuditEvent).where(
            AuditEvent.action=='gramps_read_only_validation'))==1


def test_read_validation_fail_closed_when_upstream_unavailable(setup_client,monkeypatch):
    c,engine=setup_client;plan,_,digest=approved_plan(c)
    assert approve(c,plan,digest).status_code==201
    monkeypatch.delenv('GEN_GRAMPS_ACCESS_TOKEN',raising=False)
    response=c.post('/api/v1/research/gramps/plans/'+plan['id']+'/read-validate',headers=WRITE)
    assert response.status_code==503 and response.json()['detail']['code']=='token_not_configured'
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(GrampsReadValidation))==0


def test_stale_version_blocks_before_upstream_request(setup_client,monkeypatch):
    c,engine=setup_client;plan,hid,digest=approved_plan(c)
    assert approve(c,plan,digest).status_code==201
    installed(monkeypatch)
    with Session(engine) as db:
        from uuid import UUID
        group=db.get(HypothesisSet,UUID(hid))
        group.version+=1
        db.commit()
    response=c.post('/api/v1/research/gramps/plans/'+plan['id']+'/read-validate',headers=WRITE)
    assert response.status_code==409


def test_no_upstream_fetch_for_rejected_plan(setup_client,monkeypatch):
    c,engine=setup_client;plan,_,digest=approved_plan(c)
    response=c.post('/api/v1/research/gramps/plans/'+plan['id']+'/decisions',headers=WRITE,json={
        'decision':'reject', 'expected_set_version':plan['set_version_after_creation'],
        'expected_preview_digest':digest,'confirmation':'REJECT PLAN '+digest[:12],
        'rationale':'The records are inconsistent so do not proceed'})
    assert response.status_code==201
    installed(monkeypatch)
    assert c.post('/api/v1/research/gramps/plans/'+plan['id']+'/read-validate',headers=WRITE).status_code==409


def test_workspace_exposes_manual_get_only_validation(setup_client):
    c,_=setup_client
    r=c.get('/workspace',headers=AUTH)
    assert r.status_code==200
    assert 'gramps-live-read' in r.text
    assert 'No accepted-tree change is authorised' in r.text
    assert 'Gramps live read-only validation' in r.text


def test_tampered_stored_actions_rejected_before_upstream_fetch(setup_client,monkeypatch):
    from uuid import UUID
    from app.research.models import GrampsChangePlan
    c,engine=setup_client;plan,_,digest=approved_plan(c)
    assert approve(c,plan,digest).status_code==201
    installed(monkeypatch)
    with Session(engine) as db:
        obj=db.get(GrampsChangePlan,UUID(plan['id']))
        preview=dict(obj.preview_json)
        actions=[dict(x) for x in preview['actions']]
        actions[0]['to_handle_claimed']='DIFFERENT_PERSON'
        preview['actions']=actions
        obj.preview_json=preview
        db.commit()
    resp=c.post('/api/v1/research/gramps/plans/'+plan['id']+'/read-validate',headers=WRITE)
    assert resp.status_code==409
