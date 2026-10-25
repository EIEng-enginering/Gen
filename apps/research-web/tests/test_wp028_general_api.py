"""Bounded authenticated API smoke, synthetic surname unrelated to Cheshire."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.research.models import Base,SourceDocument,Observation
from app.research.general_search_models import SearchMention
from app.research.db import session as session_dep
from uuid import uuid4

AUTH={'Authorization':'Basic YWRtaW46dGVzdC1wYXNzd29yZA=='}
WRITE={**AUTH,'X-24Gen-Intent':'research'}
ROOT='/api/v1/research/general'
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER','admin');monkeypatch.setenv('GEN_ADMIN_PASSWORD','test-password')
    engine=create_engine('sqlite+pysqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    def dep():
        with Session(engine) as s:yield s
    app.dependency_overrides[session_dep]=dep
    try:yield TestClient(app),engine
    finally:app.dependency_overrides.clear();engine.dispose()

def test_unauthenticated_denied_and_no_external_calls(client):
    c,_=client
    assert c.get('/general-search').status_code==401
    r=c.get('/general-search',headers=AUTH)
    assert r.status_code==200
    assert 'textContent' in r.text and 'General Historical Record Search' in r.text
    assert 'Given names to compare (does not filter results)' in r.text
    assert c.get(ROOT+'/coverage').status_code==401
    r=c.get(ROOT+'/coverage',headers=AUTH)
    assert r.status_code==200 and r.json()['providers_executed']==0
    features=c.get('/api/v1/features',headers=AUTH).json()
    assert 'bounded_local_general_search' in features['implemented']
    assert 'unified_gramps_and_record_search' in features['planned_not_implemented']

def test_mutation_guard_and_endpoints(client):
    c,eng=client
    with Session(eng) as db:
        d=SourceDocument(provider='fixture',provider_record_id='F1',title='Fictional English census',
            reference='FAKE/01871',origin_group='demo/a',access_method='user_import',
            licence='synthetic',acquisition_operator='tester',
            metadata_json={'operator_source_check_attested':True})
        db.add(d);db.flush()
        db.add(Observation(document_id=d.id,observation_key='1',event_type='census',
            person_name_verbatim='Caroline Mercer',surname_verbatim='Mercer',given_names_verbatim='Caroline',
            location_verbatim='Bristol, Gloucestershire',event_date_verbatim='1871'))
        db.commit()
    assert c.post(ROOT+'/index/sync',headers=AUTH,json={'source_kind':'observed'}).status_code==403
    assert c.post(ROOT+'/index/sync',headers={**WRITE,'Origin':'https://bad.example'},json={'source_kind':'observed'}).status_code==403
    r=c.post(ROOT+'/index/sync',headers=WRITE,json={'source_kind':'observed'})
    assert r.status_code==200,r.text
    assert r.json()['created']==1
    q=c.get(ROOT+'/search',headers=AUTH,params={'surname':'Mercer','county':'Gloucestershire'})
    assert q.status_code==200,q.text
    assert len(q.json()['results'])==1
    assert q.json()['results'][0]['source_checked'] is True
    oid=q.json()['results'][0]['id']
    x=c.get(ROOT+f'/mentions/{oid}/correlations',headers=AUTH)
    assert x.status_code==200 and x.json()['unknown_candidate'] is True
    assert x.json()['calibrated_probability'] is None
    assert c.get(ROOT+'/search',headers=AUTH,params={}).status_code==422
    assert c.post(ROOT+'/index/sync',headers=WRITE,json={'source_kind':'observed'}).json()['created']==0
