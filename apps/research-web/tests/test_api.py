"""Deterministic tests; no external Docker or internet required."""
import sys
from pathlib import Path
from base64 import b64encode
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import main


def auth_header(user='admin', password='test-password'):
    return {'Authorization': 'Basic '+b64encode(f'{user}:{password}'.encode()).decode()}


def test_health_public_and_minimal():
    result = TestClient(main.app).get('/health')
    assert result.status_code == 200
    assert set(result.json()) == {'status', 'component'}


def test_protected_page_requires_auth(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER', 'admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD', 'test-password')
    client = TestClient(main.app)
    assert client.get('/').status_code == 401
    assert client.get('/', headers=auth_header(password='wrong')).status_code == 401
    result = client.get('/', headers=auth_header())
    assert result.status_code == 200
    assert 'probabilistic matching and AI features are planned' in result.text


def test_status_and_features_distinguish_planned(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER', 'admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD', 'test-password')
    monkeypatch.setattr(main, 'database_check', lambda: True)
    client = TestClient(main.app)
    status = client.get('/api/v1/status', headers=auth_header())
    assert status.status_code == 200
    assert status.json()['research_database_connected'] is True
    features = client.get('/api/v1/features', headers=auth_header()).json()
    assert 'record_linkage' in features['planned_not_implemented']
    assert 'record_linkage' not in features['implemented']


def test_missing_credentials_are_not_accepted(monkeypatch):
    monkeypatch.delenv('GEN_ADMIN_USER', raising=False)
    monkeypatch.delenv('GEN_ADMIN_PASSWORD', raising=False)
    r = TestClient(main.app).get('/', headers=auth_header())
    assert r.status_code == 503


def test_untrusted_external_gramps_url_not_reflected(monkeypatch):
    monkeypatch.setenv('GEN_ADMIN_USER', 'admin')
    monkeypatch.setenv('GEN_ADMIN_PASSWORD', 'test-password')
    monkeypatch.setenv('GRAMPS_PUBLIC_URL', 'https://example.com/bad')
    r=TestClient(main.app).get('/', headers=auth_header())
    assert 'https://example.com/bad' not in r.text
    assert 'http://127.0.0.1:5055' in r.text
