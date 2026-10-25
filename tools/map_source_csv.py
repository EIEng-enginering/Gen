#!/usr/bin/env python3
"""Map user-licensed CSV columns to validated 24 Gen JSONL, without any network.

Never uses guessed field values; all literal values come from explicit mapping or file.
Does not submit source-provider queries or write to any genealogy database.
"""
import argparse,csv,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps'/'research-web'))
from app.research.acquisition_core import IntakeRecord,PROVIDER_POLICIES

def map_file(input_file,mapping_file,output_file,max_rows=1000000):
    source=Path(input_file);mapping_path=Path(mapping_file);dest=Path(output_file)
    if dest.exists():raise ValueError('Output exists: never overwrite research data')
    config=json.loads(mapping_path.read_text(encoding='utf-8'))
    if set(config)-{'columns','defaults'}:raise ValueError('Unexpected mapping sections')
    columns=config['columns'];defaults=config['defaults']
    if not isinstance(columns,dict) or not isinstance(defaults,dict):raise ValueError('Invalid mapping')
    with source.open('r',newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if any(c not in reader.fieldnames for c in columns.values()):raise ValueError('Missing source column')
        dest.parent.mkdir(parents=True,exist_ok=True)
        # Unpublished temporary output never replaces an existing final file.
        tmp=dest.with_suffix(dest.suffix+'.incomplete')
        if tmp.exists():raise ValueError('Unfinished import exists; inspect before retry')
        total=0
        try:
            with tmp.open('x',encoding='utf-8',newline='') as out:
                for row in reader:
                    total+=1
                    if total>max_rows:raise ValueError('Input exceeds capped records')
                    item={**defaults,**{key:row[src] for key,src in columns.items() if row[src] not in (None,'')}}
                    # Explicitly reject catalogue leads disguised as verified observations.
                    rec=IntakeRecord.model_validate(item)
                    out.write(json.dumps(rec.canonical_dict(),ensure_ascii=False,sort_keys=True)+'\n')
            tmp.rename(dest)
        except Exception:
            if tmp.exists():tmp.unlink()
            raise
    return total

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('input_csv',type=Path);p.add_argument('mapping_json',type=Path);p.add_argument('output_jsonl',type=Path)
    p.add_argument('--max-rows',type=int,default=1000000)
    args=p.parse_args()
    try:n=map_file(args.input_csv,args.mapping_json,args.output_jsonl,args.max_rows)
    except (OSError,ValueError) as e:p.error(str(e))
    print(f'{n} rows converted locally; NO records submitted or verified; review rights before staging.')
