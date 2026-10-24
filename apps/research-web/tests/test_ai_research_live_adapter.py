"""Synthetic Cheshire cases and non-network local model stub tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from uuid import uuid4
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import httpx
import pytest
from app.main import app
from app.research.db import session as session_dep
from app.research.ai_research_engine import validate_model_answer,ModelResponseRejected,local_endpoint
from app.research.models import Base,AIResearchRun
from test_research_api import AUTH,WRITE,DOC,OBS,source,appearance

BASE='/api/v1/research/ai'

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER','admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD','test-password')
    monkeypatch.delenv('GEN_LOCAL_AI_MODEL',raising=False)
    eng=create_engine('sqlite+pysqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(eng)
    def local_db():
        with Session(eng) as db:yield db
    app.dependency_overrides[session_dep]=local_db
    try:yield TestClient(app),eng
    finally:
        app.dependency_overrides.clear();eng.dispose()

def _oldham(client):
    doc=source(client,{**DOC,'provider_record_id':'cheshire-census-1851',
                       'title':'Synthetic 1851 census of Cheshire', 'reference':'Fictional archival folio 1851/10',
                       'origin_group':'fictional-census-sheet-12'})
    a=appearance(client,doc,{**OBS,'person_name_verbatim':'William Oldham','surname_verbatim':'Oldham',
                             'given_names_verbatim':'William','event_type':'census','event_date_verbatim':'1851',
                             'earliest_iso':'1851-01-01','latest_iso':'1851-12-31',
                             'location_verbatim':'Cheshire','transcription_verbatim':'William Oldham, household 1851'})
    return a

def test_ai_requires_auth_intent_scope(client):
    c,_=client
    body={'question':'Research Oldham census evidence', 'surname':'Oldham','county':'Cheshire'}
    assert c.post(BASE+'/ask',json=body).status_code==401
    assert c.post(BASE+'/ask',headers=AUTH,json=body).status_code==403
    assert c.post(BASE+'/ask',headers={**WRITE,'Origin':'https://malicious.example'},json=body).status_code==403
    assert c.post(BASE+'/ask',headers=WRITE,json={'question':'Search all records'}).status_code==422
    assert c.post(BASE+'/ask',headers=WRITE,json={**body,'from_year':1900,'to_year':1800}).status_code==422

def test_offline_chat_local_history_and_provenance(client):
    c,eng=client; oid=_oldham(c)
    query={'question':'Are the Oldham families related?','surname':'Oldham','county':'Cheshire',
           'from_year':1800,'to_year':1900,'mode':'guided'}
    r=c.post(BASE+'/ask',headers=WRITE,json=query)
    assert r.status_code==200,r.text
    answer=r.json()['answer']
    assert answer['model_execution']=='deterministic_fallback'
    assert answer['citations'][0]['observation_id']==oid
    assert answer['observed_facts'][0]['citation']['reference']=='Fictional archival folio 1851/10'
    assert answer['calibrated_probability'] is None
    assert answer['accepted_tree_mutation_enabled'] is False
    assert answer['online_sources_searched']==[]
    assert all(a['status']=='not_searched' and a['access']=='manual_only' for a in answer['manual_source_leads'])
    assert c.get(BASE+'/history',headers=AUTH).json()[0]['id']==r.json()['id']
    assert c.get(BASE+'/history/'+r.json()['id'],headers=AUTH).json()['answer']==answer
    with Session(eng) as db:assert len(db.scalars(select(AIResearchRun)).all())==1

def test_empty_county_is_not_exhaustive_no_result(client):
    c,_=client
    r=c.post(BASE+'/ask',headers=WRITE,json={'question':'Any listed Oldhams?','surname':'Oldham'})
    assert r.status_code==200
    assert not r.json()['answer']['selection_is_exhaustive']
    assert not r.json()['answer']['observed_facts']

def test_model_response_checks_reject_forgery_and_bounds():
    ident=str(uuid4())
    records=[{'observation_id':ident}]
    reply={'interpretation':'This might be one person, but more records are required.',
           'cited_observation_ids':[ident],
           'uncertainties':['Two Williams may differ'],
           'next_steps':['Review original census']}
    assert validate_model_answer(reply,records)['cited_observation_ids']==[ident]
    with pytest.raises(ModelResponseRejected):validate_model_answer({**reply,'cited_observation_ids':[str(uuid4())]},records)
    with pytest.raises(ModelResponseRejected):validate_model_answer({**reply,'unsafe_command':'merge_gramp_people'},records)
    with pytest.raises(ModelResponseRejected):validate_model_answer({**reply,'interpretation':'x'*3000},records)

def test_model_path_with_synthetic_http_and_refusal(client,monkeypatch):
    c,_=client;oid=_oldham(c)
    monkeypatch.setenv('GEN_LOCAL_AI_MODEL','gemma3:4b')
    monkeypatch.setenv('GEN_LOCAL_AI_URL','http://127.0.0.1:11434')
    base={'interpretation':'The 1851 household may need comparison with an 1841 entry.',
          'cited_observation_ids':[oid],'uncertainties':['Parentage unknown'],
          'next_steps':['Inspect parish records']}
    def handler(req):
        assert req.url.path=='/api/chat'
        data=json.loads(req.content)
        assert data['model']=='gemma3:4b'
        assert 'untrusted historical data' in data['messages'][1]['content']
        return httpx.Response(200,json={'message':{'content':json.dumps(base)}},headers={'Content-Type':'application/json'})
    real=httpx.Client
    def fake_client(*args,**kwargs):
        kwargs.pop('trust_env',None)
        return real(*args,transport=httpx.MockTransport(handler),**kwargs)
    monkeypatch.setattr('app.research.ai_research_engine.httpx.Client',fake_client)
    request={'question':'Evaluate two Oldhams','surname':'Oldham','county':'Cheshire'}
    good=c.post(BASE+'/ask',headers=WRITE,json=request)
    assert good.status_code==200,good.text
    assert good.json()['answer']['model_execution']=='local_model'
    assert good.json()['answer']['model_cited_observation_ids']==[oid]
    base['cited_observation_ids']=[str(uuid4())]
    denied=c.post(BASE+'/ask',headers=WRITE,json=request)
    assert denied.status_code==200
    assert denied.json()['answer']['model_execution']=='deterministic_fallback'

def test_model_endpoint_allowlist(monkeypatch):
    for url in ('http://public.example:11434','https://127.0.0.1:11434',
                'http://127.0.0.1:8080','http://user:pass@localhost:11434'):
        monkeypatch.setenv('GEN_LOCAL_AI_URL',url)
        with pytest.raises(Exception):local_endpoint()

def test_no_gramps_mutation_route_and_ui_research_entry(client):
    c,_=client
    routes=[(r.path,m) for r in app.routes for m in (r.methods or []) if '/research/ai' in r.path]
    assert all(not (m in ('PUT','PATCH','DELETE')) for _,m in routes)
    s=c.get('/workspace',headers=AUTH).text
    assert 'AI Research' in s and 'data-tab="ai-research"' in s
    assert "textContent" in s and 'innerHTML' not in s
    assert c.get('/api/v1/research/ai/capabilities',headers=AUTH).json()['accepted_gramps_writes_enabled'] is False
