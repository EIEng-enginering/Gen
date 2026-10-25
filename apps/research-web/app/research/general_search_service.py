"""Bounded projection and indexed general search over observed and staged evidence.

The materialized index is derivative and rebuildable. No provider fetches or Gramps
writes occur. Pagination uses stable UUID keys; rerun from the beginning to include
new randomly assigned UUIDs less than an earlier cursor.
"""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select,or_,func,and_
from sqlalchemy.orm import Session
from .models import Observation,SourceDocument,OriginalSourceMember,OriginalSourceFamily
from .acquisition_models import StagedEvidence
from .general_search_models import SearchMention
from .general_search_core import norm,phonetic,county,year_from_date,surname_variants,compare


def project_observation(db:Session,row:Observation)->dict:
    doc=db.get(SourceDocument,row.document_id)
    membership=db.scalar(select(OriginalSourceMember).where(OriginalSourceMember.document_id==row.document_id))
    possible_original=('attested:'+str(membership.family_id)) if membership else (
        'reported:'+doc.origin_group.strip().casefold() if doc and doc.origin_group.strip() else '')
    return dict(source_kind='observed',source_id=str(row.id),name_literal=row.person_name_verbatim,
        surname_literal=row.surname_verbatim,surname_key=norm(row.surname_verbatim),
        surname_soundex=phonetic(row.surname_verbatim),given_literal=row.given_names_verbatim,
        given_key=norm(row.given_names_verbatim),place_literal=row.location_verbatim,
        place_key=norm(row.location_verbatim),county_key=county(row.location_verbatim),
        event_type=row.event_type,year_hint=year_from_date(row.earliest_iso) or year_from_date(row.event_date_verbatim),
        year_end_hint=year_from_date(row.latest_iso),provider=doc.provider if doc else '',
        source_reference=doc.reference if doc else '',source_document_id=str(row.document_id),
        possible_original=possible_original,rights_label=doc.licence if doc else '',
        status=('human_source_check_attested' if doc and isinstance(doc.metadata_json,dict)
                and doc.metadata_json.get('operator_source_check_attested') else 'research_observation_unadjudicated'))


def project_staged(row:StagedEvidence)->dict:
    d=row.payload if isinstance(row.payload,dict) else {}
    sur=str(d.get('surname_verbatim') or '')
    place=str(d.get('location_verbatim') or '')
    return dict(source_kind='staged',source_id=str(row.id),name_literal=str(d.get('person_name_verbatim') or ''),
       surname_literal=sur,surname_key=norm(sur),surname_soundex=phonetic(sur),
       given_literal=str(d.get('given_names_verbatim') or ''),given_key=norm(d.get('given_names_verbatim')),
       place_literal=place,place_key=norm(place),county_key=county(place),
       event_type=str(d.get('record_type') or ''),year_hint=row.year_hint,
       year_end_hint=year_from_date(str(d.get('latest_iso') or '')),
       provider=str(d.get('provider') or ''),source_reference=str(d.get('source_reference') or ''),
       source_document_id=str(row.import_document_id or ''),
       possible_original=('reported:'+str(d.get('origin_group') or '').strip().casefold()) if d.get('origin_group') else '',
       rights_label=str(d.get('licence') or ''),status=str(row.status))


def sync_page(db:Session,kind:str,after:UUID|None=None,limit:int=200)->dict:
    if kind not in ('observed','staged'):raise ValueError('Unsupported source_kind')
    if limit < 1 or limit > 500:raise ValueError('Page size out of range')
    model=Observation if kind=='observed' else StagedEvidence
    q=select(model).order_by(model.id).limit(limit)
    if after:q=q.where(model.id>after)
    rows=db.scalars(q).all()
    created=0;updated=0
    for row in rows:
        fields=project_observation(db,row) if kind=='observed' else project_staged(row)
        obj=db.scalar(select(SearchMention).where(SearchMention.source_kind==kind,
                                                   SearchMention.source_id==str(row.id)))
        if obj is None:
            db.add(SearchMention(**fields));created+=1
        else:
            changed=False
            for key,val in fields.items():
                if getattr(obj,key)!=val:setattr(obj,key,val);changed=True
            updated+=bool(changed)
    db.commit()
    return {'kind':kind,'processed':len(rows),'created':created,'updated':updated,
      'next_after':str(rows[-1].id) if rows else None,
      'end_of_current_sweep':len(rows)<limit,
      'safe_to_resume':True,
      'note':'Resume within this sweep with next_after. Start a fresh sweep at null for any later imports; index is idempotent.'}


def as_result(row:SearchMention,match_type:str='indexed_filter')->dict:
    return {'id':str(row.id),'record_kind':row.source_kind,'source_id':row.source_id,
        'name_literal':row.name_literal,'surname_literal':row.surname_literal,
        'given_literal':row.given_literal,'event_type':row.event_type,
        'year':row.year_hint,'year_end':row.year_end_hint,'place_literal':row.place_literal,
        'county':row.county_key,'provider':row.provider,'source_reference':row.source_reference,
        'document_id':row.source_document_id,'possible_original_group':row.possible_original,
        'rights_label':row.rights_label,'status':row.status,'match_type':match_type,
        'source_checked':row.status=='human_source_check_attested', 'probability':None,'gramps_written':False}


