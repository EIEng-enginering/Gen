"""Reproducible fictional 100k-record *index* benchmark; never uses family data.

Usage from repository root:
PYTHONPATH=apps/research-web python tools/benchmark_general_search.py --rows 100000 --output benchmark.json
"""
import argparse,json,os,platform,random,tempfile,time,uuid
from pathlib import Path
from sqlalchemy import create_engine,select,text
from sqlalchemy.orm import Session
from app.research.models import Base
from app.research.general_search_models import SearchMention
from app.research.general_search_service import search
from app.research.general_search_core import norm,phonetic

COUNTIES=('cheshire','kent','gloucestershire','glamorgan','norfolk','lancashire','surrey','devon')
SURNAMES=('Mercer','Rhys','Sutton','Baxter','Hale','Parsons','Smith','Davis','Reed','Fletcher','Barlow','Morgan')

def run(n=100000,db_path=None):
    rng=random.Random(24026)
    if db_path is None:
        # No real database touched. A temp dir is unique and never overlaps project files.
        fd,db_path=tempfile.mkstemp(prefix='gen24-synthetic-index-',suffix='.sqlite')
        os.close(fd)
        remove=True
    else: remove=False
    eng=create_engine('sqlite+pysqlite:///'+str(db_path))
    try:
        Base.metadata.create_all(eng)
        started=time.perf_counter()
        with eng.begin() as connection:
            for start in range(0,n,5000):
                records=[]
                for i in range(start,min(start+5000,n)):
                    name=SURNAMES[rng.randrange(len(SURNAMES))]; county=COUNTIES[rng.randrange(len(COUNTIES))]
                    year=1600+rng.randrange(310)
                    records.append({'id':uuid.uuid4(),'source_kind':'staged','source_id':str(uuid.uuid4()),
                       'name_literal':'Fictional Person '+name,'surname_literal':name,'surname_key':norm(name),
                       'surname_soundex':phonetic(name),'given_literal':'Fictional','given_key':'fictional',
                       'place_literal':'Imaginary parish, '+county,'place_key':'imaginary parish '+county,
                       'county_key':county,'event_type':'census','year_hint':year,'year_end_hint':year,
                       'provider':'synthetic','source_reference':'FAKE/'+str(i),
                       'source_document_id':'','possible_original':'synthetic/'+str(i//3),
                       'rights_label':'fiction-only','status':'awaiting_human_review'})
                connection.execute(SearchMention.__table__.insert(),records)
        insert_seconds=time.perf_counter()-started
        with Session(eng) as s:
            start=time.perf_counter()
            outcomes=[]
            for _ in range(30):
                result=search(s,surname='Mercer',county_filter='cheshire',year_from=1800,year_to=1850,limit=25)
                outcomes.append(len(result['results']))
            queries_seconds=time.perf_counter()-start
            with eng.connect() as c:
                indexes=c.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='general_search_mentions'")).all()
                plan=c.execute(text("EXPLAIN QUERY PLAN SELECT * FROM general_search_mentions WHERE surname_key='mercer' AND county_key='cheshire' AND year_hint>=1800 ORDER BY id LIMIT 25")).all()
        report={'fixture':'synthetic_random_only','record_count':n,'platform':platform.platform(),
          'python':platform.python_version(),'sqlite_version':__import__('sqlite3').sqlite_version,
          'insert_seconds':round(insert_seconds,3),'thirty_queries_seconds':round(queries_seconds,3),
          'mean_query_ms':round(queries_seconds*1000/30,3),'returned_page_rows':outcomes[0],
          'all_query_counts_identical':len(set(outcomes))==1,
          'indexes':[x[0] for x in indexes], 'sqlite_query_plan':[str(p) for p in plan],
          'postgresql_explain_required':True,
          'limits':'Synthetic materialized index only; excludes provider requests, full import and Gramps retrieval'}
        return report
    finally:
        eng.dispose()
        if remove:os.remove(db_path)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rows',type=int,default=100000)
    parser.add_argument('--output',default='')
    args=parser.parse_args();assert 1<=args.rows<=1000000
    result=run(args.rows)
    result_json=json.dumps(result,indent=2)
    if args.output:Path(args.output).write_text(result_json+'\n',encoding='utf-8')
    print(result_json)
