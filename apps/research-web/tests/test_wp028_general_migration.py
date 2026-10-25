"""SQL migration from documented WP026/027 version 009, with loss protection."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,inspect,text
from sqlalchemy.orm import Session
import pytest
from app.research.models import SourceDocument
ROOT=Path(__file__).resolve().parents[1]

def config(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c

def test_upgrade_preserves_old_and_rejects_loss(tmp_path,monkeypatch):
    url='sqlite+pysqlite:///'+str(tmp_path/'test_migration.sqlite')
    monkeypatch.setenv('GEN_DB_URL',url)
    c=config(url)
    command.upgrade(c,'20261025_009')
    engine=create_engine(url)
    with Session(engine) as s:
        doc=SourceDocument(provider='synthetic',provider_record_id='G1',title='Fictional source',
          reference='FAKE-1',origin_group='fict/1',access_method='user_import',licence='synthetic',
          acquisition_operator='test')
        s.add(doc);s.commit();old_id=doc.id
    command.upgrade(c,'20261025_010')
    assert 'general_search_mentions' in inspect(engine).get_table_names()
    assert 'ix_general_search_surname_year' in {v['name'] for v in inspect(engine).get_indexes('general_search_mentions')}
    with Session(engine) as s:assert s.get(SourceDocument,old_id).reference=='FAKE-1'
    with engine.begin() as con:
        from uuid import uuid4
        con.execute(text('INSERT INTO general_search_mentions (id,source_kind,source_id,name_literal,surname_literal,surname_key,surname_soundex,given_literal,given_key,place_literal,place_key,county_key,event_type,provider,source_reference,source_document_id,possible_original,rights_label,status) VALUES (:id,\'staged\',\'fiction-1\',\'Fake Name\',\'Name\',\'name\',\'N500\',\'Fake\',\'fake\',\'Bristol\',\'bristol\',\'gloucestershire\',\'baptism\',\'synthetic\',\'FAKE/1\',\'\',\'\',\'synthetic\',\'awaiting_human_review\')'),{'id':str(uuid4())})
    with pytest.raises(RuntimeError,match='Refusing populated search-index downgrade'):
        command.downgrade(c,'20261025_009')
    with engine.connect() as con:
        assert con.scalar(text('SELECT COUNT(*) FROM general_search_mentions'))==1
    engine.dispose()
