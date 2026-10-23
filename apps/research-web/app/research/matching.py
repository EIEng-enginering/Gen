"""Conservative explainable candidate ranker, NOT a calibrated probability.

This deliberately returns an uncalibrated ranking score. It never proposes a
match as accepted and never writes to Gramps. Human-reviewed benchmarks are
required before converting scores into estimated probabilities.
"""
import re
from datetime import date
from difflib import SequenceMatcher
from unicodedata import normalize


def standardise(value):
    value=normalize('NFKD',value or '').casefold()
    value=''.join(c for c in value if not c.isdecimal() and (c.isascii() or not c.isalpha()))
    return ' '.join(re.findall(r'[a-z]+',value))


def compare(left,right,origin_a=None,origin_b=None):
    """Rank candidates for review. Different origin groups do not prove independence."""
    name_a=standardise(left.person_name_verbatim)
    name_b=standardise(right.person_name_verbatim)
    name_similarity=SequenceMatcher(None,name_a,name_b).ratio() if name_a and name_b else 0.
    family_a=standardise(left.surname_verbatim)
    family_b=standardise(right.surname_verbatim)
    family_similarity=SequenceMatcher(None,family_a,family_b).ratio() if family_a and family_b else None
    place_a=standardise(left.location_verbatim)
    place_b=standardise(right.location_verbatim)
    location_similarity=SequenceMatcher(None,place_a,place_b).ratio() if place_a and place_b else None
    year_a=int(str(left.earliest_iso)[:4]) if left.earliest_iso else None
    year_b=int(str(right.earliest_iso)[:4]) if right.earliest_iso else None
    # Events of differing types can legitimately be decades apart. No naive
    # birth/baptism or burial/death equivalence is asserted.
    same_type=left.event_type==right.event_type
    year_delta=abs(year_a-year_b) if year_a is not None and year_b is not None else None
    same_origin=bool(origin_a and origin_b and origin_a==origin_b)
    features={'name_similarity':round(name_similarity,4),'surname_similarity':round(family_similarity,4) if family_similarity is not None else None,
              'location_similarity':round(location_similarity,4) if location_similarity is not None else None,
              'year_difference':year_delta,'same_event_type':same_type,
              'shared_original_source':same_origin}
    # Heuristic retrieval/ranking only; never present as family probability.
    score=0.68*name_similarity
    score+=0.15*(family_similarity if family_similarity is not None else 0.5)
    score+=0.12*(location_similarity if location_similarity is not None else 0.5)
    score+=0.05*(1.0 if same_type else 0.0)
    if year_delta is not None and same_type:
        score-=min(0.25,max(0.,year_delta-1)*0.025)
    # Same original source may be a duplicate transcription; not independent proof.
    if same_origin:
        score-=0.07
    score=max(0.,min(1.,round(score,4)))
    explanations=[]
    if name_similarity < .6:
        explanations.append('Names are materially different')
    if same_origin:
        explanations.append('Both records may derive from one original source: do not double-count')
    if year_delta is not None and same_type and year_delta>=10:
        explanations.append('Substantial event-year discrepancy')
    if not same_type:
        explanations.append('Different event types: age/chronology require expert assessment')
    if not explanations:
        explanations.append('Possible match for manual review; no calibrated probability available')
    return score,features,'; '.join(explanations)
