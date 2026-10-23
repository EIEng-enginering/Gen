from app.research.gramps_readonly import probe

def test_gramp_probe_refuses_arbitrary_external_destination(monkeypatch):
    monkeypatch.setenv('GEN_GRAMPS_API_URL','https://evil.test/api')
    monkeypatch.setenv('GEN_GRAMPS_ACCESS_TOKEN','never-send-this')
    assert probe()['status']=='invalid_internal_endpoint'

def test_gramp_probe_does_not_expose_access_token_on_exception(monkeypatch):
    monkeypatch.setenv('GEN_GRAMPS_API_URL','http://127.0.0.1:1/api')
    monkeypatch.setenv('GEN_GRAMPS_ACCESS_TOKEN','SECRET-DO-NOT-LOG')
    assert 'SECRET-DO-NOT-LOG' not in str(probe())
