from datetime import date
import pytest
from app.research.english_rules import census_age_interval,chronology_warnings,parent_age_warning

def test_1841_ages_are_not_exact_for_adults():
    r=census_age_interval(1841,35)
    assert r['age_min']==35 and r['age_max']==39
    assert r['birth_year_min']==1801
    assert r['birth_year_max']==1806
    assert census_age_interval(1841,10)['age_max']==10
    assert census_age_interval(1851,35)['age_max']==35

def test_chronology_flags_only_hard_contradictions():
    assert chronology_warnings(date(1850,1,1),date(1850,12,31),None,date(1840,12,31))
    assert not chronology_warnings(date(1800,1,1),date(1801,1,1),None,date(1850,1,1))
    assert parent_age_warning(1880,1870).startswith('Biological chronology conflict')
    assert parent_age_warning(1800,1810).startswith('Unusual')
    assert parent_age_warning(1800,1830) is None

@pytest.mark.parametrize('year,age',[(1831,30),(1841,-2)])
def test_bad_census_args(year,age):
    with pytest.raises(ValueError):census_age_interval(year,age)
