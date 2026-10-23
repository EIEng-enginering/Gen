"""WP-006 plan tests: never mutate accepted genealogy or silently merge people."""
import base64
from uuid import uuid4, UUID
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.research.db import session as session_dep
from app.research.models import Base, GrampsChangePlan, GrampsPlanDecision, AuditEvent

AUTH = {'Authorization': 'Basic '+base64.b64encode(b'admin:test-password').decode()}
WRITE = {**AUTH, 'X-24Gen-Intent': 'research'}


@pytest.fixture
def setup_client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER', 'admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD', 'test-password')
    monkeypatch.delenv('GEN_GRAMPS_ACCESS_TOKEN', raising=False)
    db = create_engine('sqlite+pysqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(db)
    def sess():
        with Session(db) as s:
            yield s
    app.dependency_overrides[session_dep] = sess
    try:
        with TestClient(app) as c:
            yield c, db
    finally:
        app.dependency_overrides.clear()
        db.dispose()


def seed(client, rel='biological_parent', include_support=True):
    ids=[]
    for number, (name, yr) in enumerate([('Clara Finch', '1780'), ('Arthur Finch', '1810')]):
        d=client.post('/api/v1/research/documents', headers=WRITE,json={
            'provider':'synthetic','provider_record_id':'test'+str(number),'title':'Test register',
            'reference':'Synthetic source', 'origin_group':'register-'+str(number),
            'licence':'test-only', 'access_method':'user_import'})
        assert d.status_code == 201,d.text
        o=client.post('/api/v1/research/documents/'+d.json()['id']+'/observations',headers=WRITE,json={
            'observation_key':'entry','event_type':'birth','person_name_verbatim':name,
            'earliest_iso':yr+'-01-01','latest_iso':yr+'-12-31'})
        assert o.status_code == 201,o.text
        ids.append(o.json()['id'])
    h=client.post('/api/v1/research/hypotheses',headers=WRITE,json={
        'title':'Finch relationship','subject_description':'Research test',
        'relation_type':'biological_parent',
        'options':[{'option_key':'candidate','description':'Clara proposed parent'},
                   {'option_key':'unknown','description':'Unidentified','is_unknown':True}]})
    assert h.status_code == 201,h.text
    hid=h.json()['id']
    edge={'edge_key':'edge-1','from_observation_id':ids[0], 'to_observation_id':ids[1],
          'relationship_type':rel,
          'supporting_observation_ids':[ids[0]] if include_support else [],
          'reasoning':'Independent synthetic original evidence pending inspection'}
    rev=client.post(f'/api/v1/research/hypotheses/{hid}/options/candidate/revisions',headers=WRITE,
                    json={'expected_set_version':1,'rationale':'Initial research revision with cited evidence','edges':[edge]})
    assert rev.status_code==201,rev.text
    return hid, ids, rev.json()['revision_id']


def request(hid,rid,version=2):
    return {'hypothesis_set_id':hid,'option_key':'candidate',
            'expected_set_version':version,'expected_revision_id':rid,
            'bindings':[{'edge_key':'edge-1','from_handle':'gramps-person-1',
                         'to_handle':'gramps-person-2'}]}


def supported(c,hid):
    r=c.post(f'/api/v1/research/hypotheses/{hid}/options/candidate/reviews',headers=WRITE,
             json={'decision':'research_supported','reason':'Reviewed fictional original entries manually',
                   'expected_set_version':2})
    assert r.status_code==201,r.text
    return r.json()['set_version']


def test_preview_safe_and_no_upstream_calls(setup_client,monkeypatch):
    c,db=setup_client
    hid,ids,rid=seed(c)
    def fail(*args,**kw):
        raise AssertionError('Gramps API must never be called during dry-run preview')
    import httpx
    monkeypatch.setattr(httpx,'Client',fail)
    assert c.post('/api/v1/research/gramps/plans/preview',json=request(hid,rid),headers=AUTH).status_code==403
    p=c.post('/api/v1/research/gramps/plans/preview',json=request(hid,rid),headers=WRITE)
    assert p.status_code==200,p.text
    j=p.json();assert len(j['digest_sha256'])==64 and j['accepted_tree_write'] is False
    assert j['upstream_validation']=='NOT_PERFORMED'
    assert j['actions'][0]['from_handle_claimed']=='gramps-person-1'
    with Session(db) as s:
        assert s.scalar(select(func.count()).select_from(GrampsChangePlan))==0


def test_approval_requires_research_support_and_correct_digest(setup_client):
    c,db=setup_client;hid,_,rid=seed(c)
    p=c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(hid,rid)).json()
    body={**request(hid,rid), 'idempotency_key':'unique-proposal-001',
          'expected_preview_digest':p['digest_sha256'],'operator_note':'Candidate Gramps mapping to verify later'}
    assert c.post('/api/v1/research/gramps/plans',headers=WRITE,json=body).status_code==409
    ver=supported(c,hid)
    body['expected_set_version']=ver
    p2=c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(hid,rid,ver)).json()
    body['expected_preview_digest']=p2['digest_sha256']
    bad={**body,'expected_preview_digest':'0'*64}
    assert c.post('/api/v1/research/gramps/plans',headers=WRITE,json=bad).status_code==409
    created=c.post('/api/v1/research/gramps/plans',headers=WRITE,json=body)
    assert created.status_code==201,created.text
    plan=created.json();assert plan['set_version_after_creation']==4
    assert not plan['execution_enabled'] and not plan['accepted_tree_write']
    retry=c.post('/api/v1/research/gramps/plans',headers=WRITE,json=body)
    assert retry.status_code==201 and retry.json()['id']==plan['id']
    collision={**body,'operator_note':'A very different proposal note for same key'}
    assert c.post('/api/v1/research/gramps/plans',headers=WRITE,json=collision).status_code==409
    post=f'/api/v1/research/gramps/plans/{plan["id"]}/decisions'
    approval={'decision':'approve_for_future_validation','expected_set_version':4,
              'expected_preview_digest':p2['digest_sha256'],
              'confirmation':'APPROVE PLAN '+p2['digest_sha256'][:12],
              'rationale':'I have reviewed the fictional proposed family connections'}
    assert c.post(post,headers=AUTH,json=approval).status_code==403
    assert c.post(post,headers=WRITE,json={**approval,'confirmation':'APPROVE PLAN '+'f'*12}).status_code==422
    ok=c.post(post,headers=WRITE,json=approval)
    assert ok.status_code==201,ok.text
    assert not ok.json()['accepted_tree_write'] and not ok.json()['execution_enabled']
    assert c.post(post,headers=WRITE,json=approval).status_code==409
    record=c.get(f'/api/v1/research/gramps/plans/{plan["id"]}',headers=AUTH)
    assert record.status_code==200 and record.json()['decision']['decision']=='approve_for_future_validation'
    with Session(db) as s:
        assert s.scalar(select(func.count()).select_from(GrampsPlanDecision))==1
        assert s.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.action=='gramps_plan_created_no_write'))==1


