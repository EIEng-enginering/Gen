"""WP-005: human-reviewable genealogy alternatives, no fictional probability labels."""
import base64
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.research.db import session as session_dep
from app.research.models import (Base, BranchEdge, BranchRevision, BranchReview,
                                 HypothesisSet, Observation)
from app.research.graph import validate_topology
from app.research.graph_schemas import EdgeIn
from uuid import uuid4

AUTH={'Authorization':'Basic '+base64.b64encode(b'admin:test-password').decode()}
WRITE={**AUTH,'X-24Gen-Intent':'research'}

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER','admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD','test-password')
    db=create_engine('sqlite+pysqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(db)
    def sess():
        with Session(db) as s:yield s
    app.dependency_overrides[session_dep]=sess
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear();db.dispose()


def observations(client):
    uuids=[]
    for name,kind,year,group in [('Harriet Carter','birth','1790','register-7'),
                                  ('Edmund Carter','birth','1819','register-8'),
                                  ('Harriet Carter','census','1841','register-7'),
                                  ('Edmund Carter','census','1841','register-7')]:
        d={'provider':'local_test','provider_record_id':name+kind,
           'title':'Synthetic '+kind,'reference':'Test register '+group,
           'origin_group':group,'licence':'test-only','access_method':'user_import'}
        doc=client.post('/api/v1/research/documents',headers=WRITE,json=d)
        assert doc.status_code==201,doc.text
        oid=client.post('/api/v1/research/documents/'+doc.json()['id']+'/observations',headers=WRITE,json={
            'observation_key':'entry-1','event_type':kind,'person_name_verbatim':name,
            'event_date_verbatim':year,'earliest_iso':year+'-01-01','latest_iso':year+'-12-31'});
        assert oid.status_code==201,oid.text
        uuids.append(oid.json()['id'])
    return uuids


def hypothesis(client, uuids):
    opts=[{'option_key':'mother_harriet','description':'Harriet is mother of Edmund',
           'evidence_observation_ids':[uuids[0],uuids[1]]},
          {'option_key':'other_unknown','description':'Parent unknown','is_unknown':True}]
    r=client.post('/api/v1/research/hypotheses',headers=WRITE,json={
        'title':'Parentage of Edmund','subject_description':'Edmund parentage',
        'relation_type':'biological_parent','options':opts})
    assert r.status_code==201,r.text
    return r.json()['id']


def revision(c,h,option,version,edges):
    return c.post(f'/api/v1/research/hypotheses/{h}/options/{option}/revisions',headers=WRITE,
                  json={'expected_set_version':version,'rationale':'Genealogical alternative pending source review',
                        'edges':edges})


def parent(a,b,support,contradict=()):
    return {'edge_key':'parent-1','from_observation_id':a,'to_observation_id':b,
            'relationship_type':'biological_parent','supporting_observation_ids':list(support),
            'contradicting_observation_ids':list(contradict),
            'reasoning':'Synthetic original register entry, require individual comparison'}


def test_graph_revisions_and_optimistic_conflict(client):
    obs=observations(client);hid=hypothesis(client,obs)
    graph=client.get(f'/api/v1/research/hypotheses/{hid}/graph',headers=AUTH).json()
    assert graph['version']==1 and len(graph['options'])==2
    r=revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[0:2])])
    assert r.status_code==201,r.text
    assert r.json()['set_version']==2 and not r.json()['gramps_written']
    assert revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[0:2])]).status_code==409
    g=client.get(f'/api/v1/research/hypotheses/{hid}/graph',headers=AUTH).json()
    assert g['version']==2
    assert g['calibrated_probabilities'] is None
    assert g['comparison']['distinct_edges_by_option']['mother_harriet']
    r=revision(client,hid,'other_unknown',2,[])
    assert r.status_code==201,r.text
    assert revision(client,hid,'other_unknown',3,[parent(obs[0],obs[1],obs[0:2])]).status_code==422
    hist=client.get(f'/api/v1/research/hypotheses/{hid}/options/mother_harriet/revisions',headers=AUTH).json()
    assert len(hist)==1 and hist[0]['assessment']['calibration_status']=='unscored'
    rev2=revision(client,hid,'mother_harriet',3,[parent(obs[0],obs[1],obs[0:2],obs[2:4])])
    assert rev2.status_code==201,rev2.text
    past=client.get(f'/api/v1/research/hypotheses/{hid}/options/mother_harriet/revisions',headers=AUTH).json()
    assert len(past)==2 and past[0]['revision_number']==2 and past[1]['revision_number']==1
    assert past[1]['edges'][0]['contradicting_observation_ids']==[]


