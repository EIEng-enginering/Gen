"""WP-006 schema migration works after WP-005 without dropping older evidence."""
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from app.research.models import SourceDocument, HypothesisSet, HypothesisOption, BranchRevision, GrampsChangePlan

ROOT=Path(__file__).resolve().parents[1]


def config(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c


def test_002_to_003_migration_preserves_old_records_and_refuses_destructive_rollback(monkeypatch,tmp_path):
    path=tmp_path/'research.sqlite';url='sqlite+pysqlite:///'+str(path)
    monkeypatch.setenv('GEN_DB_URL',url)
    cfg=config(url)
    command.upgrade(cfg,'20261023_002')
    engine=create_engine(url)
    with Session(engine) as s:
        doc=SourceDocument(provider='test',provider_record_id='source-1',title='Original document',
          reference='T1',access_method='user_import',licence='fixture',origin_group='source-1',acquisition_operator='tester')
        s.add(doc);s.flush()
        group=HypothesisSet(title='Test parent',subject_description='Test',relation_type='biological_parent',created_by='tester')
        s.add(group);s.flush()
        option=HypothesisOption(hypothesis_set_id=group.id,option_key='candidate',description='test')
        s.add(option);s.flush()
        rev=BranchRevision(hypothesis_set_id=group.id,option_id=option.id,revision_number=1,
           rationale='Research pending further source validation',created_by='tester')
        s.add(rev);s.commit()
        did=doc.id;gid=group.id;rid=rev.id;oid=option.id
    command.upgrade(cfg,'head')
    with Session(engine) as s:
        assert s.get(SourceDocument,did).title=='Original document'
        assert 'gramps_change_plans' in inspect(engine).get_table_names()
        plan=GrampsChangePlan(idempotency_key='migration-test-001',hypothesis_set_id=gid,option_id=oid,
           branch_revision_id=rid,set_version_after_creation=2,digest_sha256='a'*64,
           preview_json={'accepted_tree_write':False},operator_note='Test preview cannot be executed',created_by='tester')
        s.add(plan);s.commit()
    engine.dispose()
    with pytest.raises(RuntimeError,match='Refusing destructive WP-006 downgrade'):
        command.downgrade(cfg,'20261023_002')
    engine=create_engine(url)
    assert 'gramps_change_plans' in inspect(engine).get_table_names()
    with Session(engine) as s:
        assert s.get(SourceDocument,did).reference=='T1'
    engine.dispose()
