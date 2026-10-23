"""WP-016: bounded dashboard, review queue and budget accounting."""
from uuid import uuid4
from test_research_api import client, source, appearance, AUTH, WRITE
from test_graph_branches import hypothesis, revision, parent


def test_dashboard_needs_auth_and_counts_are_grounded(client):
    url='/api/v1/research/ops/dashboard'
    assert client.get(url).status_code==401
    v=client.get(url,headers=AUTH).json()
    assert v['counts']['documents']==0
    assert not v['operations_enabled']['external_providers']
    assert not v['operations_enabled']['cloud_ai']
    assert not v['operations_enabled']['gramps_writes']
    obs=appearance(client,source(client))
    v=client.get(url,headers=AUTH).json()
    assert v['counts']['documents']==1
    assert v['counts']['appearances']==1
    assert not v['providers']
    assert 'lease_token' not in str(v)


def test_job_budget_and_tasks_are_planning_only(client):
    r=client.post('/api/v1/research/jobs',headers=WRITE,
      json={'mode':'guided','objective':'Inspect synthetic birth records','cost_limit_usd':1.25})
    assert r.status_code==201,r.text
    jid=r.json()['id']
    task=client.post(f'/api/v1/research/jobs/{jid}/tasks',headers=WRITE,json={
      'task_key':'inspect-entry-0001','kind':'local_review','source_provider':'offline',
      'reserved_cost_cents':25,'input_json':{}})
    assert task.status_code==201,task.text
    data=client.get('/api/v1/research/ops/jobs/'+jid,headers=AUTH).json()
    assert data['budget_limit_cents']==125
    assert data['reserved_cents']==25
    assert data['reported_spent_cents']==0
    assert data['available_cents']==100
    assert data['task_status_counts']['queued']==1
    assert data['billable_requests_executed'] is False
    assert client.get('/api/v1/research/ops/jobs/'+str(uuid4()),headers=AUTH).status_code==404
    assert not any('lease_token' in s for s in str(data).split())


def test_review_queue_research_only(client):
    r=client.get('/api/v1/research/ops/reviews',headers=AUTH)
    assert r.status_code==200
    assert r.json()['gramps_change_plans']==[]
    assert r.json()['branch_revisions']==[]
    assert r.json()['write_permission_granted'] is False
    assert client.get('/api/v1/research/ops/reviews?limit=1000',headers=AUTH).status_code==422
    # A proposed branch without a research review appears in the queue.
    ids=[]
    for n in ('John One','Mary Two'):
        from test_research_api import DOC, OBS
        did=source(client,{**DOC,'provider_record_id':n,'origin_group':n})
        ids.append(appearance(client,did,{**OBS,'person_name_verbatim':n}))
    hid=hypothesis(client,ids)
    rr=revision(client,hid,'mother_harriet',1,[parent(ids[0],ids[1],ids)])
    assert rr.status_code==201,rr.text
    q=client.get('/api/v1/research/ops/reviews',headers=AUTH).json()
    assert len(q['branch_revisions'])==1
    assert q['branch_revisions'][0]['hypothesis_set_id']==hid
    assert q['write_permission_granted'] is False


def test_overview_policy_metadata_not_permission_to_execute(client):
    p=client.post('/api/v1/research/source-provider-policies',headers=WRITE,json={
       'provider':'example_catalogue','access_mode':'manual_only',
       'permission_reference':'Human supplied manual use only',
       'requests_per_day':0,'cooldown_seconds':0,'daily_budget_cents':0})
    assert p.status_code==201,p.text
    dashboard=client.get('/api/v1/research/ops/dashboard',headers=AUTH).json()
    assert dashboard['providers'][0]['provider']=='example_catalogue'
    assert dashboard['providers'][0]['execution_enabled'] is False
    assert dashboard['audit'] and 'details_json' not in dashboard['audit'][0]
