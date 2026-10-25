"""Deterministic *retrieval* features, never genealogical posterior probabilities.

No calls to historical websites, no accepted-tree mutation. Input record text is
untrusted; callers must render with textContent or HTML escaping.
"""
from __future__ import annotations
import re
import unicodedata
from difflib import SequenceMatcher

COUNTIES = ('bedfordshire','berkshire','buckinghamshire','cambridgeshire','cheshire',
 'cornwall','cumberland','derbyshire','devon','dorset','durham','essex','gloucestershire',
 'hampshire','herefordshire','hertfordshire','huntingdonshire','kent','lancashire',
 'leicestershire','lincolnshire','middlesex','norfolk','northamptonshire','northumberland',
 'nottinghamshire','oxfordshire','rutland','shropshire','somerset','staffordshire',
 'suffolk','surrey','sussex','warwickshire','westmorland','wiltshire','worcestershire',
 'yorkshire','anglesey','brecknockshire','caernarfonshire','cardiganshire','carmarthenshire',
 'denbighshire','flintshire','glamorgan','merionethshire','monmouthshire','montgomeryshire',
 'pembrokeshire','radnorshire')


def norm(s: str | None) -> str:
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+',s.casefold()))[:250]


def phonetic(s: str | None) -> str:
    """Simple Soundex retrieval fallback. Not a phonetic identity proof."""
    text=re.sub(r'[^a-z]','',norm(s))
    if not text:return ''
    groups=dict(zip('bfpvcgjkqsxzdtlmnr', '111122222222334556'))
    out=[text[0].upper()];prev=groups.get(text[0],'')
    for letter in text[1:]:
        code=groups.get(letter,'')
        if code and code!=prev:out.append(code)
        prev=code
    return (''.join(out)+'000')[:4]


def surname_variants(name: str) -> set[str]:
    """User-supplied alternative spellings; no invented genealogy aliases."""
    return {norm(part) for part in name.split('|') if norm(part)}


def county(place: str) -> str:
    p=norm(place)
    matches=[x for x in COUNTIES if re.search(r'(?<!\w)'+re.escape(x)+r'(?!\w)',p)]
    if matches:return max(matches,key=len)
    # Historical locality may lack county; do not silently claim one.
    return ''


def year_from_date(text: str | None) -> int | None:
    m=re.search(r'(?<!\d)(1[5-9]\d{2}|20[0-2]\d)(?!\d)',text or '')
    return int(m.group(1)) if m else None


def similarity(a: str,b: str) -> float:
    if not a or not b:return 0.
    return SequenceMatcher(None,a,b,autojunk=False).ratio()


def compare(a: dict,b: dict) -> dict:
    """Explainable heuristic comparison, with abstention/unknown. No posterior."""
    surname=similarity(norm(a.get('surname')),norm(b.get('surname')))
    given=similarity(norm(a.get('given')),norm(b.get('given')))
    place=similarity(norm(a.get('place')),norm(b.get('place')))
    y1,y2=a.get('year'),b.get('year')
    gap=abs(y1-y2) if y1 is not None and y2 is not None else None
    same_origin=bool(a.get('document_id') and a.get('document_id')==b.get('document_id')) or (
      bool(a.get('origin')) and a.get('origin')==b.get('origin'))
    reasons=[];conflicts=[]
    if surname>=.8:reasons.append('Surname text is similar')
    else:conflicts.append('Surname spelling differs')
    if given>=.75:reasons.append('Given name text is similar')
    if place>=.65:reasons.append('Recorded places are similar')
    if gap is not None and gap>100:conflicts.append('Events more than 100 years apart; review chronology')
    if same_origin:conflicts.append('Same possible original source: duplicate evidence, not independent corroboration')
    if a.get('event_type')=='birth' and b.get('event_type')=='birth' and gap is not None and gap>5:
        conflicts.append('Conflicting proposed birth dates')
    score=round(max(0.,min(1.,.52*surname+.28*given+.13*place+(.07 if gap is not None and gap<=80 else 0) - (.3 if gap is not None and gap>100 else 0))),4)
    return {'ranking_score':score,'score_type':'uncalibrated_heuristic_not_probability',
       'features':{'surname_text':round(surname,3),'given_text':round(given,3),'place_text':round(place,3),'year_gap':gap},
       'supports':reasons,'conflicts':conflicts,'same_possible_original':same_origin,
       'unknown_option':True,'calibrated_probability':None,'identity_approved':False,
       'warning':'Similar names or household co-residence do not establish identity, marriage or biological parentage.'}
