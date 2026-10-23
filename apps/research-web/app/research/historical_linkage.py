"""WP-009 historically aware, UNCALIBRATED identity-candidate triage.

Ranks evidence for review; NEVER infers an accepted identity/relationship. In
particular, a census observation's event year is not the person's birth year.
"""
from __future__ import annotations
from difflib import SequenceMatcher
from app.research.matching import standardise
from app.research.english_rules import census_age_interval

# Curated, deliberately small variants used ONLY as soft clues, not proven identities.
GIVEN_VARIANTS = {
    'william': {'will', 'wm', 'bill'}, 'elizabeth': {'eliz', 'elizth', 'betty', 'bess'},
    'john': {'jno', 'jack'}, 'margaret': {'margt', 'meg'},
    'thomas': {'thos', 'tom'}, 'james': {'jas', 'jim'},
    'richard': {'richd', 'dick'}, 'mary': {'maria', 'molly'},
}


def name_tokens(text):
    return standardise(text).split()


def given_similarity(a, b):
    aa, bb = name_tokens(a), name_tokens(b)
    if not aa or not bb: return None
    left, right = aa[0], bb[0]
    if left == right: return 1.0
    if right in GIVEN_VARIANTS.get(left, ()) or left in GIVEN_VARIANTS.get(right, ()):
        return 0.82
    return SequenceMatcher(None, left, right).ratio()


def _year(text):
    try:
        return int(str(text)[:4]) if text else None
    except ValueError:
        return None


def _age_birth_interval(item):
    """Only returns an estimate when the record explicitly contains an age."""
    extra = item.additional_json if isinstance(item.additional_json, dict) else {}
    event = (item.event_type or '').casefold()
    if event != 'census': return None
    year = _year(item.earliest_iso)
    age = extra.get('reported_age')
    if year is None or isinstance(age, bool) or not isinstance(age, int):return None
    if year < 1841 or (year - 1841) % 10 != 0: return None
    try:
        return census_age_interval(year, age)
    except ValueError:
        return None


def candidate_assessment(a, b, origin_a='', origin_b=''):
    """Deterministic ranking and transparent warning report; no posteriors."""
    surname_a, surname_b = standardise(a.surname_verbatim), standardise(b.surname_verbatim)
    given = given_similarity(a.given_names_verbatim, b.given_names_verbatim)
    surname = SequenceMatcher(None, surname_a, surname_b).ratio() if surname_a and surname_b else None
    location_a, location_b = standardise(a.location_verbatim), standardise(b.location_verbatim)
    place = SequenceMatcher(None, location_a, location_b).ratio() if location_a and location_b else None
    same_verified_place_ref = bool(a.historical_place_ref and b.historical_place_ref
                                   and a.historical_place_ref == b.historical_place_ref)
    same_origin = bool(origin_a and origin_b and origin_a == origin_b)
    warnings = []
    if same_origin:
        warnings.append('Shared original-source group; do not treat duplicate transcriptions as independent evidence')
    if surname is not None and surname < .5:
        warnings.append('Dissimilar surnames; marriage or transcription may explain the difference')
    year_a, year_b = _year(a.earliest_iso), _year(b.earliest_iso)
    years = abs(year_a - year_b) if year_a is not None and year_b is not None else None
    if a.event_type == b.event_type == 'census' and year_a == year_b and a.document_id != b.document_id:
        warnings.append('Multiple census appearances in one enumeration year: resolve household and duplicate source context')
    age_a, age_b = _age_birth_interval(a), _age_birth_interval(b)
    if age_a and age_b:
        overlap = (age_a['birth_year_min'] <= age_b['birth_year_max'] and
                   age_b['birth_year_min'] <= age_a['birth_year_max'])
        if not overlap:
            warnings.append('Reported census ages imply non-overlapping estimated birth-year intervals')
    elif a.event_type == 'census' or b.event_type == 'census':
        warnings.append('At least one census birth-year range is unavailable; event dates are NOT dates of birth')
    # Manual catalogue keys are advisory, never geographic proof.
    score = 0.0
    score += 0.45 * (surname if surname is not None else 0.35)
    score += 0.35 * (given if given is not None else 0.35)
    score += 0.12 * (place if place is not None else 0.35)
    score += 0.08 * (1.0 if same_verified_place_ref else 0.35)
    if same_origin: score -= 0.06
    if years is not None and a.event_type == b.event_type and a.event_type in ('baptism', 'birth', 'death', 'burial'):
        score -= min(0.2, years * .018)
    score = max(0, min(1, round(score, 4)))
    return {
        'ranking_score': score, 'calibrated_probability': None,
        'calibration_status':'NOT_CALIBRATED',
        'features': {
            'given_similarity': round(given, 3) if given is not None else None,
            'surname_similarity': round(surname, 3) if surname is not None else None,
            'place_text_similarity': round(place, 3) if place is not None else None,
            'same_historical_place_key': same_verified_place_ref,
            'shared_original_source_group':same_origin,
            'event_year_gap':years,
            'reported_census_birth_range_a':age_a,
            'reported_census_birth_range_b':age_b,
        },
        'warnings': warnings,
        'explanation': 'Heuristic record retrieval rank only; not identity proof or a genealogical probability',
    }
