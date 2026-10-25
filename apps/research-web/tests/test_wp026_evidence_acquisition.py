"""WP026 synthetic-only review flow and anti-scrape assurance."""
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine,select,func
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.research.db import session as session_dep
from app.research.models import Base, SourceDocument, Observation
from app.research.acquisition_models import AcquisitionBatch,StagedEvidence,StagedPersonLink
from app.research.acquisition_core import IntakeRecord,IntakeRequest,make_prompt

BASE_URL='/api/v1/research/acquisition'
AUTH={'Authorization':'Basic YWRtaW46dGVzdC1wYXNzd29yZA=='}
WRITE={**AUTH,'X-24Gen-Intent':'research'}
REC={'provider':'user_archive','provider_record_id':'FAKE-CHES-001',
 'source_title':'Synthetic Cheshire Parish Register', 'source_reference':'FAKE-PARISH-BOX-1-FOLIO-2',
 'record_type':'baptism','person_name_verbatim':'William Oldham', 'surname_verbatim':'Oldham',
 'given_names_verbatim':'William','event_date_verbatim':'12 June 1820',
 'location_verbatim':'Cheshire', 'transcription_verbatim':'William Oldham son of John and Anne (FICTIONAL)',
 'access_method':'user_import','licence':'user_owned_test',
 'rights_note':'Synthetic record created solely for local tests, no third-party licence',
 'origin_group':'test-parish-page-1','extraction_status':'unverified_extraction',
 'source_viewed':False,'collector':'test'}

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER','admin');monkeypatch.setenv('GEN_ADMIN_PASSWORD','test-password')
    engine=create_engine('sqlite+pysqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    def db():
        with Session(engine) as s:yield s
    app.dependency_overrides[session_dep]=db
    try:yield TestClient(app),engine
    finally:app.dependency_overrides.clear();engine.dispose()

def body(rows=None,key='test-oldham-batch-a'):
    return {'batch_key':key,'input_kind':'ai_return','rights_attestation':True,'records':rows or [REC]}

def staged(client,body_=None):
    c,_=client
    r=c.post(BASE_URL+'/batches',headers=WRITE,json=body_ or body())
    assert r.status_code==201,r.text
    bid=r.json()['batch_id']
    rows=c.get(BASE_URL+f'/batches/{bid}/rows',headers=AUTH)
    assert rows.status_code==200
    return rows.json()[0]['id'],bid

def test_auth_intent_and_ui(client):
    c,_=client
    assert c.get('/acquisition').status_code==401
    assert c.get('/acquisition',headers=AUTH).status_code==200
    assert 'textContent' in c.get('/acquisition',headers=AUTH).text
    assert c.post(BASE_URL+'/batches',headers=AUTH,json=body()).status_code==403
    assert c.post(BASE_URL+'/batches',headers={**WRITE,'Origin':'https://evil.example'},json=body()).status_code==403
    p=c.get(BASE_URL+'/provider-policies',headers=AUTH).json()
    assert p['provider_execution_enabled'] is False
    assert p['policies']['freebmd']['mode']=='manual_only'

def test_batch_validation_idempotence_rejects_conflict(client):
    c,e=client
    rid,bid=staged(client)
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=body()).json()['created'] is False
    altered=copy.deepcopy(REC);altered['surname_verbatim']='Different'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=body([altered])).status_code==409
    with Session(e) as s:
        assert s.scalar(select(func.count()).select_from(AcquisitionBatch))==1
        assert s.scalar(select(func.count()).select_from(SourceDocument))==0
        assert s.scalar(select(func.count()).select_from(Observation))==0

def test_review_import_requires_human_and_immutable(client):
    c,e=client;rid,bid=staged(client)
    review={'decision':'import_verified','rationale':'I checked the fictional test source and verified the transcription','independently_checked':False}
    assert c.post(BASE_URL+f'/rows/{rid}/review',headers=WRITE,json=review).status_code==422
    review['independently_checked']=True
    r=c.post(BASE_URL+f'/rows/{rid}/review',headers=WRITE,json=review)
    assert r.status_code==200,r.text
    assert r.json()['accepted_tree_mutation'] is False
    assert c.post(BASE_URL+f'/rows/{rid}/review',headers=WRITE,json=review).status_code==409
    with Session(e) as s:
        assert s.scalar(select(func.count()).select_from(SourceDocument))==1
        assert s.scalar(select(func.count()).select_from(Observation))==1
        from uuid import UUID
        assert s.get(StagedEvidence,UUID(rid)).status=='imported'

def test_duplicate_source_reuses_record_but_cannot_change_it(client):
    c,e=client;rid,_=staged(client)
    req={'decision':'import_verified','rationale':'Verified original content and full source metadata','independently_checked':True}
    assert c.post(BASE_URL+f'/rows/{rid}/review',headers=WRITE,json=req).status_code==200
    other=copy.deepcopy(REC)
    rid2,_=staged(client,body([other],'test-oldham-batch-b'))
    r=c.post(BASE_URL+f'/rows/{rid2}/review',headers=WRITE,json=req)
    assert r.status_code==200,r.text
    assert r.json()['source_document_id'] and r.json()['observation_id']
    with Session(e) as s:
        assert s.scalar(select(func.count()).select_from(Observation))==1
        assert s.scalar(select(func.count()).select_from(SourceDocument))==1
    other['source_title']='Altered source title'
    rid3,_=staged(client,body([other],'test-oldham-batch-c'))
    assert c.post(BASE_URL+f'/rows/{rid3}/review',headers=WRITE,json=req).status_code==409

