"""Test durable import migration and nine-volume archive validation with synthetic files."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,inspect,select
from sqlalchemy.orm import Session
from app.research.models import SourceDocument
from app.research.acquisition_models import AcquisitionBatch,StagedEvidence
import pytest
import io
import hashlib
import tarfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'tools'))
from verify_24gen_backup import verify,EXPECTED

def config(url):
    c=Config(str(ROOT/'alembic.ini'))
    c.set_main_option('script_location',str(ROOT/'migrations'))
    c.set_main_option('sqlalchemy.url',url)
    return c

def test_upgrade_previous_schema_and_refuse_downgrade(monkeypatch,tmp_path):
    url='sqlite+pysqlite:///'+str(tmp_path/'test.sqlite')
    monkeypatch.setenv('GEN_DB_URL',url)
    c=config(url)
    command.upgrade(c,'20261024_008')
    eng=create_engine(url)
    with Session(eng) as db:
        old=SourceDocument(provider='synthetic',provider_record_id='previous',title='Previous source',
           reference='previous archive',access_method='user_import',licence='test_only',origin_group='test/page',acquisition_operator='tester')
        db.add(old);db.commit();oid=old.id
    command.upgrade(c,'20261025_009')
    assert {'acquisition_batches','staged_evidence','staged_person_links'}<=set(inspect(eng).get_table_names())
    with Session(eng) as db:
        assert db.get(SourceDocument,oid).reference=='previous archive'
        b=AcquisitionBatch(batch_key='test-123456',input_kind='user_export',created_by='test',rights_attested=1,row_count=1)
        db.add(b);db.flush()
        db.add(StagedEvidence(batch_id=b.id,row_number=1,sha256='a'*64,payload={'synthetic':True},status='awaiting_human_review'))
        db.commit()
    with pytest.raises(RuntimeError,match='Refusing downgrade'):
        command.downgrade(c,'20261024_008')
    with Session(eng) as db:
        assert db.get(SourceDocument,oid).reference=='previous archive'
        assert db.scalar(select(AcquisitionBatch.batch_key))=='test-123456'
    eng.dispose()

def fake_archives(folder,include_media=False):
    folder.mkdir()
    sums=[]
    for key in EXPECTED:
        name='gen24_'+key+'.tgz'
        dest=folder/name
        with tarfile.open(dest,'w:gz') as tf:
            raw=(b'synthetic fixture - NOT ACTUAL HISTORY' if key=='gramps_media' and include_media else b'')
            if raw:
                info=tarfile.TarInfo('test_fixture.txt');info.size=len(raw)
                tf.addfile(info,io.BytesIO(raw))
        h=hashlib.sha256(dest.read_bytes()).hexdigest()
        sums.append(h+'  '+name)
    (folder/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='ascii')

def test_backup_integrity_nonempty_media_and_missing(tmp_path):
    d=tmp_path/'restricted'
    fake_archives(d,include_media=True)
    x=verify(d,True)
    assert x['archives']==9 and x['media_file_count']==1 and not x['restored']
    (d/'gen24_gramps_db.tgz').unlink()
    with pytest.raises(ValueError,match='exactly nine'):verify(d)

def test_backup_empty_media_is_not_acceptable(tmp_path):
    d=tmp_path/'restricted'
    fake_archives(d)
    assert verify(d)['media_restore_requirement_met'] is False
    with pytest.raises(ValueError,match='No nonempty media'):verify(d,True)

def test_backup_hash_tamper_and_traversal(tmp_path):
    d=tmp_path/'restricted'
    fake_archives(d,include_media=True)
    (d/'gen24_gramps_media.tgz').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash mismatch'):verify(d)
    fake_archives_v2=tmp_path/'restricted2';fake_archives(fake_archives_v2)
    name='gen24_gramps_media.tgz';dest=fake_archives_v2/name
    with tarfile.open(dest,'w:gz') as tf:
        v=b'bad';info=tarfile.TarInfo('../../escape');info.size=len(v);tf.addfile(info,io.BytesIO(v))
    lines=(fake_archives_v2/'SHA256SUMS.txt').read_text().splitlines()
    h=hashlib.sha256(dest.read_bytes()).hexdigest()
    (fake_archives_v2/'SHA256SUMS.txt').write_text('\n'.join((h+'  '+name if ln.endswith(name) else ln) for ln in lines)+'\n')
    with pytest.raises(ValueError,match='unsafe archive member'):verify(fake_archives_v2)

def test_immutable_restore_namespace_powershell():
    script=(ROOT.parents[1]/'deploy/windows/Invoke-24Gen-IsolatedRestore.ps1').read_text()
    assert 'gen24wp027' in script and 'if (-not $Execute)' in script
    assert '--network none' in script
    assert 'docker volume rm' not in script and 'docker compose down' not in script
