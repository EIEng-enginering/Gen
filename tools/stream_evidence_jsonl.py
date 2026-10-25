#!/usr/bin/env python3
"""Stream approved user-provided JSONL/CSV into quarantined intake batches.

No external search. Only localhost is accepted. Requires local credentials via env.
Does not import records into the evidence database or accepted Gramps.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
from urllib.error import HTTPError
from base64 import b64encode

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return None

def rows(path,kind):
    if kind=='jsonl':
        with path.open('r',encoding='utf-8-sig') as f:
            for n,line in enumerate(f,1):
                if line.strip():
                    try:v=json.loads(line)
                    except json.JSONDecodeError as e:raise ValueError('Invalid JSON on line '+str(n)) from e
                    if not isinstance(v,dict):raise ValueError('Line '+str(n)+' must be a JSON object')
                    yield v
    else:
        with path.open('r',encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                yield {k:(v if v!='' else None) for k,v in row.items() if k is not None and v is not None and v!=''}

def stream(path,kind,client,input_kind,check,limit):
    batch=[];total=0;parts=0
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    digest=h.hexdigest()[:18]
    for row in rows(path,kind):
        total+=1
        if total>limit:raise ValueError('Safety row cap exceeded')
        batch.append(row)
        if len(batch)==100:
            parts+=1;client(f'acq-{digest}-{parts:07d}',batch,input_kind,check);batch=[]
    if batch:
        parts+=1;client(f'acq-{digest}-{parts:07d}',batch,input_kind,check)
    return total,parts

def main():
    parser=argparse.ArgumentParser(description='24 Gen reviewed local evidence staging')
    parser.add_argument('source',type=Path)
    parser.add_argument('--format',choices=['jsonl','csv'],default='jsonl')
    parser.add_argument('--input-kind',choices=['manual','licensed_bulk','ai_return','user_export'],default='user_export')
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--max-rows',type=int,default=100000)
    parser.add_argument('--confirm-rights',action='store_true')
    parser.add_argument('--execute',action='store_true',help='Actually send to LOCAL staging API; default validates only')
    args=parser.parse_args()
    u=urlsplit(args.url)
    if u.scheme!='http' or u.hostname not in ('localhost','127.0.0.1') or u.port!=8765 or u.username or u.password or u.path not in ('','/'):
        parser.error('Only local http://127.0.0.1:8765 or localhost:8765 accepted')
    if not args.source.is_file() or args.max_rows<1 or args.max_rows>1000000:parser.error('Input file missing or row cap out of range')
    if args.execute and not args.confirm_rights:parser.error('Rights confirmation required for upload')
    def send(key,recs,kind,check):
        if not args.execute:
            from sys import path as syspath
            syspath.insert(0,str(Path(__file__).resolve().parents[1]/'apps'/'research-web'))
            from app.research.acquisition_core import IntakeRequest
            IntakeRequest.model_validate({'batch_key':key,'records':recs,'input_kind':kind,'rights_attestation':True})
            return
        user=os.environ.get('GEN_ADMIN_USER','');pwd=os.environ.get('GEN_ADMIN_PASSWORD','')
        if not user or not pwd:raise ValueError('Set GEN_ADMIN_USER and GEN_ADMIN_PASSWORD; no credentials in command line')
        body=json.dumps({'batch_key':key,'records':recs,'input_kind':kind,'rights_attestation':check}).encode()
        hdr={'Authorization':'Basic '+b64encode((user+':'+pwd).encode()).decode(),
             'Content-Type':'application/json','X-24Gen-Intent':'research'}
        req=Request(args.url.rstrip('/')+'/api/v1/research/acquisition/batches',body,headers=hdr,method='POST')
        try:
            # Never route local credentials through an environment proxy or
            # follow a redirect to another host.
            with build_opener(ProxyHandler({}),NoRedirect()).open(req,timeout=25) as res:
                answer=json.load(res)
                if not answer.get('batch_id'):raise ValueError('Missing batch ID from response')
        except HTTPError as e:raise ValueError('Batch rejected (HTTP '+str(e.code)+'); inspect original file; no raw rows logged') from e
    count,parts=stream(args.source,args.format,send,args.input_kind,args.confirm_rights,args.max_rows)
    print(f'{"STAGED" if args.execute else "VALIDATED ONLY"}: {count} rows, {parts} idempotent batches. No Gramps writes.')
if __name__=='__main__':main()
