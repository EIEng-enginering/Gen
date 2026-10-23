"""WP-009 migration preservation and fail-closed downgrade with evidence."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from app.research.models import SourceDocument, HistoricalPlace
import pytest

ROOT=Path(__file__).resolve().parents[1]


def conf(uri):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',uri)
    return c


def test_004_to_005_retains_provenance_and_refuses_destructive_rollback(monkeypatch,tmp_path):
    uri='sqlite+pysqlite:///'+str(tmp_path/'wp009.sqlite')
    monkeypatch.setenv('GEN_DB_URL',uri)
    c=conf(uri)
    command.upgrade(c,'20261023_004')
    eng=create_engine(uri)
    with Session(eng) as db:
        src=SourceDocument(provider='test',provider_record_id='original',title='Original page',
         reference='Synthetic test archive',access_method='user_import',licence='test_only',
         origin_group='original/test',acquisition_operator='tester')
        db.add(src);db.commit();id=src.id
    command.upgrade(c,'20261023_005')
    assert 'historical_places' in inspect(eng).get_table_names()
    with Session(eng) as db:
        assert db.get(SourceDocument,id).reference=='Synthetic test archive'
        place=HistoricalPlace(source_document_id=id,place_key='place-1',label='Synthetic old parish',
           county_label='Demo',jurisdiction_type='parish',valid_from_year=1710,valid_to_year=1901,
           aliases_json=['Old Parish'],evidence_note='Synthetic place evidence',created_by='tester')
        db.add(place);db.commit();pid=place.id
    with pytest.raises(RuntimeError,match='Refusing destructive WP-009 downgrade'):
        command.downgrade(c,'20261023_004')
    with Session(eng) as db:
        assert db.get(SourceDocument,id) is not None
        assert db.get(HistoricalPlace,pid) is not None
    eng.dispose()