def test_stale_revision_unknown_invalid_relationship_and_mappings(setup_client):
    c,db=setup_client;hid,obs,rid=seed(c)
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(hid,rid,4)).status_code==409
    invalid={**request(hid,rid),'expected_revision_id':str(uuid4())}
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=invalid).status_code==409
    dup={**request(hid,rid),'bindings':[{'edge_key':'wrong','from_handle':'G1','to_handle':'G2'}]}
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=dup).status_code==422
    same={**request(hid,rid),'bindings':[{'edge_key':'edge-1','from_handle':'G1','to_handle':'G1'}]}
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=same).status_code==422
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json={**request(hid,rid),'option_key':'unknown'}).status_code==409


def test_unsupported_same_person_and_unsourced_rejected(setup_client):
    c,_=setup_client;h,_,r=seed(c,rel='same_person')
    assert c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(h,r)).status_code==422


def test_stale_after_other_review_prevents_approval(setup_client):
    c,db=setup_client;hid,_,rid=seed(c);ver=supported(c,hid)
    p=c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(hid,rid,ver)).json()
    body={**request(hid,rid,ver),'idempotency_key':'unique-proposal-002',
          'expected_preview_digest':p['digest_sha256'],
          'operator_note':'Candidate Gramps identifiers need live comparison'}
    x=c.post('/api/v1/research/gramps/plans',headers=WRITE,json=body).json()
    # A new provisional branch version makes the plan stale.
    from app.research.models import HypothesisSet
    with Session(db) as s:
        group=s.get(HypothesisSet,UUID(hid))
        group.version += 1
        s.commit()
    decision={'decision':'reject','expected_set_version':4,
              'expected_preview_digest':p['digest_sha256'],
              'confirmation':'REJECT PLAN '+p['digest_sha256'][:12],
              'rationale':'Old plan is now stale after newly received evidence'}
    assert c.post(f'/api/v1/research/gramps/plans/{x["id"]}/decisions',headers=WRITE,json=decision).status_code==409


def test_unsourced_parent_and_empty_live_gramps_token(setup_client):
    c,_=setup_client;hid,_,rid=seed(c,include_support=False)
    denied=c.post('/api/v1/research/gramps/plans/preview',headers=WRITE,json=request(hid,rid))
    assert denied.status_code==422 and 'Unsourced' in denied.text
    probe=c.get('/api/v1/research/gramps/compatibility',headers=AUTH)
    assert probe.status_code==200 and probe.json()['read_only'] is True
    assert probe.json()['accepted_tree_write_enabled'] is False


def test_workspace_has_separate_gramps_review_panel(setup_client):
    c,_=setup_client
    assert c.get('/workspace').status_code==401
    response=c.get('/workspace',headers=AUTH)
    assert response.status_code==200
    assert 'gramps-preview-form' in response.text
    assert 'Gramps review (dry-run)' in response.text
    assert 'no accepted-tree writes' in response.text.lower()
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
