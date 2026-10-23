"""Lawful, user-supplied CSV ingestion. No crawling or remote network access.

Each row is one person appearance linked to a cited source document. Repeated
imports are idempotent by provider ID and observation key. Failures are captured
by row; no source text is discarded or silently normalised.
"""
import argparse
import csv
import json
from pathlib import Path
from contextlib import nullcontext
from sqlalchemy import select
from app.research.db import engine
from app.research.models import (SourceDocument, Observation, TranscriptionRevision, AuditEvent)
from app.research.schemas import DocumentIn, ObservationIn
from sqlalchemy.orm import Session

REQUIRED={'provider','provider_record_id','source_title','reference','origin_group','licence',
          'observation_key','event_type','person_name_verbatim'}


def import_csv(path:str,operator='local_import',dry_run=True,max_rows=100000):
    result={'file':Path(path).name,'dry_run':dry_run,'rows':0,'documents_created':0,
            'observations_created':0,'duplicates':0,'errors':[]}
    with open(path,'r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        missing=REQUIRED-set(reader.fieldnames or [])
        if missing:
            raise ValueError('Missing required CSV fields: '+', '.join(sorted(missing)))
        with (nullcontext(None) if dry_run else Session(engine())) as db:
            for rowno,row in enumerate(reader,start=2):
                if result['rows']>=max_rows:
                    result['errors'].append({'row':rowno,'error':'Max row limit exceeded'})
                    break
                result['rows']+=1
                try:
                    d=DocumentIn(provider=row['provider'],provider_record_id=row['provider_record_id'],
                        title=row['source_title'],reference=row['reference'],origin_group=row['origin_group'],
                        licence=row['licence'],access_method=row.get('access_method') or 'user_import',
                        original_url=row.get('original_url') or None)
                    o=ObservationIn(observation_key=row['observation_key'],event_type=row['event_type'],
                        person_name_verbatim=row['person_name_verbatim'],surname_verbatim=row.get('surname_verbatim') or '',
                        given_names_verbatim=row.get('given_names_verbatim') or '',
                        event_date_verbatim=row.get('event_date_verbatim') or '',
                        earliest_iso=row.get('earliest_iso') or None,latest_iso=row.get('latest_iso') or None,
                        location_verbatim=row.get('location_verbatim') or '',
                        occupation_verbatim=row.get('occupation_verbatim') or '',
                        transcription_verbatim=row.get('transcription_verbatim') or '')
                    if dry_run:
                        continue
                    document_values=d.model_dump()
                    observation_values=o.model_dump(mode='json')
                    new_document=False
                    new_observation=False
                    duplicate=False
                    with db.begin_nested():
                        old=db.scalar(select(SourceDocument).where(SourceDocument.provider==d.provider,
                                              SourceDocument.provider_record_id==d.provider_record_id))
                        if old is None:
                            old=SourceDocument(**document_values,acquisition_operator=operator)
                            db.add(old);db.flush()
                            new_document=True
                        elif any(getattr(old,key)!=value for key,value in document_values.items()):
                            raise ValueError('Provider record ID conflicts with existing source provenance')
                        existing=db.scalar(select(Observation).where(Observation.document_id==old.id,
                                                 Observation.observation_key==o.observation_key))
                        if existing:
                            if any(getattr(existing,key)!=value for key,value in observation_values.items()):
                                raise ValueError('Previously imported observation has conflicting content')
                            duplicate=True
                        else:
                            obj=Observation(document_id=old.id,**observation_values)
                            db.add(obj);db.flush()
                            if o.transcription_verbatim:
                                db.add(TranscriptionRevision(observation_id=obj.id,text=o.transcription_verbatim,
                                        editor=operator,reason='Initial CSV import'))
                            db.add(AuditEvent(actor=operator,action='csv_observation_imported',
                                              target_type='observation',target_id=str(obj.id),
                                              details_json={'source_provider':d.provider}))
                            new_observation=True
                    db.commit()
                    result['documents_created']+=int(new_document)
                    result['observations_created']+=int(new_observation)
                    result['duplicates']+=int(duplicate)
                except Exception as exc:
                    db.rollback()
                    # Counts count committed operations only; if nested transaction
                    # failed, reset counts conservatively in failed row.
                    result['errors'].append({'row':rowno,'error':str(exc)[:500]})
    return result


def main():
    parser=argparse.ArgumentParser(description='24 Gen user-authorised CSV import')
    parser.add_argument('csv_file')
    parser.add_argument('--apply',action='store_true',help='Write to research DB (default: dry-run validation)')
    parser.add_argument('--operator',default='local_csv_import')
    args=parser.parse_args()
    outcome=import_csv(args.csv_file,operator=args.operator,dry_run=not args.apply)
    print(json.dumps(outcome,indent=2))
    if outcome['errors']:
        raise SystemExit(1)

if __name__=='__main__': main()
