#!/usr/bin/env python3
"""Make many non-overlapping chatbot tasks; does not contact a chatbot or source."""
import argparse
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps'/'research-web'))
from app.research.acquisition_core import make_prompt

KIND_GROUPS={'civil_bmd':['birth','marriage','death'],
             'church':['baptism','marriage','burial'],
             'households':['census','directory'],
             'estates':['probate']}

def generate(surnames,areas,start,end,step,dest,max_items=40):
    if not 1<=step<=100:raise ValueError('Shard period 1–100 years')
    dest=Path(dest)
    if dest.exists() and any(dest.iterdir()):raise ValueError('Output folder must be new or empty; no overwrite')
    dest.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name in surnames:
        for area in areas:
            for year in range(start,end+1,step):
                through=min(end,year+step-1)
                for kind,classes in KIND_GROUPS.items():
                    text=make_prompt(name,area,year,through,max_records=max_items,record_types=classes)
                    filename=f'PROMPT-{len(rows)+1:06d}.txt'
                    (dest/filename).write_text(text,encoding='utf-8')
                    rows.append({'file':filename,'surname':name,'area':area,'start_year':year,
                                 'end_year':through,'types':','.join(classes),'status':'not_searched'})
    with (dest/'TASK_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['file'])
        w.writeheader();w.writerows(rows)
    (dest/'README.txt').write_text('These are proposed AI research shards, NOT executed searches. Record actual searches, rights, results and unsearched shards. Never upload living-person details without authorisation.\n',encoding='utf-8')
    return len(rows)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--surnames',required=True,help='Comma-separated surnames (do not include living-person details)')
    p.add_argument('--areas',required=True,help='Comma-separated counties/historic areas')
    p.add_argument('--start',type=int,default=1800);p.add_argument('--end',type=int,default=1900)
    p.add_argument('--step-years',type=int,default=20)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        n=generate([s.strip() for s in a.surnames.split(',') if s.strip()],
            [s.strip() for s in a.areas.split(',') if s.strip()],a.start,a.end,a.step_years,a.out)
    except ValueError as e:p.error(str(e))
    print(f'{n} source-controlled AI prompt shards generated (NONE searched or executed).')
