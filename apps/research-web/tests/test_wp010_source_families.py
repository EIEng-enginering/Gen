"""Source independence warnings, duplicate review, privacy and immutable source rows."""
from test_research_api import client, source, DOC, AUTH, WRITE


def doc(client, key, origin, checksum=None):
    p={**DOC,'provider_record_id':key,'origin_group':origin,'title':'Synthetic parish entry '+key}
    if checksum:p['checksum_sha256']=checksum
    return source(client,p)


def test_family_requirements_idempotency_and_conflict(client):
    one=doc(client,'i-101','archive-1/page4')
    two=doc(client,'i-102','archive-1/page4')
    data={'family_key':'archive:vol-1:page-4','description':'Reproduced from one original source page',
          'rationale':'Independent catalogue references appear to reproduce the same original manuscript.'}
    assert client.post('/api/v1/research/source-families',headers=AUTH,json=data).status_code==403
    created=client.post('/api/v1/research/source-families',headers=WRITE,json=data)
    assert created.status_code==201,created.text
    fid=created.json()['id']
    assert client.post('/api/v1/research/source-families',headers=WRITE,json=data).json()['created'] is False
    assert client.post('/api/v1/research/source-families',headers=WRITE,json={**data,'description':'Changed'}).status_code==409
    attach={'document_id':one,'justification':'Compared the shelf marks and concluded that this is the same original document'}
    url=f'/api/v1/research/source-families/{fid}/members'
    assert client.post(url,headers=WRITE,json=attach).status_code==201
    assert client.post(url,headers=WRITE,json=attach).json()['created'] is False
    assert client.post(url,headers=WRITE,json={**attach,'justification':'Inconsistent alternate provenance justification'}).status_code==409
    two_url=f'/api/v1/research/source-families/{fid}/members'
    assert client.post(two_url,headers=WRITE,json={**attach,'document_id':two}).status_code==201
    assessment=client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
                 json={'document_ids':[one,two]})
    assert assessment.status_code==200,assessment.text
    assert assessment.json()['origin_group_count']==1
    assert assessment.json()['independence_verified'] is False
    assert assessment.json()['probability_assigned'] is False
    assert len(client.get(f'/api/v1/research/documents/{one}',headers=AUTH).json())>0


def test_reported_group_does_not_claim_corroboration(client):
    a=doc(client,'p100','same-manuscript/folio-3')
    b=doc(client,'p101','same-manuscript/folio-3')
    c=doc(client,'p102','different-manuscript/folio-11')
    r=client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
                  json={'document_ids':[a,b,c]})
    assert r.status_code==200
    assert r.json()['origin_group_count']==2
    assert any(g['classification']=='possible_dependent_originals' for g in r.json()['groups'])
    copies=client.get(f'/api/v1/research/documents/{a}/possible-copies',headers=AUTH)
    assert copies.status_code==200 and len(copies.json()['possible_copies'])==1
    assert copies.json()['automatically_merged'] is False


def test_source_group_does_not_fabricate_missing_records(client):
    a=doc(client,'missing-one','vol-unknown')
    r=client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
                  json={'document_ids':[a,'00000000-0000-0000-0000-000000000123']})
    assert r.status_code==404
    assert client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
                  json={'document_ids':[a,a]}).status_code==422
    assert client.post('/api/v1/research/source-dependence/assess',headers=AUTH,
                  json={'document_ids':[a]}).status_code==403


def test_overlapping_reported_and_attested_groups_stay_conservative(client):
    a=doc(client,'transitive-a','register-page-A')
    b=doc(client,'transitive-b','register-page-B')
    c=doc(client,'transitive-c','register-page-B')
    body={'family_key':'transitive-01','description':'Human-attested same original manuscript page',
          'rationale':'Researcher compared original shelfmarks and concluded repeated scan of one page.'}
    fid=client.post('/api/v1/research/source-families',headers=WRITE,json=body).json()['id']
    for did in [a,b]:
        r=client.post(f'/api/v1/research/source-families/{fid}/members',headers=WRITE,
             json={'document_id':did,'justification':'Original shelfmark and page number are identical after review'})
        assert r.status_code==201
    result=client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
             json={'document_ids':[a,b,c]})
    assert result.status_code==200 and result.json()['origin_group_count']==1
    assert result.json()['groups'][0]['classification']=='contains_human_attested_shared_original'


def test_single_attested_member_does_not_claim_shared_original(client):
    one=doc(client,'single-attested','distinct-original')
    body={'family_key':'single-attestation','description':'One original source under review',
          'rationale':'This synthetic source has no second catalogue record attested yet.'}
    fid=client.post('/api/v1/research/source-families',headers=WRITE,json=body).json()['id']
    assert client.post(f'/api/v1/research/source-families/{fid}/members',headers=WRITE,
        json={'document_id':one,'justification':'Single synthetic source pending comparison'}).status_code==201
    result=client.post('/api/v1/research/source-dependence/assess',headers=WRITE,
        json={'document_ids':[one]}).json()
    assert result['origin_group_count']==1
    assert result['groups'][0]['classification']=='original_relationship_unknown'
