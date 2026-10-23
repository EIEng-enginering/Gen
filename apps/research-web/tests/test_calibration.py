import pytest
from app.research.calibration import LabelledCase, evaluate, check_benchmark_split

def c(score,good,family,group):
    return LabelledCase(score,good,family,group,1800,'Kent')

def test_holdout_is_grouped_by_family_and_original_source():
    a=c(.9,True,'smith','register-A')
    b=c(.4,False,'jones','register-B')
    assert check_benchmark_split([a],[b])
    with pytest.raises(ValueError,match='family_group'):
        check_benchmark_split([a],[c(.1,False,'smith','register-B')])
    with pytest.raises(ValueError,match='original_source_group'):
        check_benchmark_split([a],[c(.2,False,'jones','register-A')])

def test_validation_clearly_does_not_call_rank_scores_probabilities():
    r=evaluate([c(.95,True,'a','a1'),c(.85,False,'b','b1'),
                c(.25,False,'c','c1'),c(.2,True,'d','d1')],threshold=.8)
    assert (r['tp'],r['fp'],r['tn'],r['fn'])==(1,1,1,1)
    assert r['precision']==.5 and r['recall']==.5
    assert r['n']==4
    assert 'NOT calibrated' in r['warning']

def test_empty_benchmark_refused():
    with pytest.raises(ValueError):evaluate([])
