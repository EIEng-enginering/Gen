"""Guest-only, bounded Gramps context using entirely fictional tree objects."""
import base64
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.research import gramps_context as gc
from app.research import ai_research_engine as engine
from app.research.models import Base


def token(permissions):
    body = base64.urlsafe_b64encode(json.dumps({'permissions': permissions,
                                               'exp': time.time() + 900}).encode()).decode().rstrip('=')
    return 'header.' + body + '.signature'


def oldham_tree():
    def person(handle, first):
        return {'handle': handle, 'gramps_id': 'I' + handle,
                'private': False, 'primary_name': {'first_name': first,
                    'surname_list': [{'surname': 'Oldham', 'primary': True}]},
                'event_ref_list': [], 'family_list': [], 'parent_family_list': []}
    selected = person('p1', 'Alice')
    selected['event_ref_list'] = [{'ref': 'e1', 'citation_list': []},
                                  {'ref': 'e2', 'citation_list': []}]
    selected['family_list'] = ['f1']
    return {
        '/api/metadata/': {'gramps_webapi': {'version': '3.24.0'}},
        '/api/search/': [{'handle': 'p1', 'object': selected, 'object_type': 'person'}],
        '/api/people/p1': selected,
        '/api/people/p2': person('p2', 'Robert'),
        '/api/people/p3': person('p3', 'Child'),
        '/api/events/e1': {'handle': 'e1', 'gramps_id': 'E1', 'private': False,
                           'type': 'Census', 'date': {'year': 1851, 'text': ''},
                           'description': 'Fictional Cheshire household',
                           'place': 'pl1', 'citation_list': ['c1']},
        '/api/events/e2': {'handle': 'e2', 'gramps_id': 'E2', 'private': False,
                           'type': 'Birth', 'date': {'year': 1820, 'text': ''},
                           'description': '', 'place': None, 'citation_list': []},
        '/api/places/pl1': {'handle': 'pl1', 'private': False,
                            'name': {'value': 'Fictional Cheshire'}},
        '/api/citations/c1': {'handle': 'c1', 'private': False,
                              'page': 'Folio 24', 'source_handle': 's1'},
        '/api/sources/s1': {'handle': 's1', 'private': False,
                            'title': 'Fictional original census'},
        '/api/families/f1': {'handle': 'f1', 'gramps_id': 'F1', 'private': False,
                             'father_handle': 'p2', 'mother_handle': 'p1',
                             'child_ref_list': [{'ref': 'p3'}]},
    }


@pytest.fixture
def fake_gramps(monkeypatch):
    objects = oldham_tree()
    calls = []
    monkeypatch.setenv('GEN_GRAMPS_READ_USER', 'fictional_guest')
    monkeypatch.setenv('GEN_GRAMPS_READ_PASSWORD', 'fictional_password')
    monkeypatch.setenv('GEN_GRAMPS_API_URL', 'http://grampsweb:5000/api')
    gc._TOKEN_CACHE.update({'credential_digest': None, 'token': None, 'expires_at': 0})
    real_client = httpx.Client
    auth_token = token(['EditOwnUser'])

    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == '/api/token/':
            assert request.method == 'POST'
            assert json.loads(request.content)['username'] == 'fictional_guest'
            return httpx.Response(200, json={'access_token': auth_token})
        assert request.method == 'GET'
        assert request.headers['Authorization'] == 'Bearer ' + auth_token
        value = objects.get(request.url.path)
        return httpx.Response(200, json=value) if value is not None else httpx.Response(404)

    def client(*args, **kwargs):
        kwargs.pop('trust_env', None)
        return real_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(gc.httpx, 'Client', client)
    return objects, calls


def test_guest_person_search_and_cited_context(fake_gramps):
    _, calls = fake_gramps
    found = gc.search_people('Oldham')
    assert found['results'] == [{'handle': 'p1', 'gramps_id': 'Ip1', 'name': 'Alice Oldham'}]
    assert found['selection_is_exhaustive'] is False
    context = gc.read_person_context('p1')
    assert context['person']['name'] == 'Alice Oldham'
    assert len(context['events']) == 2
    assert context['events'][0]['place'] == 'Fictional Cheshire'
    assert context['event_citation_count'] == 1
    assert context['events'][1]['citations'] == []
    assert len(context['related_people']) == 2
    packets = gc.cited_event_packets(context)
    assert len(packets) == 1
    assert packets[0]['citation']['reference'] == 'Fictional original census Folio 24'
    assert packets[0]['record']['event'] == 'Census'
    assert {method for method, _ in calls} == {'GET', 'POST'}
    assert calls.count(('POST', '/api/token/')) == 1
    assert all(method == 'GET' for method, path in calls if path != '/api/token/')
    assert context['accepted_tree_mutation_enabled'] is False


def test_invalid_search_and_handle_are_blocked_before_network(fake_gramps):
    _, calls = fake_gramps
    with pytest.raises(gc.ContextBlocked):
        gc.search_people('Oldham* OR private')
    with pytest.raises(gc.ContextBlocked):
        gc.read_person_context('../users')
    assert calls == []


def test_guest_permission_and_version_changes_fail_closed(fake_gramps, monkeypatch):
    objects, _ = fake_gramps
    with pytest.raises(gc.ContextBlocked, match='gramps_guest_permission_mismatch'):
        gc._guest_permissions(token(['EditOwnUser', 'AddObject']))
    objects['/api/metadata/']['gramps_webapi']['version'] = '3.25.0'
    with pytest.raises(gc.ContextBlocked, match='gramps_version_not_validated'):
        gc.search_people('Oldham')


def test_only_cited_tree_event_reaches_model(fake_gramps, monkeypatch):
    context = gc.read_person_context('p1')
    packet_id = gc.cited_event_packets(context)[0]['observation_id']
    seen = {}

    def model(packets, question, mode):
        seen['packets'] = packets
        return {'interpretation': 'This fictional entry requires review against the original census.',
                'cited_observation_ids': [packet_id],
                'uncertainties': ['Identity is not proven'],
                'next_steps': ['Inspect the original folio']}

    monkeypatch.setattr(engine, '_request_model', model)
    monkeypatch.setattr(engine, 'configured_model', lambda: 'fictional-local-model')
    db_engine = create_engine('sqlite+pysqlite://', connect_args={'check_same_thread': False},
                              poolclass=StaticPool)
    Base.metadata.create_all(db_engine)
    try:
        with Session(db_engine) as db:
            answer = engine.answer(db, 'Review fictional Oldham evidence', 'guided', '', '',
                                   None, None, [], gramps_context=context)
        assert answer['model_execution'] == 'local_model'
        assert answer['model_cited_tree_evidence_ids'] == [packet_id]
        assert answer['model_cited_observation_ids'] == []
        assert len(seen['packets']) == 1
        assert seen['packets'][0]['record']['event'] == 'Census'
        assert answer['gramps_context']['events'][1]['citations'] == []
        assert answer['accepted_tree_mutation_enabled'] is False
    finally:
        db_engine.dispose()


def test_new_gramps_routes_require_24gen_auth():
    with TestClient(app) as client:
        assert client.get('/api/v1/research/ai/gramps/search?q=Oldham').status_code == 401
        assert client.get('/api/v1/research/ai/gramps/people/p1').status_code == 401


def test_cheshire_provider_leads_remain_manual():
    leads = engine.manual_leads('Oldham', 'Cheshire')
    assert {x['provider'] for x in leads} >= {'Cheshire BMD', 'Cheshire Archives and Local Studies'}
    assert all(x['access'] == 'manual_only' and x['status'] == 'not_searched' for x in leads)
