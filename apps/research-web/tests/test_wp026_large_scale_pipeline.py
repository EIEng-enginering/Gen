"""No network or external model used; tests streaming scale and research shard bookkeeping."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib.util
import json
from app.research.acquisition_core import IntakeRequest

ROOT=Path(__file__).resolve().parents[3]
def load_script(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_sharded_prompts_have_task_ledger_and_no_runs(tmp_path):
    module=load_script('build_ai_research_shards.py','shards')
    dest=tmp_path/'prompts'
    count=module.generate(['Oldham','Bardsley'],['Cheshire'],1800,1849,25,dest)
    assert count==2*2*4
    entries=(dest/'TASK_MANIFEST.csv').read_text(encoding='utf-8')
    assert entries.count('not_searched')==count
    assert 'automate the public FreeBMD' in (dest/'PROMPT-000001.txt').read_text()
    try: module.generate(['Oldham'],['Cheshire'],1800,1820,20,dest)
    except ValueError:pass
    else:assert False,'Must not overwrite or erase previous research manifests'

def test_stream_jsonl_incremental_chunks(tmp_path):
    module=load_script('stream_evidence_jsonl.py','streamer')
    fixture=ROOT/'fixtures'/'synthetic_cheshire_intake.jsonl'
    row=json.loads(fixture.read_text())
    file=tmp_path/'rows.jsonl'
    with file.open('w',encoding='utf-8') as out:
        for i in range(215):
            item={**row,'provider_record_id':f'FAKE-CHES-{i:05d}'}
            out.write(json.dumps(item)+'\n')
    sent=[]
    def local(key,records,kind,check):
        IntakeRequest.model_validate({'batch_key':key,'records':records,'input_kind':kind,'rights_attestation':True})
        sent.append((key,len(records)))
    count,parts=module.stream(file,'jsonl',local,'user_export',True,500)
    assert count==215 and parts==3 and [n for _,n in sent]==[100,100,15]
    # Deterministic across restarts to avoid duplicated bulk staging
    again=[]
    module.stream(file,'jsonl',lambda k,r,m,c:again.append(k),'user_export',True,500)
    assert [k for k,_ in sent]==again

def test_explicit_licensed_csv_field_mapping(tmp_path):
    mapper=load_script('map_source_csv.py','mapping')
    source=ROOT/'fixtures'/'synthetic_cheshire_export.csv'
    config=ROOT/'fixtures'/'synthetic_csv_field_mapping.json'
    out=tmp_path/'mapped.jsonl'
    assert mapper.map_file(source,config,out)==1
    data=json.loads(out.read_text().strip())
    assert data['person_name_verbatim']=='William Oldham'
    assert data['source_reference']=='FICTIONAL-PARISH-1-PAGE-2'
    assert data['extraction_status']=='unverified_extraction'
    try:mapper.map_file(source,config,out)
    except ValueError:pass
    else: assert False,'Never overwrite converted files'
