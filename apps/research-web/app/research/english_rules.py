"""Historical England-specific conservative rule helpers.

These are research warnings, not claims that records are false. Historical
jurisdiction and old-calendar rules require additional source context.
"""
from datetime import date


def census_age_interval(census_year:int,reported_age:int):
    """Possible age and birth-year ranges; not an identity proof.

    The 1841 instructions normally rounded adult ages down to nearest five;
    enumerators did not always obey. This function reports the conventional
    interval, which can be widened by the research model for transcription and
    enumerator errors.
    """
    if census_year<1841 or census_year%10 not in (1,):
        raise ValueError('This helper is for 1841 and later decennial England/Wales censuses')
    if reported_age<0 or reported_age>125:
        raise ValueError('Invalid reported age')
    if census_year==1841 and reported_age>=15:
        age_min,age_max=reported_age,reported_age+4
    else:
        age_min=age_max=reported_age
    # Whole years at an enumeration date imply birth-year uncertainty +/- 1.
    return {'age_min':age_min,'age_max':age_max,
            'birth_year_min':census_year-age_max-1,
            'birth_year_max':census_year-age_min,
            'warning':'1841 adult ages often rounded down; recorded ages may still contain errors'
              if census_year==1841 else 'Census ages and birthplaces may be inconsistent'}


def chronology_warnings(birth_earliest:date|None,birth_latest:date|None,
                        death_earliest:date|None,death_latest:date|None):
    alerts=[]
    if birth_earliest and birth_latest and birth_earliest>birth_latest:
        alerts.append('Inverted birth date range')
    if death_earliest and death_latest and death_earliest>death_latest:
        alerts.append('Inverted death date range')
    if birth_earliest and death_latest and birth_earliest>death_latest:
        alerts.append('Chronology conflict: earliest birth after latest death')
    return alerts


def parent_age_warning(parent_birth_year:int|None,child_birth_year:int|None):
    if parent_birth_year is None or child_birth_year is None:
        return None
    age=child_birth_year-parent_birth_year
    if age<0:return 'Biological chronology conflict: parent born after child'
    if age<12 or age>70:return 'Unusual parent age; investigate biological, step, adoption and record accuracy'
    return None
