"""Explicit, resumable local search-index projection. Does not migrate DB or fetch providers.

Example:
  GEN_DB_URL=... PYTHONPATH=apps/research-web python tools/reindex_general_search.py --source both --page-size 300
  ... --source staged --after UUID  # resume an interrupted sweep
Always use an explicit project database. Never point this at an unknown production database.
"""
import argparse,json,os,sys
from uuid import UUID
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.research.db import engine
from app.research.general_search_service import sync_page
from app.research.general_search_models import SearchMention


def run(args):
    if not os.getenv('GEN_DB_URL'):
        raise SystemExit('GEN_DB_URL must explicitly identify the intended research database')
    if not args.ack_derived_only:
        raise SystemExit('Supply --ack-derived-only after checking backups and target database')
    eng=engine()
    tables=set(inspect(eng).get_table_names())
    required={'general_search_mentions','observations','source_documents','staged_evidence'}
    if not required<=tables:
        raise SystemExit('Database not at search-index schema revision 010; migration requires separate review')
    completed=[]
    for kind in (('observed','staged') if args.source=='both' else (args.source,)):
        cursor=UUID(args.after) if args.after and args.source==kind else None
        pages=0
        while pages<args.max_pages:
            with Session(eng) as s:
                result=sync_page(s,kind,cursor,args.page_size)
            completed.append(result)
            print(json.dumps(result,sort_keys=True),flush=True)
            pages+=1
            if result['end_of_current_sweep']:break
            cursor=UUID(result['next_after'])
    print(json.dumps({'processed_total':sum(r['processed'] for r in completed),
      'created_total':sum(r['created'] for r in completed),
      'pages':len(completed),'remaining_sweep_pages_unknown':bool(completed and not completed[-1]['end_of_current_sweep']),
      'external_provider_requests':0,'gramps_writes':0},sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',choices=('both','observed','staged'),default='both')
    p.add_argument('--page-size',type=int,choices=range(1,501),metavar='1..500',default=300)
    p.add_argument('--after',default='')
    p.add_argument('--max-pages',type=int,default=100000)
    p.add_argument('--ack-derived-only',action='store_true')
    opts=p.parse_args()
    if opts.after and opts.source=='both':p.error('--after requires one specific --source')
    if opts.max_pages<1:p.error('--max-pages must be positive')
    run(opts)
