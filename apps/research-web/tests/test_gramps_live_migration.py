"""WP-007 migration must preserve WP-006 plans and refuse destruction of audit."""
from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.research.models import (GrampsChangePlan, GrampsReadValidation,
    HypothesisSet, HypothesisOption, BranchRevision, SourceDocument)

ROOT=Path(__file__).resolve().parents[1]


def makeconfig(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c


def test_003_to_004_retains_plans_and_approved_audit(monkeypatch,tmp_path):
    uri='sqlite+pysqlite:///'+str(tmp_path/'gramps-live.sqlite')
    monkeypatch.setenv('GEN_DB_URL',uri)
    cfg=makeconfig(uri)
    command.upgrade(cfg,'20261023_003')
    eng=create_engine(uri)
    with Session(eng) as s:
        doc=SourceDocument(provider='fixture',provider_record_id='1',title='Synthetic record',
          reference='FAKE',access_method='user_import',licence='test',
          origin_group='single',acquisition_operator='tester')
        group=HypothesisSet(title='Synthetic',subject_description='Test graph',relation_type='biological_parent',created_by='tester')
        s.add_all([doc,group]);s.flush()
        option=HypothesisOption(hypothesis_set_id=group.id,option_key='candidate',description='Potential match')
        s.add(option);s.flush()
        revision=BranchRevision(hypothesis_set_id=group.id,option_id=option.id,
            revision_number=1,rationale='Synthetic original evidence',created_by='tester')
        s.add(revision);s.flush()
        plan=GrampsChangePlan(idempotency_key='migration-wp007-001',
          hypothesis_set_id=group.id,option_id=option.id,branch_revision_id=revision.id,
          set_version_after_creation=2,digest_sha256='a'*64,
          preview_json={'digest_sha256':'a'*64,'accepted_tree_write':False},
          operator_note='Synthetic historic family proposal',created_by='tester')
        s.add(plan);s.commit()
        did=doc.id;pid=plan.id
    command.upgrade(cfg,'head')
    assert 'gramps_read_validations' in inspect(eng).get_table_names()
    with Session(eng) as s:
        assert s.get(GrampsChangePlan,pid) is not None
        assert s.get(SourceDocument,did).title=='Synthetic record'
        obj=GrampsReadValidation(plan_id=pid,plan_digest='a'*64,checked_by='tester',
             result_json={'status':'READ_ONLY_OBSERVATION_COMPLETE','mutation_performed':False})
        s.add(obj);s.commit()
    eng.dispose()
    with pytest.raises(RuntimeError,match='Refusing destructive WP-007 downgrade'):
        command.downgrade(cfg,'20261023_003')
    eng=create_engine(uri)
    with Session(eng) as s:
        assert s.get(GrampsChangePlan,pid) is not None
        assert s.get(SourceDocument,did).reference=='FAKE'
    eng.dispose()
