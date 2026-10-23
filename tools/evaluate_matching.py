"""Offline record-linkage quality audit against independently reviewed cases.

Input CSV must contain: score,true_match,family_group,original_source_group,
century,county. A reviewed BENCHMARK is needed for any production accuracy claim.
The evaluation does NOT calibrate the heuristic ranker into probabilities.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'research-web'))
from app.research.calibration import LabelledCase, evaluate, check_benchmark_split

REQUIRED = set(LabelledCase.__dataclass_fields__)


def read_cases(file_path):
    with Path(file_path).open('r',encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not REQUIRED.issubset(set(reader.fieldnames or [])):
            raise ValueError('Benchmark CSV missing: '+', '.join(sorted(REQUIRED-set(reader.fieldnames or []))))
        rows=[]
        for row in reader:
            try:
                score=float(row['score'])
                if not math.isfinite(score) or not 0<=score<=1:
                    raise ValueError('score must be finite and within [0,1]')
                label=row['true_match'].strip().lower()
                if label not in ('true','false','1','0'):
                    raise ValueError('true_match must be true/false or 1/0')
                if any(not row[x].strip() for x in ('family_group','original_source_group','county')):
                    raise ValueError('family/source/county identifiers cannot be blank')
                rows.append(LabelledCase(score,label in ('true','1'),row['family_group'].strip(),
                            row['original_source_group'].strip(),int(row['century']),row['county'].strip()))
            except (ValueError,KeyError,TypeError) as exc:
                raise ValueError(f'Invalid benchmark row {reader.line_num}: {exc}') from exc
    if not rows:
        raise ValueError('Empty benchmark')
    return rows


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--holdout',required=True,help='Independently reviewed held-out CSV')
    parser.add_argument('--train',help='Optional disjoint development CSV, for leakage screening')
    parser.add_argument('--threshold',type=float,default=0.65)
    parser.add_argument('--output',help='Optional JSON report path')
    args=parser.parse_args(argv)
    holdout=read_cases(args.holdout)
    if args.train:
        train=read_cases(args.train)
        check_benchmark_split(train,holdout)
    result=evaluate(holdout,args.threshold)
    result['benchmark_type']='held_out_reviewed_cases_required'
    result['reference_only']=True
    result['may_deploy_calibrated_probabilities']=False
    result['source_file']=str(Path(args.holdout).name)
    output=json.dumps(result,sort_keys=True,indent=2)
    if args.output:
        Path(args.output).write_text(output+'\n',encoding='utf-8')
    print(output)
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print('BENCHMARK REJECTED: '+str(exc),file=sys.stderr)
        raise SystemExit(2)
