"""Incremental 001 -> 002 upgrade never mutates the old evidence rows."""
import os
from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import Session
from app.research.models import SourceDocument, Observation, HypothesisSet, HypothesisOption, BranchRevision

ROOT=Path(__file__).resolve().parents[1]


def config(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c


def test_old_records_survive_upgrade_and_populated_downgrade_blocks(monkeypatch,tmp_path):
    db=tmp_path/'genealogy.db';url='sqlite+pysqlite:///'+str(db)
    monkeypatch.setenv('GEN_DB_URL',url)
    cfg=config(url)
    command.upgrade(cfg,'20261023_001')
    eng=create_engine(url)
    with Session(eng) as s:
        doc=SourceDocument(provider='synthetic',provider_record_id='old-1',title='Old record',
            reference='Earlier evidence',access_method='user_import',licence='test',
            acquisition_operator='tester',origin_group='example-register')
        s.add(doc);s.flush()
        record=Observation(document_id=doc.id,observation_key='row-1',event_type='baptism',
            person_name_verbatim='Jane Hart')
        s.add(record);s.commit()
        original_id=doc.id
    command.upgrade(cfg,'head')
    with Session(eng) as s:
        assert s.get(SourceDocument,original_id).title=='Old record'
        assert s.scalar(select(Observation.person_name_verbatim))=='Jane Hart'
        assert 'hypothesis_branch_revisions' in inspect(eng).get_table_names()
        group=HypothesisSet(title='Parents of Jane',subject_description='Father?',
             relation_type='biological_parent',created_by='tester')
        s.add(group);s.flush()
        option=HypothesisOption(hypothesis_set_id=group.id,option_key='unknown',
             description='Unidentified',is_unknown=1)
        s.add(option);s.flush()
        s.add(BranchRevision(hypothesis_set_id=group.id,option_id=option.id,
             revision_number=1,rationale='No source can establish parent',created_by='tester'))
        s.commit()
    eng.dispose()
    # Even an acknowledged earlier destructive-test flag cannot drop branch history.
    monkeypatch.setenv('GEN_ALLOW_DESTRUCTIVE_DOWNGRADE','ISOLATED_TEST_ONLY')
    with pytest.raises(RuntimeError,match='Refusing destructive WP-005 downgrade'):
        command.downgrade(cfg,'20261023_001')
    eng2=create_engine(url)
    assert 'hypothesis_branch_revisions' in inspect(eng2).get_table_names()
    eng2.dispose()
