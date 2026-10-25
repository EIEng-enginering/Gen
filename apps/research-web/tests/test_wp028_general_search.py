"""Synthetic-only tests for general surname search and unscored correlation."""
import pytest
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from uuid import uuid4
from app.research.models import Base,SourceDocument,Observation
from app.research.acquisition_models import AcquisitionBatch,StagedEvidence
from app.research.general_search_models import SearchMention
from app.research.general_search_core import norm,phonetic,county,compare
from app.research.general_search_service import sync_page,search,correlate

@pytest.fixture
def db():
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:yield session
    engine.dispose()

def synthetic_doc(db,first,sur,place,year,origin='original-A',provider='fictional'):
    d=SourceDocument(provider=provider,provider_record_id=str(uuid4()),title='Fictional census transcription',
       reference='SYNTH/001',access_method='user_import',licence='synthetic test fixture',
       origin_group=origin,acquisition_operator='test')
    db.add(d);db.flush()
    o=Observation(document_id=d.id,observation_key='1',event_type='census',person_name_verbatim=f'{first} {sur}',
       surname_verbatim=sur,given_names_verbatim=first,location_verbatim=place,event_date_verbatim=str(year),
       earliest_iso=f'{year}-01-01')
    db.add(o);db.commit();return o

def test_variants_and_place():
    assert norm('SMÝTH')=='smyth'
    assert phonetic('Smith')==phonetic('Smyth')
    assert county('Nantwich, Cheshire, England')=='cheshire'
    assert county('Somewhere unknown')==''

def test_reviewed_and_staged_are_separate(db):
    o=synthetic_doc(db,'Ada','Smyth','Congleton, Cheshire',1871)
    b=AcquisitionBatch(batch_key='fixture-a',input_kind='ai_jsonl',created_by='test',rights_attested=1,row_count=1)
    db.add(b);db.flush()
    s=StagedEvidence(batch_id=b.id,row_number=1,sha256='b'*64,
      payload={'person_name_verbatim':'Ada Smith','surname_verbatim':'Smith',
       'given_names_verbatim':'Ada','location_verbatim':'Nantwich, Cheshire','record_type':'census',
       'source_reference':'SYNTH/002','provider':'fictional'},surname_key='smith',place_key='nantwich',year_hint=1881,status='awaiting_human_review')
    db.add(s);db.commit()
    assert sync_page(db,'observed')['created']==1
    assert sync_page(db,'staged')['created']==1
    assert sync_page(db,'observed')['created']==0
    reviewed=search(db,surname='Smyth',county_filter='Cheshire',include_staged=False)
    assert len(reviewed['results'])==1
    phonetic_results=search(db,surname='Smyth',mode='phonetic')
    assert len(phonetic_results['results'])==2
    assert any(x['status']=='awaiting_human_review' for x in phonetic_results['results'])
    assert all(x['probability'] is None for x in phonetic_results['results'])
    assert phonetic_results['external_provider_requests']==0
    subject=db.scalar(select(SearchMention).where(SearchMention.source_kind=='observed'))
    matches=correlate(db,subject)
    assert matches['unknown_candidate'] is True
    assert matches['calibrated_probability'] is None
    assert len(matches['candidates'])==1

def test_manual_source_copy_not_independent(db):
    a=synthetic_doc(db,'Jane','Hale','Chester, Cheshire',1861,'shared-orig')
    b=synthetic_doc(db,'Jane','Hale','Chester, Cheshire',1861,'shared-orig',provider='fictional_other')
    sync_page(db,'observed')
    x=db.scalar(select(SearchMention).where(SearchMention.source_id==str(a.id)))
    c=correlate(db,x)
    assert c['candidates'][0]['comparison']['same_possible_original'] is True
    assert c['candidates'][0]['comparison']['identity_approved'] is False

def test_no_parentage_claim():
    out=compare({'surname':'Jones','given':'Mary','year':1871,'place':'Chester'},
                {'surname':'Jones','given':'Mary','year':1881,'place':'Chester'})
    assert 'parent' in out['warning']
    assert out['unknown_option'] and out['calibrated_probability'] is None

def test_cursor_and_other_region(db):
    for n in range(9):synthetic_doc(db,'Daniel','Rhys','Cardiff, Glamorgan',1861+n,'origin'+str(n))
    sync_page(db,'observed')
    a=search(db,surname='Rhys',county_filter='Glamorgan',limit=4)
    assert len(a['results'])==4 and a['next_cursor']
    b=search(db,surname='Rhys',county_filter='Glamorgan',limit=10,after=a['next_cursor'])
    assert len(b['results'])==5
    assert not {v['id'] for v in a['results']}&{v['id'] for v in b['results']}
    assert search(db,surname='Rhys',county_filter='Cheshire')['results']==[]

def test_invalid_broad_search(db):
    with pytest.raises(ValueError):search(db)
    with pytest.raises(ValueError):search(db,surname='a')
    with pytest.raises(ValueError):search(db,surname='Jones',year_from=1900,year_to=1800)
