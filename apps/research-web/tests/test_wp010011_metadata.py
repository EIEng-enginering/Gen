"""Rights-aware cache receipts and fail-closed provider access limits."""
from test_research_api import client, source, DOC, AUTH, WRITE


def test_cache_receipt_is_metadata_only_and_immutable(client):
    docid=source(client)
    receipt={'source_document_id':docid,'cache_key':'demo/folio/23-v1',
             'checksum_sha256':'a'*64,'acquisition_method':'user_import',
             'rights_basis':'User submitted scan held under private research rights'}
    r=client.post('/api/v1/research/source-cache-receipts',headers=WRITE,json=receipt)
    assert r.status_code==201,r.text
    assert r.json()['created'] is True
    assert client.post('/api/v1/research/source-cache-receipts',headers=WRITE,json=receipt).json()['created'] is False
    assert client.post('/api/v1/research/source-cache-receipts',headers=WRITE,
         json={**receipt,'checksum_sha256':'b'*64}).status_code==409
    rows=client.get('/api/v1/research/source-cache-receipts?source_document_id='+docid,headers=AUTH).json()
    assert len(rows)==1 and rows[0]['checksum_sha256']=='a'*64
    assert client.post('/api/v1/research/source-cache-receipts',headers=WRITE,
         json={**receipt,'cache_key':'different','acquisition_method':'approved_api'}).status_code==422


def test_provider_policy_never_unlocks_external_execution(client):
    data={'provider':'hypothetical_archive','access_mode':'approved_api',
          'permission_reference':'Synthetic research use only; no approved live credentials',
          'requests_per_day':100,'cooldown_seconds':5,'daily_budget_cents':100}
    assert client.post('/api/v1/research/source-provider-policies',headers=AUTH,json=data).status_code==403
    r=client.post('/api/v1/research/source-provider-policies',headers=WRITE,json=data)
    assert r.status_code==201,r.text
    assert r.json()['execution_enabled'] is False
    assert client.post('/api/v1/research/source-provider-policies',headers=WRITE,json=data).json()['created'] is False
    assert client.post('/api/v1/research/source-provider-policies',headers=WRITE,
        json={**data,'requests_per_day':5000}).status_code==409
    policies=client.get('/api/v1/research/source-provider-policies',headers=AUTH).json()
    assert len(policies)==1 and policies[0]['execution_enabled'] is False
