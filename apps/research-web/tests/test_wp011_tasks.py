"""Supervised job tasks; no network, billing or Gramps write execution."""
from test_research_api import client, AUTH, WRITE


def create_job(client,mode='guided',limit=1):
    r=client.post('/api/v1/research/jobs',headers=WRITE,
           json={'mode':mode,'objective':'Review synthetic parish record','cost_limit_usd':limit})
    assert r.status_code==201,r.text
    return r.json()['id']


def create_task(client,job,key='local-one',kind='local_review',cost=0):
    return client.post(f'/api/v1/research/jobs/{job}/tasks',headers=WRITE,
      json={'task_key':key,'kind':kind,'source_provider':'test_offline','reserved_cost_cents':cost,
            'input_json':{'record_ref':'synthetic-only'}})


def test_task_budget_idempotency_and_manual_source_gate(client):
    job=create_job(client,limit=1)
    a=create_task(client,job,cost=90)
    assert a.status_code==201,a.text
    assert a.json()['created'] is True
    assert create_task(client,job,cost=90).json()['created'] is False
    assert create_task(client,job,cost=91).status_code==409
    assert create_task(client,job,key='second',cost=11).status_code==409
    manual=create_task(client,job,key='manual-bmd',kind='manual_lookup',cost=5)
    assert manual.status_code==201
    r=client.post(f'/api/v1/research/jobs/{job}/tasks/{manual.json()["id"]}/claim',headers=WRITE,
        json={'worker_name':'tester'})
    assert r.status_code==403
    totals=client.get(f'/api/v1/research/jobs/{job}/budget',headers=AUTH).json()
    assert totals['outstanding_reservations_cents']==95
    assert totals['available_cents']==5
    assert totals['external_execution_enabled'] is False


def test_worker_lease_auth_wrong_token_and_repeat_complete(client):
    job=create_job(client,limit=1)
    task=create_task(client,job,cost=25).json()['id']
    url=f'/api/v1/research/jobs/{job}/tasks/{task}'
    assert client.post(url+'/claim',headers=AUTH,json={'worker_name':'test-worker'}).status_code==403
    r=client.post(url+'/claim',headers=WRITE,json={'worker_name':'test-worker'})
    assert r.status_code==200,r.text
    token=r.json()['lease_token']
    assert r.json()['status']=='leased'
    assert client.post(url+'/claim',headers=WRITE,json={'worker_name':'test-worker'}).status_code==409
    body={'lease_token':'invalid-token-must-be-at-least-thirty-characters','completion_key':'job-commit-a',
          'spent_cost_cents':20,'result':'complete'}
    assert client.post(url+'/finish',headers=WRITE,json=body).status_code==403
    body['lease_token']=token
    assert client.post(url+'/finish',headers=WRITE,json={**body,'spent_cost_cents':26}).status_code==409
    done=client.post(url+'/finish',headers=WRITE,json=body)
    assert done.status_code==200 and done.json()['idempotent'] is False
    again=client.post(url+'/finish',headers=WRITE,json=body)
    assert again.status_code==200 and again.json()['idempotent'] is True
    assert client.post(url+'/finish',headers=WRITE,json={**body,'completion_key':'new-key'}).status_code==409
    totals=client.get(f'/api/v1/research/jobs/{job}/budget',headers=AUTH).json()
    assert totals['task_charges_cents']==20
    assert totals['outstanding_reservations_cents']==0
    assert totals['available_cents']==80
    assert client.get('/api/v1/research/jobs',headers=AUTH).json()[0]['spent_usd']==0.2


def test_autonomous_remains_paused_and_no_network_executor(client):
    job=create_job(client,mode='autonomous',limit=0)
    task=create_task(client,job,key='local-01').json()['id']
    assert client.post(f'/api/v1/research/jobs/{job}/tasks/{task}/claim',headers=WRITE,
                json={'worker_name':'tester'}).status_code==409
    r=create_task(client,job,key='api-lookup',kind='approved_api_request')
    assert r.status_code==201
    assert client.post(f'/api/v1/research/jobs/{job}/tasks/{r.json()["id"]}/claim',headers=WRITE,
                 json={'worker_name':'tester'}).status_code==409
    assert client.post(f'/api/v1/research/jobs/{job}/control',headers=WRITE,json={'action':'resume'}).status_code==200
    assert client.post(f'/api/v1/research/jobs/{job}/tasks/{r.json()["id"]}/claim',headers=WRITE,
                 json={'worker_name':'tester'}).status_code==403


def test_expired_lease_reclaim_rejects_stale_token(client,monkeypatch):
    from datetime import timedelta
    from app.research import task_queue_api
    job=create_job(client,limit=1)
    task=create_task(client,job,cost=10).json()['id']
    url=f'/api/v1/research/jobs/{job}/tasks/{task}'
    first=client.post(url+'/claim',headers=WRITE,
        json={'worker_name':'reviewer-one','lease_seconds':30}).json()
    original_now=task_queue_api.utc_now()
    monkeypatch.setattr(task_queue_api,'utc_now',lambda:original_now+timedelta(seconds=31))
    second=client.post(url+'/claim',headers=WRITE,
        json={'worker_name':'reviewer-two','lease_seconds':30})
    assert second.status_code==200,second.text
    assert second.json()['attempt']==2
    assert second.json()['lease_token']!=first['lease_token']
    old={'lease_token':first['lease_token'],'completion_key':'stale-attempt',
         'spent_cost_cents':0,'result':'complete'}
    assert client.post(url+'/finish',headers=WRITE,json=old).status_code==403
    assert client.post(url+'/finish',headers=WRITE,
        json={**old,'lease_token':second.json()['lease_token']}).status_code==200
