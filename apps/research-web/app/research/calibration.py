"""Offline independent pair-match validation and reliability reporting.

No production model is installed by this module. Its purpose is to evaluate
held-out reviewed English genealogy benchmarks and expose false-match risks.
Family/source-network grouping must be applied BEFORE constructing train/test.
"""
import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LabelledCase:
    score: float
    true_match: bool
    family_group: str
    original_source_group: str
    century: int
    county: str


def evaluate(cases:Iterable[LabelledCase],threshold=0.65,bins=10):
    rows=list(cases)
    if not rows:raise ValueError('Cannot evaluate empty benchmark')
    if any(not 0<=r.score<=1 for r in rows): raise ValueError('Scores outside [0,1]')
    if not 0<threshold<1:raise ValueError('Threshold must be in (0,1)')
    tp=sum(r.score>=threshold and r.true_match for r in rows)
    fp=sum(r.score>=threshold and not r.true_match for r in rows)
    tn=sum(r.score<threshold and not r.true_match for r in rows)
    fn=sum(r.score<threshold and r.true_match for r in rows)
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    rows_by_bin=[[] for _ in range(bins)]
    for r in rows:
        i=min(bins-1,int(r.score*bins))
        rows_by_bin[i].append(r)
    reliability=[]
    for i,part in enumerate(rows_by_bin):
        if part:
            average_score=sum(r.score for r in part)/len(part)
            observed_rate=sum(r.true_match for r in part)/len(part)
        else:average_score=observed_rate=None
        reliability.append({'interval':[i/bins,(i+1)/bins],
                            'n':len(part),'average_rank_score':average_score,
                            'empirical_match_fraction':observed_rate})
    brier_if_score_were_probability=sum((r.score-float(r.true_match))**2 for r in rows)/len(rows)
    ece_if_score_were_probability=sum((part['n']/len(rows))*abs(part['average_rank_score']-part['empirical_match_fraction'])
       for part in reliability if part['n'])
    return {'n':len(rows),'tp':tp,'fp':fp,'tn':tn,'fn':fn,'precision':precision,
            'recall':recall,'false_merge_rate':fp/(fp+tn) if fp+tn else None,
            'false_split_rate':fn/(fn+tp) if fn+tp else None,
            'brier_if_rank_score_treated_as_probability':brier_if_score_were_probability,
            'ece_if_rank_score_treated_as_probability':ece_if_score_were_probability,
            'reliability':reliability,
            'warning':'Rank scores are NOT calibrated posteriors; these metrics quantify the gap, not a deployed probability model'}


def check_benchmark_split(train:Iterable[LabelledCase],holdout:Iterable[LabelledCase]):
    """Refuse family/source leakage between development and validation sets."""
    train=list(train);holdout=list(holdout)
    if not train or not holdout:raise ValueError('Both train and holdout need reviewed records')
    for key in ('family_group','original_source_group'):
        seen={getattr(row,key) for row in train}
        overlap=seen.intersection(getattr(row,key) for row in holdout)
        if overlap:
            raise ValueError(f'Leaked {key} between train and holdout: '+','.join(sorted(overlap)[:5]))
    return True