def test_cycle_duplicates_and_unregistered_evidence_rejected(client):
    obs=observations(client);hid=hypothesis(client,obs)
    a=parent(obs[0],obs[1],[obs[0]])
    b={**a,'edge_key':'parent-2','from_observation_id':obs[1],'to_observation_id':obs[0]}
    assert revision(client,hid,'mother_harriet',1,[a,b]).status_code==422
    b={**a,'edge_key':'parent-2'}
    assert revision(client,hid,'mother_harriet',1,[a,b]).status_code==422
    other={**a,'supporting_observation_ids':[str(uuid4())]}
    assert revision(client,hid,'mother_harriet',1,[other]).status_code==422
    self_edge={**a,'to_observation_id':obs[0]}
    assert revision(client,hid,'mother_harriet',1,[self_edge]).status_code==422
    assert client.get(f'/api/v1/research/hypotheses/{hid}/graph',headers=AUTH).json()['version']==1


def test_source_dependence_warning_and_chronology(client):
    obs=observations(client);hid=hypothesis(client,obs)
    r=revision(client,hid,'mother_harriet',1,[parent(obs[1],obs[0],obs[2:4])])
    assert r.status_code==201,r.text
    branch=client.get(f'/api/v1/research/hypotheses/{hid}/graph',headers=AUTH).json()['options'][0]
    assert branch['option_key']=='mother_harriet'
    warnings=branch['revision']['assessment']['warnings']
    assert any('same' in m.lower() or 'share' in m.lower() for m in warnings)
    assert any('chronology' in m.lower() for m in warnings)
    assert any('census-only' in m.lower() for m in warnings)
    assert branch['revision']['assessment']['edge_assessments'][0]['distinct_declared_origin_groups']==1


def test_review_is_audited_and_never_writes_gramps(client):
    obs=observations(client);hid=hypothesis(client,obs)
    assert revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[0:2])]).status_code==201
    url=f'/api/v1/research/hypotheses/{hid}/options/mother_harriet/reviews'
    payload={'decision':'research_supported','reason':'Reviewed underlying synthetic documents',
             'expected_set_version':2}
    assert client.post(url,json=payload,headers=AUTH).status_code==403
    assert client.post(url,json={**payload,'expected_set_version':1},headers=WRITE).status_code==409
    r=client.post(url,json=payload,headers=WRITE)
    assert r.status_code==201,r.text
    assert r.json()['gramps_written'] is False
    assert client.post(url,json={**payload,'expected_set_version':3},headers=WRITE).status_code==409
    reviews=client.get(url,headers=AUTH).json()
    assert len(reviews)==1 and reviews[0]['decision']=='research_supported'


def test_no_unsourced_probability_or_gramps_write(client):
    obs=observations(client);hid=hypothesis(client,obs)
    edge={**parent(obs[0],obs[1],obs[:2]),'calibrated_probability':0.99}
    # Explicitly reject unverified, client-authored posterior numbers.
    r=revision(client,hid,'mother_harriet',1,[edge])
    assert r.status_code==422
    assert revision(client,hid,'mother_harriet',1,[parent(obs[0],obs[1],obs[:2])]).status_code==201
    graph=client.get(f'/api/v1/research/hypotheses/{hid}/graph',headers=AUTH).json()
    assert graph['calibrated_probabilities'] is None
    assert all(x['revision'] is None or x['revision']['assessment']['probability'] is None for x in graph['options'])
    assert graph['gramps_written'] is False
