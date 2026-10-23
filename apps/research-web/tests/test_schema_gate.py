import pytest
from sqlalchemy import create_engine,text
from alembic.config import Config
from alembic import command
from app.research.db import close_engine
from app.research.schema_gate import check_schema

def test_gate_initialises_empty_and_refuses_unknown_existing(tmp_path,monkeypatch):
    db=tmp_path/'first.sqlite3'
    monkeypatch.setenv('GEN_DB_URL','sqlite:///'+str(db))
    close_engine()
    assert check_schema()=='initialized_empty_database'
    assert check_schema()=='schema_current'
    close_engine()
    another=tmp_path/'legacy.sqlite3'
    monkeypatch.setenv('GEN_DB_URL','sqlite:///'+str(another))
    engine=create_engine('sqlite:///'+str(another))
    with engine.begin() as c:c.execute(text('CREATE TABLE legacy_family_records (id INTEGER PRIMARY KEY)'))
    engine.dispose();close_engine()
    with pytest.raises(RuntimeError,match='refusing automatic upgrade'):
        check_schema()
    close_engine()
