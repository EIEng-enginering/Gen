"""Synthetic Gramps REST responses only: no living person data or external calls."""
import json
import httpx
import pytest
from app.research import gramps_live_read as lib


def preview(kind='propose_parent_child_link'):
    return {'digest_sha256':'a'*64, 'actions':[{'action':kind,'edge_key':'edge-1',
      'from_handle_claimed':'parent_1','to_handle_claimed':'child_1'}]}


def handler(request):
    assert request.method == 'GET'
    assert request.headers['authorization'] == 'Bearer FAKE_PRIVATE_TOKEN'
    assert request.url.host == 'grampsweb'
    objects={
      '/api/metadata/': {'version':'fixture'},
      '/api/people/parent_1': {'handle':'parent_1','gramps_id':'I0001','change':100,
                               'family_list':['F0001'], 'parent_family_list':[],'private_name':'NOT_FOR_LOCAL_STORAGE'},
      '/api/people/child_1': {'handle':'child_1','gramps_id':'I0002','change':101,
                               'family_list':[], 'parent_family_list':['F0001']},
      '/api/people/gramps-person-1': {'handle':'gramps-person-1', 'family_list':['F0002'], 'parent_family_list':[], 'change':80},
      '/api/people/gramps-person-2': {'handle':'gramps-person-2', 'family_list':[], 'parent_family_list':['F0002'], 'change':81},
      '/api/families/F0002': {'handle':'F0002', 'father_handle':'gramps-person-1', 'mother_handle':None, 'child_ref_list':[{'ref':'gramps-person-2'}], 'change':53},
      '/api/families/F0001': {'handle':'F0001','father_handle':'parent_1','mother_handle':None,
                               'child_ref_list':[{'ref':'child_1'}], 'change':50},
    }
    return httpx.Response(200,json=objects[request.url.path])


def installed(monkeypatch, h=handler):
    monkeypatch.setenv('GEN_GRAMPS_API_URL','http://grampsweb:5000/api')
    monkeypatch.setenv('GEN_GRAMPS_ACCESS_TOKEN','FAKE_PRIVATE_TOKEN')
    monkeypatch.setattr(lib,'make_client',lambda: httpx.Client(transport=httpx.MockTransport(h),trust_env=False))


def test_read_only_relationship_observation_no_private_data(monkeypatch):
    installed(monkeypatch)
    v=lib.read_plan_snapshot(preview())
    assert v['status']=='READ_ONLY_OBSERVATION_COMPLETE'
    assert v['findings'][0]['observed_upstream_status']=='already_linked'
    assert v['people_checked']==2 and v['related_families_checked']==1
    assert len(v['snapshot_sha256'])==64 and v['execution_enabled'] is False
    assert 'NOT_FOR_LOCAL_STORAGE' not in json.dumps(v)
    assert 'FAKE_PRIVATE_TOKEN' not in json.dumps(v)


def test_spouse_not_seen_and_no_writes(monkeypatch):
    installed(monkeypatch)
    v=lib.read_plan_snapshot(preview('propose_spouse_link'))
    assert v['findings'][0]['observed_upstream_status']=='not_seen_in_related_families'
    assert not v['future_write_eligible']

@pytest.mark.parametrize('url',['https://example.com/api','http://username:pw@grampsweb:5000/api',
     'http://localhost:5678/api?a=1','http://grampsweb:5001/api','http://grampsweb:5000/api/../evil',
     'http://169.254.169.254/api'])
def test_disallow_non_internal_urls(monkeypatch,url):
    monkeypatch.setenv('GEN_GRAMPS_API_URL',url)
    monkeypatch.setenv('GEN_GRAMPS_ACCESS_TOKEN','FAKE_PRIVATE_TOKEN')
    with pytest.raises(lib.UpstreamBlocked): lib.read_plan_snapshot(preview())


def test_missing_token_blocks_before_network(monkeypatch):
    monkeypatch.delenv('GEN_GRAMPS_ACCESS_TOKEN',raising=False)
    with pytest.raises(lib.UpstreamBlocked,match='token_not_configured'):
        lib.read_plan_snapshot(preview())


def test_untrusted_handle_rejected(monkeypatch):
    installed(monkeypatch)
    bad=preview();bad['actions'][0]['from_handle_claimed']='../../etc/secret'
    with pytest.raises(lib.UpstreamBlocked,match='invalid_handle'):
        lib.read_plan_snapshot(bad)


def test_http_redirect_refused(monkeypatch):
    installed(monkeypatch,lambda _:httpx.Response(302, headers={'location':'https://example.com/'}))
    with pytest.raises(lib.UpstreamBlocked,match='upstream_http_error'):
        lib.read_plan_snapshot(preview())


def test_unknown_upstream_shape_rejected(monkeypatch):
    def bad(req):
        j=handler(req)
        if req.url.path=='/api/people/child_1':
            return httpx.Response(200,json={'handle':'child_1','family_list':[]})
        return j
    installed(monkeypatch,bad)
    with pytest.raises(lib.UpstreamBlocked,match='person_missing_family_references'):
        lib.read_plan_snapshot(preview())


def test_response_size_limit(monkeypatch):
    installed(monkeypatch,lambda _:httpx.Response(200,content=b'X'*(lib.MAX_BYTES+1),headers={'content-type':'application/json'}))
    with pytest.raises(lib.UpstreamBlocked,match='upstream_response_too_large'):
        lib.read_plan_snapshot(preview())


def test_no_entire_person_data_in_history(monkeypatch):
    installed(monkeypatch)
    a=lib.read_plan_snapshot(preview())
    b=lib.read_plan_snapshot(preview())
    assert a['snapshot_sha256']==b['snapshot_sha256']
