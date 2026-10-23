"""Static topology assertions. They do not replace live Docker acceptance."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ROOT / 'deploy' / 'compose.yaml'


def test_compose_has_local_only_web_ports_and_persistent_state():
    cfg = yaml.safe_load(COMPOSE.read_text(encoding='utf-8'))
    services = cfg['services']
    assert {'grampsweb', 'grampsweb_celery', 'grampsweb_redis', 'research_db', 'research_web'} <= set(services)
    for item in ('grampsweb', 'research_web'):
        assert all(str(p).startswith('127.0.0.1:') for p in services[item]['ports'])
    for item in ('research_db', 'grampsweb_redis'):
        assert 'ports' not in services[item]
    assert len(cfg['volumes']) >= 8
    assert 'research_postgres' in cfg['volumes']
    assert 'gramps_db' in cfg['volumes'] and 'gramps_media' in cfg['volumes']
