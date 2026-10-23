"""WP-014 evidence dossiers and side-by-side comparisons.

No source images are fetched, stored or transmitted. The associated browser has an
optional *client-side only* local-image preview. Raw historical readings and
subsequent corrections remain separately identifiable.
"""
from collections import defaultdict
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.research.models import SourceDocument, Observation, TranscriptionRevision
from app.research.source_families_api import classification

MAX_COMPARE = 6
MAX_REVISIONS = 30
MAX_TRANSCRIPTION_CHARS = 8000


def _text(value, maximum=MAX_TRANSCRIPTION_CHARS):
    value = value or ''
    return value[:maximum]


def dossiers(db: Session, observation_ids: list[UUID]) -> list[dict]:
    if not observation_ids or len(observation_ids) > MAX_COMPARE or len(set(observation_ids)) != len(observation_ids):
        raise HTTPException(422, f'Select between 1 and {MAX_COMPARE} distinct observations')
    records = {o.id:o for o in db.scalars(select(Observation).where(Observation.id.in_(observation_ids)))}
    if len(records) != len(observation_ids):
        raise HTTPException(404, 'One or more historical observations were not found')
    documents = {d.id:d for d in db.scalars(select(SourceDocument).where(
        SourceDocument.id.in_({o.document_id for o in records.values()})))}
    # Account for both manually attested copies and declared-source warnings.
    # This classification is deliberately advisory and never proves independence.
    output=[]
    for ident in observation_ids:
        o=records[ident]; doc=documents[o.document_id]
        revisions=db.scalars(select(TranscriptionRevision).where(
            TranscriptionRevision.observation_id==ident).order_by(
            TranscriptionRevision.created_at.asc(), TranscriptionRevision.id.asc()).limit(MAX_REVISIONS+1)).all()
        truncated=len(revisions)>MAX_REVISIONS
        revisions=revisions[:MAX_REVISIONS]
        # A capped history must not pretend its final displayed entry is the
        # newest reading. Obtain the actual latest revision independently.
        latest=db.scalar(select(TranscriptionRevision).where(
            TranscriptionRevision.observation_id==ident).order_by(
            TranscriptionRevision.created_at.desc(),TranscriptionRevision.id.desc()).limit(1))
        output.append({
            'observation_id':str(o.id),
            'observation_key':o.observation_key,
            'record':{'name_verbatim':o.person_name_verbatim,'event_type':o.event_type,
                      'event_date_verbatim':o.event_date_verbatim,
                      'earliest_iso':o.earliest_iso,'latest_iso':o.latest_iso,
                      'place_verbatim':o.location_verbatim,
                      'occupation_verbatim':o.occupation_verbatim,
                      'initial_transcription':_text(o.transcription_verbatim)},
            'citation':{'document_id':str(doc.id),'title':doc.title,'reference':doc.reference,
                        'provider':doc.provider,'provider_record_id':doc.provider_record_id,
                        'rights_note':doc.rights_note,'licence':doc.licence,
                        'access_method':doc.access_method,'origin_group':doc.origin_group,
                        'original_url':doc.original_url},
            'revision_history':[{'id':str(r.id),'text':_text(r.text),'editor':r.editor,
                                 'reason':r.reason,'created_at':r.created_at.isoformat(),
                                 'model_id':r.model_id} for r in revisions],
            'revision_history_truncated':truncated,
            'latest_reading':_text(latest.text if latest else o.transcription_verbatim),
            'original_source_independence_verified':False,
            'accepted_tree_write':False,
        })
    return output


def compare_dossiers(db: Session, observation_ids: list[UUID]) -> dict:
    results=dossiers(db,observation_ids)
    doc_ids={UUID(r['citation']['document_id']) for r in results}
    documents=db.scalars(select(SourceDocument).where(SourceDocument.id.in_(doc_ids))).all()
    source_groups=classification(db,documents)
    conflicts=[]
    grouped=defaultdict(list)
    for result in results:
        r=result['record']
        for key in ('name_verbatim','event_date_verbatim','place_verbatim','event_type'):
            if r[key]: grouped[key].append(str(r[key]).casefold().strip())
    for key in ('name_verbatim','event_date_verbatim','place_verbatim','event_type'):
        values=grouped[key]
        if len(set(values))>1:
            conflicts.append({'field':key,'kind':'different_literal_readings',
                              'explanation':'The source wording differs. This does not establish identity or contradiction.'})
    # Structural duplicates are possible even if citations differ: never report
    # independent corroboration from a count of source-document identifiers.
    possible_duplicate_docs=len({r['citation']['document_id'] for r in results}) < len(results)
    return {'observations':results,'literal_differences':conflicts,
            'same_document_reused':possible_duplicate_docs,
            'source_dependence_groups':source_groups,'source_independence_verified':False,
            'calibrated_probability':None,'accepted_tree_mutation_enabled':False,
            'warning':'Differences are literal observations, not identity proof. Copies of a common original are dependent.'}
