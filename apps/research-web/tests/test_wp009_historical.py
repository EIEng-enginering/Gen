"""WP-009: source-backed local historical places and honest candidate scoring."""
from copy import deepcopy
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.research.models import HistoricalPlace
from test_research_api import client,source,appearance,DOC,OBS,AUTH,WRITE
from app.research.historical_linkage import candidate_assessment
from types import SimpleNamespace


def place_payload(did):
    return {'source_document_id':did,'place_key':'test-parish-01',
        'label':'Fictional St Anselm Parish','county_label':'Fictionshire',
        'jurisdiction_type':'parish','valid_from_year':1720,'valid_to_year':1900,
        'aliases_json':['St. Anselm','Anselm Par.'],
        'evidence_note':'Synthetic parish jurisdiction register supplied for a test'}


def test_place_requires_original_source_and_explicit_intent(client):
    bad=place_payload(str(uuid4()))
    assert client.post('/api/v1/research/historical-places',headers=WRITE,json=bad).status_code==422
    did=source(client)
    good=place_payload(did)
    assert client.post('/api/v1/research/historical-places',headers=AUTH,json=good).status_code==403
    r=client.post('/api/v1/research/historical-places',headers=WRITE,json=good)
    assert r.status_code==201,r.text
    pid=r.json()['id']
    r=client.post('/api/v1/research/historical-places',headers=WRITE,json=good)
    assert r.status_code==201 and r.json()=={'id':pid,'created':False}
    assert client.post('/api/v1/research/historical-places',headers=WRITE,
         json={**good,'county_label':'Other'}).status_code==409
    r=client.get('/api/v1/research/historical-places?q=Fictional&year=1800',headers=AUTH)
    assert r.status_code==200 and len(r.json())==1
    assert client.get('/api/v1/research/historical-places?year=1920',headers=AUTH).json()==[]


def test_place_rejects_bad_ranges_and_duplicate_aliases(client):
    did=source(client);data=place_payload(did)
    assert client.post('/api/v1/research/historical-places',headers=WRITE,
        json={**data,'valid_to_year':1600}).status_code==422
    assert client.post('/api/v1/research/historical-places',headers=WRITE,
        json={**data,'aliases_json':['St Anselm','st anselm']}).status_code==422


def test_historical_matching_ranks_without_inventing_probability(client):
    a=appearance(client,source(client))
    b=appearance(client,source(client,{**DOC,'provider_record_id':'diff-page','origin_group':'vol-2'}),
       {**OBS,'observation_key':'line2','given_names_verbatim':'Jno','person_name_verbatim':'Jno Carter',
        'event_type':'census','earliest_iso':'1841-06-01','latest_iso':'1841-06-01',
        'additional_json':{'reported_age':35}})
    r=client.get(f'/api/v1/research/observations/{a}/historical-candidates',headers=AUTH)
    assert r.status_code==200,r.text
    assert any(x['observation_id']==b for x in r.json()['candidates'])
    assert r.json()['calibration_status']=='NOT_CALIBRATED'
    assert r.json()['candidates'][0]['calibrated_probability'] is None
    assert r.json()['accepted_tree_written'] is False


def test_1841_census_ages_respond_to_uncertainty():
    doc=uuid4()
    def example(name,year,age,doc_id=doc):
        return SimpleNamespace(surname_verbatim='Carter',given_names_verbatim=name,
          location_verbatim='Leeds',historical_place_ref=None,
          event_type='census',earliest_iso=f'{year}-01-01',additional_json={'reported_age':age},
          document_id=doc_id)
    a=example('William',1841,30)
    b=example('Wm',1851,55)
    r=candidate_assessment(a,b,'p1','p2')
    assert 'non-overlapping' in ' '.join(r['warnings'])
    assert r['features']['reported_census_birth_range_a']['age_max']==34
    c=example('William',1851,38)
    r=candidate_assessment(a,c,'same','same')
    assert r['features']['shared_original_source_group'] is True
    assert r['calibrated_probability'] is None


def test_missing_surname_is_refused_for_bounded_search(client):
    did=source(client)
    oid=appearance(client,did,{**OBS,'surname_verbatim':'','person_name_verbatim':'Anonymous'})
    r=client.get(f'/api/v1/research/observations/{oid}/historical-candidates',headers=AUTH)
    assert r.status_code==200 and r.json()['candidates']==[]
    assert r.json()['accepted_tree_written'] is False


def test_workspace_exposes_historical_citations(client):
    r=client.get('/workspace',headers=AUTH)
    assert r.status_code==200
    assert 'Historic parish / place evidence' in r.text
    assert 'historical-candidates' in r.text
