"""WP-008: fail-closed offline schema and readiness gates."""
from types import SimpleNamespace
from uuid import uuid4
from app.research.gramps_contract import inspect_openapi, plan_readiness
from test_gramps_plan import setup_client, AUTH


def test_openapi_contract_requires_three_get_routes():
    spec={'openapi':'3.0.3','paths':{'/api/metadata/':{'get':{}},'/api/people/{id}':{'get':{},'put':{}},
      '/api/families/{id}':{'get':{},'post':{}}}}
    result=inspect_openapi(spec)
    assert result['read_route_shape_complete'] is True
    assert result['accepted_tree_write_enabled'] is False
    assert result['response_shapes_verified'] is False
    assert not result['future_write_eligible']
    spec['paths'].pop('/api/families/{id}')
    assert inspect_openapi(spec)['read_routes']['family'] is False


def test_openapi_invalid_and_many_routes():
    import pytest
    with pytest.raises(ValueError):inspect_openapi({'swagger':'2.0','paths':[]})
    with pytest.raises(ValueError):inspect_openapi({'openapi':'4.0','paths':{}})
    with pytest.raises(ValueError):inspect_openapi({'openapi':'3.0.1','paths':{str(x):{} for x in range(6001)}})


def test_readiness_never_authorizes_write():
    plan=SimpleNamespace(id=uuid4(),digest_sha256='a'*64)
    decision=SimpleNamespace(decision='approve_for_future_validation')
    validation=SimpleNamespace(plan_digest='a'*64,result_json={
       'status':'READ_ONLY_OBSERVATION_COMPLETE','snapshot_sha256':'b'*64})
    info=plan_readiness(plan,decision,validation,current=True)
    assert info['latest_read_observation_available']
    assert not info['execution_enabled']
    assert 'upstream_atomic_concurrency_not_verified' in info['blockers']
    assert not plan_readiness(plan,None,None,current=False)['future_write_eligible']


def test_contract_api_authenticated_and_size_limited(setup_client):
    client,_=setup_client
    assert client.get('/api/v1/research/gramps/execution-policy').status_code==401
    r=client.get('/api/v1/research/gramps/execution-policy',headers=AUTH)
    assert r.status_code==200 and r.json()['accepted_tree_mutation_enabled'] is False
    spec={'swagger':'2.0','paths':{'/people/{handle}':{'get':{}},'/families/{handle}':{'get':{}},
        '/metadata/':{'get':{}}}}
    r=client.post('/api/v1/research/gramps/contracts/review',headers=AUTH,json=spec)
    assert r.status_code==200,r.text
    assert r.json()['read_route_shape_complete'] is True
    r=client.post('/api/v1/research/gramps/contracts/review',headers=AUTH,content=b'X'*(1024*1024+1))
    assert r.status_code==413
    r=client.get(f'/api/v1/research/gramps/plans/{uuid4()}/execution-readiness',headers=AUTH)
    assert r.status_code==404
