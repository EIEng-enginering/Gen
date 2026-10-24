"""Disposable rev 007 -> 008 migration with evidence preservation and safe downgrade."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.research.models import SourceDocument,AIResearchRun
ROOT=Path(__file__).resolve().parents[1]

def test_ai_research_upgrade_preserves_source_and_blocks_history_loss(tmp_path,monkeypatch):
    url='sqlite+pysqlite:///'+str(tmp_path/'ai.sqlite')
    monkeypatch.setenv('GEN_DB_URL',url)
    config=Config(str(ROOT/'alembic.ini'))
    config.set_main_option('script_location',str(ROOT/'migrations'))
    command.upgrade(config,'20261023_007')
    eng=create_engine(url)
    with Session(eng) as db:
        source=SourceDocument(provider='fictional',provider_record_id='cheshire-1851',title='Synthetic census',
            reference='Fictional folio',access_method='user_import',licence='test_only',
            origin_group='fictional-original',acquisition_operator='fixture')
        db.add(source);db.commit();source_id=source.id
    command.upgrade(config,'20261024_008')
    assert 'ai_research_runs' in inspect(eng).get_table_names()
    with Session(eng) as db:
        assert db.get(SourceDocument,source_id).reference=='Fictional folio'
        row=AIResearchRun(id=uuid4(),created_by='tester',question='Which families?',mode='guided',
            surname='Oldham',county='Cheshire',scope_json={},answer_json={'summary':'unknown'},
            execution_status='deterministic_fallback')
        db.add(row);db.commit();saved=row.id
    with pytest.raises(RuntimeError,match='Refusing destructive downgrade'):
        command.downgrade(config,'20261023_007')
    with Session(eng) as db:
        assert db.get(AIResearchRun,saved).question=='Which families?'
        assert db.get(SourceDocument,source_id) is not None
    eng.dispose()
