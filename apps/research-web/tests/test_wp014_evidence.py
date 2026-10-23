"""WP-014 evidence comparison: citations, transcriptions, no image transfers."""
from uuid import uuid4
from test_research_api import client, source, appearance, AUTH, WRITE, DOC, OBS


def test_requires_auth_cites_original_and_separates_revisions(client):
    did=source(client);oid=appearance(client,did)
    assert client.get(f'/api/v1/research/evidence/observations/{oid}/dossier').status_code==401
    r=client.post(f'/api/v1/research/observations/{oid}/transcriptions',headers=WRITE,
                  json={'text':'John Carter baptized [second reading]','reason':'Rescanned original source'})
    assert r.status_code==201,r.text
    r=client.get(f'/api/v1/research/evidence/observations/{oid}/dossier',headers=AUTH)
    assert r.status_code==200,r.text
    d=r.json()
    assert d['citation']['document_id']==did
    assert 'Parish register' in d['citation']['reference']
    assert d['record']['initial_transcription']=='John Carter baptized'
    assert d['latest_reading']=='John Carter baptized [second reading]'
    assert len(d['revision_history'])==2
    assert d['record']['name_verbatim']=='John Carter'
    assert d['accepted_tree_write'] is False


def test_different_literal_readings_not_equated_with_identity(client):
    first=appearance(client,source(client))
    did=source(client,{**DOC,'provider_record_id':'a-002','origin_group':'another_original'})
    second=appearance(client,did,{**OBS,'person_name_verbatim':'Jon Carter','event_date_verbatim':'June 1791'})
    r=client.post('/api/v1/research/evidence/compare',headers=AUTH,
                  json={'observation_ids':[first,second]})
    assert r.status_code==200,r.text
    payload=r.json()
    assert len(payload['observations'])==2
    assert 'name_verbatim' in {x['field'] for x in payload['literal_differences']}
    assert payload['source_independence_verified'] is False
    assert len(payload['source_dependence_groups'])==2
    assert payload['calibrated_probability'] is None
    assert payload['accepted_tree_mutation_enabled'] is False


def test_cited_shared_original_is_one_possible_group(client):
    a=appearance(client,source(client))
    did=source(client,{**DOC,'provider_record_id':'a-003','origin_group':'unrelated_catalogue_label'})
    b=appearance(client,did,{**OBS,'observation_key':'line2'})
    fam=client.post('/api/v1/research/source-families',headers=WRITE,json={
        'family_key':'folio:united-1','description':'One original folio',
        'rationale':'Manually compared original register and reproduced folio.'})
    assert fam.status_code==201,fam.text
    family_id=fam.json()['id']
    docs=[client.get('/api/v1/research/observations/'+o,headers=AUTH).json()['document_id'] for o in (a,b)]
    for doc_id in docs:
        r=client.post(f'/api/v1/research/source-families/{family_id}/members',headers=WRITE,
            json={'document_id':doc_id,'justification':'Manual comparison of original historical folio.'})
        assert r.status_code==201,r.text
    result=client.post('/api/v1/research/evidence/compare',headers=AUTH,
                       json={'observation_ids':[a,b]}).json()
    assert len(result['source_dependence_groups'])==1
    assert not result['source_independence_verified']


def test_missing_duplicate_and_excess_observations_rejected(client):
    a=appearance(client,source(client))
    url='/api/v1/research/evidence/compare'
    assert client.post(url,headers=AUTH,json={'observation_ids':[a,a]}).status_code==422
    assert client.post(url,headers=AUTH,json={'observation_ids':[a,str(uuid4())]}).status_code==404
    assert client.post(url,headers=AUTH,json={'observation_ids':[a]*7}).status_code==422
    assert client.get('/api/v1/research/evidence/observations/'+str(uuid4())+'/dossier',headers=AUTH).status_code==404
    caps=client.get('/api/v1/research/evidence/capabilities',headers=AUTH).json()
    assert caps['source_image_server_fetch_enabled'] is False
    assert caps['source_image_server_storage_enabled'] is False


def test_local_image_workspace_never_uploads(client):
    r=client.get('/workspace',headers=AUTH)
    assert r.status_code==200
    assert 'Local-only image inspection' in r.text
    assert 'URL.createObjectURL' in r.text
    assert 'URL.revokeObjectURL' in r.text
    assert '.innerHTML' not in r.text
    assert "image/webp" in r.text
