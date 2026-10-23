"""WP-015 local guided assistant: rigorous provenance, no network, no LLM."""
from uuid import uuid4
from test_research_api import client, source, appearance, AUTH, DOC, OBS

URL='/api/v1/research/assistant/answer'


def test_assistant_requires_auth_and_valid_bounds(client):
    assert client.post(URL,json={'question':'Who was the father?'}).status_code==401
    assert client.post(URL,headers=AUTH,json={'question':'Hi'}).status_code==422
    assert client.post(URL,headers=AUTH,json={'question':'Compare','mode':'madeup'}).status_code==422
    assert client.post(URL,headers=AUTH,json={'question':'Compare','observation_ids':[str(uuid4())]}).status_code==404
    assert client.post(URL,headers=AUTH,json={'question':'Compare','observation_ids':[str(uuid4())]*7}).status_code==422


def test_unselected_evidence_means_no_identification(client):
    r=client.post(URL,headers=AUTH,json={'question':'Are these the same person?','mode':'guided'})
    assert r.status_code==200
    v=r.json()
    assert v['citations']==[]
    assert 'No evidence' in v['summary']
    assert v['identity_asserted'] is False and v['relationship_asserted'] is False
    assert v['calibrated_probability'] is None
    assert v['llm_execution_enabled'] is False


def test_cited_guidance_in_all_modes_never_claims_truth(client):
    obs=appearance(client,source(client))
    for mode in ('autonomous','guided','conventional'):
        r=client.post(URL,headers=AUTH,json={'question':'Is this person the father of another ancestor?',
                      'mode':mode,'observation_ids':[obs]})
        assert r.status_code==200,r.text
        v=r.json()
        assert v['citations'][0]['observation_id']==obs
        assert 'Parish register' in v['citations'][0]['reference']
        assert len(v['research_steps'])>=4
        assert not v['relationship_asserted']
        assert not v['external_provider_execution_enabled']
        assert not v['accepted_tree_mutation_enabled']
        assert v['reasoning_origin']=='deterministic_local_rules_no_llm'
        if mode=='autonomous':assert 'disabled' in v['mode_explanation']


def test_malicious_source_text_not_rendered_as_html(client):
    obs=appearance(client,source(client),{**OBS,'person_name_verbatim':'<script>alert(1)</script>'})
    r=client.post(URL,headers=AUTH,json={'question':'Review the name and source',
                      'observation_ids':[obs]})
    assert r.status_code==200
    assert '<script>alert(1)</script>' in r.json()['summary']
    h=client.get('/workspace',headers=AUTH).text
    assert 'Cited summary' in h
    assert 'textContent' in h and '.innerHTML' not in h
    assert 'local research guide' in r.json()['warning']


def test_assistant_capabilities_do_not_claim_llm(client):
    v=client.get('/api/v1/research/assistant/capabilities',headers=AUTH).json()
    assert v['llm_model_active'] is False
    assert v['data_sent_to_cloud'] is False
