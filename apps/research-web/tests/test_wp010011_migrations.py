"""Schema migrations 005->006->007 preserve historical source records."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.research.models import SourceDocument, OriginalSourceFamily, ResearchJob, ResearchTask
import pytest
ROOT=Path(__file__).resolve().parents[1]


def config(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c


def test_migrations_preserve_sources_and_reject_populated_downgrades(monkeypatch,tmp_path):
    url='sqlite+pysqlite:///'+str(tmp_path/'migrate.sqlite')
    monkeypatch.setenv('GEN_DB_URL',url)
    c=config(url)
    command.upgrade(c,'20261023_005')
    eng=create_engine(url)
    with Session(eng) as db:
        s=SourceDocument(provider='synthetic',provider_record_id='a1',title='Synthetic document',
            reference='ref1',access_method='user_import',licence='test_only',
            origin_group='test/sheet',acquisition_operator='tester')
        db.add(s);db.commit();original=s.id
    command.upgrade(c,'20261023_007')
    assert {'original_source_families','original_source_members','research_tasks'} <=set(inspect(eng).get_table_names())
    with Session(eng) as db:
        assert db.get(SourceDocument,original).reference=='ref1'
        family=OriginalSourceFamily(family_key='test/sheet',description='One original test page',
             rationale='Synthetic only source grouping for migration testing',created_by='tester')
        db.add(family)
        job=ResearchJob(mode='guided',objective='Synthetic task',created_by='tester',cost_limit_usd=1)
        db.add(job);db.flush()
        task=ResearchTask(job_id=job.id,task_key='task1',kind='local_review',source_provider='offline',
             input_json={},status='queued',reserved_cost_cents=0,spent_cost_cents=0)
        db.add(task);db.commit()
    with pytest.raises(RuntimeError,match='WP-011 downgrade'):
        command.downgrade(c,'20261023_006')
    with Session(eng) as db:
        db.query(ResearchTask).delete();db.commit()
    command.downgrade(c,'20261023_006')
    with pytest.raises(RuntimeError,match='WP-010 downgrade'):
        command.downgrade(c,'20261023_005')
    with Session(eng) as db:
        assert db.get(SourceDocument,original) is not None
    eng.dispose()
