"""Genuine offline API CRUD and evidence controls, using isolated SQLite DB."""
from base64 import b64encode
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.research.db import session as session_dep
from app.research.models import Base,AuditEvent,Observation,SourceDocument,TranscriptionRevision

AUTH={'Authorization':'Basic '+b64encode(b'admin:test-password').decode()}
WRITE={**AUTH,'X-24Gen-Intent':'research'}
DOC={'provider':'test_archive','provider_record_id':'a-001','title':'Parish page',
     'reference':'Parish register film 42 p10','origin_group':'original_volume/42/10',
     'licence':'user_supplied_research_only','access_method':'user_import'}
OBS={'observation_key':'line-1','event_type':'baptism','person_name_verbatim':'John Carter',
     'surname_verbatim':'Carter','given_names_verbatim':'John','earliest_iso':'1790-05-01',
     'latest_iso':'1790-05-31','event_date_verbatim':'May 1790','location_verbatim':'Yorkshire',
     'transcription_verbatim':'John Carter baptized'}

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER','admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD','test-password')
    eng=create_engine('sqlite+pysqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(eng)
    def db():
        with Session(eng) as s:yield s
    app.dependency_overrides[session_dep]=db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        eng.dispose()


def test_requires_auth_and_mutation_intent(client):
    assert client.get('/api/v1/research/summary').status_code==401
    assert client.post('/api/v1/research/documents',headers=AUTH,json=DOC).status_code==403
    assert client.post('/api/v1/research/documents',headers={**WRITE,'Origin':'https://evil.example'},json=DOC).status_code==403
    assert client.get('/api/v1/research/summary',headers=AUTH).json()['documents']==0


def source(client,data=DOC):
    r=client.post('/api/v1/research/documents',headers=WRITE,json=data)
    assert r.status_code==201,r.text
    return r.json()['id']


def appearance(client,did,data=OBS):
    r=client.post(f'/api/v1/research/documents/{did}/observations',headers=WRITE,json=data)
    assert r.status_code==201,r.text
    return r.json()['id']


def test_cited_document_idempotence_and_conflicting_provider_id(client):
    ident=source(client)
    assert source(client)==ident
    changed={**DOC,'reference':'Different page'}
    assert client.post('/api/v1/research/documents',headers=WRITE,json=changed).status_code==409
    assert client.get('/api/v1/research/summary',headers=AUTH).json()['documents']==1
    assert 'Parish register' in client.get(f'/api/v1/research/documents/{ident}',headers=AUTH).json()['reference']


def test_observation_corrections_are_append_only(client):
    did=source(client);oid=appearance(client,did)
    assert appearance(client,did)==oid
    rev=client.post(f'/api/v1/research/observations/{oid}/transcriptions',headers=WRITE,
                    json={'text':'John Carter baptysed','reason':'Alternate reading'})
    assert rev.status_code==201,rev.text
    history=client.get(f'/api/v1/research/observations/{oid}/transcriptions',headers=AUTH).json()
    assert [x['text'] for x in history]==['John Carter baptized','John Carter baptysed']
    assert history[1]['supersedes_id']==history[0]['id']
    assert client.get(f'/api/v1/research/observations/{oid}',headers=AUTH).json()['transcription_verbatim']=='John Carter baptized'


def test_bad_date_range_does_not_insert(client):
    did=source(client)
    r=client.post(f'/api/v1/research/documents/{did}/observations',headers=WRITE,
                  json={**OBS,'earliest_iso':'1850-01-01','latest_iso':'1800-01-01'})
    assert r.status_code==422
    assert client.get('/api/v1/research/summary',headers=AUTH).json()['observations']==0


def test_identity_candidate_scores_not_probabilities(client):
    first=appearance(client,source(client))
    second=appearance(client,source(client,{**DOC,'provider_record_id':'a-002','origin_group':'original_volume/43/11'}),
                      {**OBS,'observation_key':'line-3','person_name_verbatim':'Jon Carter','event_type':'marriage'})
    r=client.post(f'/api/v1/research/observations/{first}/suggest-matches',headers=WRITE)
    assert r.status_code==200,r.text
    payload=r.json()
    assert payload['candidates']
    assert 'NOT probabilities' in payload['warning']
    assert payload['candidates'][0]['calibrated_probability'] is None
    candidate_id=payload['candidates'][0]['candidate_id']
    r=client.post('/api/v1/research/identity-candidates/'+candidate_id+'/review',headers=WRITE,
                  json={'decision':'accept_as_research','reason':'Reviewed documents and no hard contradictions'})
    assert r.status_code==200
    assert r.json()['gramps_written'] is False
    assert client.post('/api/v1/research/identity-candidates/'+candidate_id+'/review',headers=WRITE,
                  json={'decision':'reject','reason':'Another person'}).status_code==409


def test_hypothesis_requires_unknown_and_genuine_evidence(client):
    oid=appearance(client,source(client))
    opts=[{'option_key':'father_a','description':'Possible father A','evidence_observation_ids':[oid]},
          {'option_key':'other_unknown','description':'Unidentified father','is_unknown':True}]
    body={'title':'Father of John','subject_description':'Unknown father','relation_type':'biological_parent','options':opts}
    assert client.post('/api/v1/research/hypotheses',headers=WRITE,json=body).status_code==201
    result=client.get('/api/v1/research/hypotheses',headers=AUTH).json()
    assert len(result[0]['options'])==2
    assert sum(x['is_unknown'] for x in result[0]['options'])==1
    assert all(x['calibrated_probability'] is None for x in result[0]['options'])
    assert client.post('/api/v1/research/hypotheses',headers=WRITE,json={**body,'options':opts[:1]}).status_code==422
    fake='00000000-0000-4000-8000-000000000002'
    invalid=[{**opts[0],'evidence_observation_ids':[fake]},opts[1]]
    assert client.post('/api/v1/research/hypotheses',headers=WRITE,json={**body,'options':invalid}).status_code==422


def test_hypothesis_probabilities_require_calibration_id_and_sum_to_one(client):
    opts=[{'option_key':'father_1','description':'A','calibrated_probability':0.75,'model_id':'benchmark-v1'},
          {'option_key':'other_unknown','description':'Other','is_unknown':True,'calibrated_probability':0.25,'model_id':'benchmark-v1'}]
    body={'title':'Father','subject_description':'Unknown father','relation_type':'biological_parent','options':opts}
    assert client.post('/api/v1/research/hypotheses',headers=WRITE,json=body).status_code==422
    opts[0]['calibrated_probability']=0.85
    assert client.post('/api/v1/research/hypotheses',headers=WRITE,json=body).status_code==422
    # This phase rejects fabricated numeric probabilities despite model_id text.


def test_jobs_do_not_run_implicitly(client):
    r=client.post('/api/v1/research/jobs',headers=WRITE,
                  json={'mode':'autonomous','objective':'Find ancestors','cost_limit_usd':0.0})
    assert r.status_code==201
    ident=r.json()['id'];assert r.json()['status']=='paused'
    assert r.json()['execution_engine']=='not_yet_implemented'
    r=client.post('/api/v1/research/jobs/'+ident+'/control',headers=WRITE,json={'action':'resume'})
    assert r.json()['status']=='queued'
    assert client.post('/api/v1/research/jobs/'+ident+'/control',headers=WRITE,json={'action':'resume'}).status_code==409
    assert client.post('/api/v1/research/jobs/'+ident+'/control',headers=WRITE,json={'action':'cancel'}).json()['status']=='cancelled'


def test_review_audit_and_workspace_escapes_local_only(client):
    did=source(client)
    assert client.get('/api/v1/research/audit',headers=AUTH).json()[0]['target_id']==did
    assert client.get('/workspace').status_code==401
    page=client.get('/workspace',headers=AUTH)
    assert page.status_code==200
    assert 'Historical documents' in page.text
    assert 'frame-ancestors' in page.headers['content-security-policy']
    assert 'External sites' not in page.text or 'no automatic external searches' in page.text


def test_gramps_probe_does_not_connect_without_token(client,monkeypatch):
    monkeypatch.delenv('GEN_GRAMPS_ACCESS_TOKEN',raising=False)
    r=client.get('/api/v1/research/gramps-compatibility',headers=AUTH)
    assert r.status_code==200
    assert r.json()['status']=='token_not_configured'
    assert r.json()['read_only'] is True
