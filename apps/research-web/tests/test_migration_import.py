import csv
from pathlib import Path
from os import environ
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,inspect,select,func
from sqlalchemy.orm import Session
from app.research.db import close_engine
from app.research.importer import import_csv
from app.research.models import SourceDocument,Observation

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT.parents[1]/'fixtures'/'english_parish_demo.csv'


def test_initial_alembic_upgrade_idempotent_import_and_downgrade(tmp_path,monkeypatch):
    path=tmp_path/'research.sqlite3'
    monkeypatch.setenv('GEN_DB_URL','sqlite:///'+str(path))
    close_engine()
    config=Config(str(ROOT/'alembic.ini'))
    config.set_main_option('script_location',str(ROOT/'migrations'))
    command.upgrade(config,'head')
    eng=create_engine('sqlite:///'+str(path))
    assert 'source_documents' in inspect(eng).get_table_names()
    assert 'hypothesis_options' in inspect(eng).get_table_names()
    assert 'audit_events' in inspect(eng).get_table_names()
    assert import_csv(str(FIXTURE),dry_run=True)['rows']==3
    first=import_csv(str(FIXTURE),dry_run=False)
    assert first['documents_created']==3 and first['observations_created']==3
    second=import_csv(str(FIXTURE),dry_run=False)
    assert second['duplicates']==3 and second['documents_created']==0
    with Session(eng) as db:
        assert db.scalar(select(func.count()).select_from(Observation))==3
    with FIXTURE.open(newline='',encoding='utf-8') as source_file:
        reader=csv.DictReader(source_file)
        rows=list(reader)
        fields=reader.fieldnames
    for field,replacement in [('source_title','Changed source title'),
                              ('transcription_verbatim','Changed original reading')]:
        altered=[dict(row) for row in rows]
        altered[0][field]=replacement
        conflict_path=tmp_path/f'conflict-{field}.csv'
        with conflict_path.open('w',newline='',encoding='utf-8') as target_file:
            writer=csv.DictWriter(target_file,fieldnames=fields)
            writer.writeheader()
            writer.writerows(altered)
        outcome=import_csv(str(conflict_path),dry_run=False)
        assert len(outcome['errors'])==1 and outcome['errors'][0]['row']==2
        assert outcome['duplicates']==2
    with Session(eng) as db:
        assert db.scalar(select(SourceDocument.title).where(SourceDocument.provider_record_id=='DEMO-001'))=='Demonstration parish register'
        assert db.scalar(select(Observation.transcription_verbatim).where(Observation.observation_key=='entry-1'))=='John Carter baptised'
    eng.dispose();close_engine()
    # Protect against accidental destruction in real installations.
    import pytest
    with pytest.raises(RuntimeError,match='Destructive downgrade blocked'):
        command.downgrade(config,'base')
    monkeypatch.setenv('GEN_ALLOW_DESTRUCTIVE_DOWNGRADE','ISOLATED_TEST_ONLY')
    command.downgrade(config,'base')
    assert 'source_documents' not in inspect(create_engine('sqlite:///'+str(path))).get_table_names()
    close_engine()