def search(db:Session,*,surname:str='',given:str='',county_filter:str='',year_from:int|None=None,
           year_to:int|None=None,record_type:str='',provider:str='',include_staged:bool=True,
           mode:str='exact',limit:int=30,after:str|None=None)->dict:
    """Query indexed equality/phonetic key; never scan the whole DB for fuzzy names."""
    if limit<1 or limit>100:raise ValueError('Limit out of bounds')
    if year_from and year_to and year_from>year_to:raise ValueError('Invalid date range')
    if mode not in ('exact','phonetic','prefix'):raise ValueError('Invalid name mode')
    alternatives=surname_variants(surname)
    c=norm(county_filter)
    if not alternatives and len(c)<2:raise ValueError('Provide a surname or indexed historic county')
    if alternatives and (len(alternatives)>8 or min(map(len,alternatives))<2):raise ValueError('Surname filters too broad')
    filters=[]
    if alternatives:
        if mode=='exact':filters.append(SearchMention.surname_key.in_(sorted(alternatives)))
        elif mode=='phonetic':filters.append(SearchMention.surname_soundex.in_(sorted({phonetic(x) for x in alternatives})))
        else:
            filters.append(or_(*(and_(SearchMention.surname_key>=x,SearchMention.surname_key<x+'\uffff') for x in alternatives)))
    if c:filters.append(SearchMention.county_key==c)
    if year_from:filters.append(or_(SearchMention.year_hint==None,SearchMention.year_hint>=year_from-25))
    if year_to:filters.append(or_(SearchMention.year_hint==None,SearchMention.year_hint<=year_to+25))
    if record_type:filters.append(SearchMention.event_type==record_type)
    if provider:filters.append(SearchMention.provider==provider)
    if not include_staged:filters.append(SearchMention.source_kind=='observed')
    if after:
        try:filters.append(SearchMention.id>UUID(after))
        except ValueError:raise ValueError('Invalid cursor')
    q=select(SearchMention).where(*filters).order_by(SearchMention.id).limit(limit+1)
    rows=db.scalars(q).all(); has_more=len(rows)>limit; rows=rows[:limit]
    formatted=[]
    for r in rows:
        item=as_result(r,match_type=mode)
        if given:item['given_name_similarity']=round(__import__('difflib').SequenceMatcher(None,norm(given),r.given_key).ratio(),3)
        # Explicitly label unknown event date instead of manufacturing a date.
        if (year_from and r.year_hint and r.year_hint<year_from) or (year_to and r.year_hint and r.year_hint>year_to):
            item['date_outside_request_but_in_uncertainty_window']=True
        formatted.append(item)
    distinct=len({r.possible_original for r in rows if r.possible_original})
    return {'results':formatted,'next_cursor':str(rows[-1].id) if has_more and rows else None,
        'result_cap':limit,'page_has_more':has_more,'exhaustive':False,
        'scope':{'surname':surname,'county':county_filter,'year_from':year_from,'year_to':year_to,
                 'record_type':record_type,'provider':provider},
        'origin_labelled_groups_on_page':distinct,'origin_independence_verified':False,
        'calibrated_probability':None,'external_provider_requests':0,
        'coverage_note':'Only locally indexed records were searched. No absent provider or year/region is claimed covered.'}


def correlate(db:Session,subject:SearchMention,limit:int=20)->dict:
    """Bounded candidate pool, explicit unknown option and explainable ranking."""
    if not subject.surname_soundex:return {'candidates':[],'unknown_candidate':True,'probability':None}
    q=(select(SearchMention).where(SearchMention.id!=subject.id,
                                   SearchMention.surname_soundex==subject.surname_soundex)
                             .order_by(SearchMention.id).limit(250))
    pool=db.scalars(q).all()
    base={'surname':subject.surname_literal,'given':subject.given_literal,'place':subject.place_literal,
          'year':subject.year_hint,'origin':subject.possible_original,
          'document_id':subject.source_document_id,'event_type':subject.event_type}
    out=[]
    for cand in pool:
        features=compare(base,{'surname':cand.surname_literal,'given':cand.given_literal,
           'place':cand.place_literal,'year':cand.year_hint,'origin':cand.possible_original,
           'document_id':cand.source_document_id,'event_type':cand.event_type})
        out.append({'record':as_result(cand),'comparison':features})
    out.sort(key=lambda x:(-x['comparison']['ranking_score'],x['record']['id']))
    return {'subject':as_result(subject),'candidates':out[:limit],
       'unknown_candidate':True,'candidate_pool_cap':250,'pool_exhaustive':len(pool)<250,
       'calibrated_probability':None,'accepted_tree_mutation':False,
       'warning':'Candidate ranking only, not proof of same person or relationship. Unlisted/unknown persons remain possible.'}