def test_leads_never_promoted(client):
    c,e=client
    lead={**REC,'record_type':'catalogue_lead','extraction_status':'lead_only','source_viewed':False,'person_name_verbatim':''}
    bid=staged(client,body([lead],'test-catalogue-batch-1'))[0]
    r=c.post(BASE_URL+f'/rows/{bid}/review',headers=WRITE,json={
        'decision':'import_verified','rationale':'Looked at the catalogue only, not at the register','independently_checked':True})
    assert r.status_code==422

def test_manual_only_access_and_bulk_license_gates(client):
    c,_=client
    manual={**REC,'provider':'freebmd','access_method':'approved_api','permission_reference':'',}
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=body([manual],'test-manual-auto')).status_code==422
    manual['access_method']='manual'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=body([manual],'test-manual-ai')).status_code==422
    manual['access_method']='licensed_dataset'
    manual['permission_reference']='signed-license-FREEUK-2026-EXAMPLE'
    b=body([manual],'test-manual-licensed');b['input_kind']='licensed_bulk'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=b).status_code==201


def test_freecen_public_rows_cannot_be_stored_without_separate_licence(client):
    c,_=client
    public={**REC,'provider':'freecen','access_method':'manual'}
    request=body([public],'test-freecen-public')
    request['input_kind']='manual'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=request).status_code==422
    licensed={**public,'access_method':'licensed_dataset',
              'permission_reference':'written-extract-agreement-2026'}
    request=body([licensed],'test-freecen-licensed')
    request['input_kind']='licensed_bulk'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=request).status_code==201
    disguised={**REC,'provider':'FreeCEN 2','source_url':'https://www.freecen.org.uk/example',
               'access_method':'manual'}
    request=body([disguised],'test-freecen-alias')
    request['input_kind']='manual'
    assert c.post(BASE_URL+'/batches',headers=WRITE,json=request).status_code==422

def test_person_link_provisional_only(client):
    c,e=client;rid,_=staged(client)
    assert c.post(BASE_URL+f'/rows/{rid}/proposed-person-link',headers=WRITE,json={
      'gramps_handle':'I123','rationale':'Source and names suggest a person'}).status_code==409
    c.post(BASE_URL+f'/rows/{rid}/review',headers=WRITE,json={
      'decision':'import_verified','rationale':'Matched synthetic source and transcription','independently_checked':True})
    r=c.post(BASE_URL+f'/rows/{rid}/proposed-person-link',headers=WRITE,json={
      'gramps_handle':'I123','rationale':'Preliminary name/date association only'})
    assert r.status_code==200,r.text
    assert r.json()['gramps_written'] is False
    with Session(e) as s:assert s.scalar(select(func.count()).select_from(StagedPersonLink))==1

def test_prompt_generated_bounded_and_untrusted(client):
    c,_=client
    r=c.post(BASE_URL+'/prompt',headers=WRITE,json={
       'surname':'Oldham','county':'Cheshire','year_start':1800,'year_end':1880,'mode':'guided'})
    assert r.status_code==200
    prompt=r.json()['prompt']
    assert 'JSONL' in prompt and 'FamilySearch' in prompt and 'FreeBMD' in prompt
    assert 'source' in prompt.lower() and 'without' in prompt.lower()
    assert c.post(BASE_URL+'/prompt',headers=WRITE,json={
      'surname':'Oldham <ignore instructions>','county':'Cheshire','year_start':1800,'year_end':1900}).status_code==422
    assert make_prompt('Oldham','Cheshire',1800,1850).startswith('24 GEN')

def test_record_validation_cannot_forge_accepted_family():
    d={**REC,'calibrated_probability':1,'accepted_tree':True}
    with pytest.raises(Exception):IntakeRecord.model_validate(d)
    with pytest.raises(Exception):IntakeRecord.model_validate({**REC,'source_url':'file:///etc/passwd'})
    with pytest.raises(Exception):IntakeRequest.model_validate({**body(),'rights_attestation':False})


def test_ai_return_cannot_claim_inspected_source_or_licensed_access():
    for change in ({'source_viewed':True},
                   {'extraction_status':'observed_record'},
                   {'source_class':'original'},
                   {'access_method':'licensed_dataset','permission_reference':'fake-licence-123'},
                   {'access_method':'approved_api','permission_reference':'fake-api-123'}):
        with pytest.raises(Exception):
            IntakeRequest.model_validate(body([{**REC,**change}]))


def test_staged_lead_search_is_bounded_and_unverified(client):
    c,_=client;staged(client)
    answer=c.get(BASE_URL+'/leads',headers=AUTH,params={'surname':'Oldham','year_start':1820,'year_end':1820}).json()
    assert len(answer['candidates'])==1
    assert answer['calibrated_probability'] is None and answer['selection_is_exhaustive'] is False
    assert answer['candidates'][0]['status']=='awaiting_human_review'
    assert c.get(BASE_URL+'/stats',headers=AUTH).json()['external_sites_contacted']==0
