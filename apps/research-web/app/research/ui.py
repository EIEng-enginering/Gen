"""Simple accessible local evidence workspace, no CDN and no external data access."""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app import main

router=APIRouter()

HTML=r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>24 Gen | Evidence Research</title>
<style>
:root { color-scheme: light; --ink:#172c3c; --line:#d5dfe5; --blue:#134968; --muted:#556875; --bg:#f3f6f8 }
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:var(--blue);color:white;padding:16px max(20px,calc((100vw - 1260px)/2));display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center}
header strong{font-size:22px}header small{display:block;opacity:.8} nav{display:flex;flex-wrap:wrap;gap:6px;padding:12px max(16px,calc((100vw - 1260px)/2));background:white;border-bottom:1px solid var(--line)}
nav button,.action{border:1px solid #b8c8d3;background:white;border-radius:7px;padding:9px 12px;cursor:pointer;color:var(--blue);font:inherit} nav button.active{background:var(--blue);color:white} .action.primary{background:var(--blue);color:white}
main{max-width:1260px;margin:auto;padding:20px}.panel{background:white;border:1px solid var(--line);padding:20px;border-radius:12px;margin:0 0 14px}
h2{font-size:18px;margin:0 0 10px}h3{font-size:15px}p{margin:6px 0 12px}.muted,.hint{color:var(--muted)}.hint{font-size:12px}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
label{display:block;font-size:13px;font-weight:600;margin:8px 0 3px}input,select,textarea{font:inherit;width:100%;border:1px solid #a9b8c4;border-radius:7px;padding:9px;background:white}textarea{min-height:80px}input[type='checkbox']{width:auto}
pre{background:#f0f4f6;padding:10px;border-radius:6px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
.results{max-height:460px;overflow-y:auto}.item{border-top:1px solid var(--line);padding:10px 0}.item button{margin-top:6px}.tag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:30px;background:#eaf1f5;margin:2px}.warning{padding:10px 12px;border-left:4px solid #b77e13;background:#fffae9}.notice{margin:6px 0;padding:9px 12px;background:#e7f4ed;border-radius:6px}.error{background:#ffeded;color:#8e2626}
section[hidden]{display:none!important}button:focus,input:focus,select:focus,textarea:focus{outline:2px solid #be812c;outline-offset:2px}
</style></head><body><header><div><strong>24 Gen</strong><small>Research workspace · WP-002 provisional evidence</small></div><span>Private local installation — no automatic external searches</span></header>
<nav aria-label="Research sections">
<button class="active" data-tab="overview">Overview</button><button data-tab="documents">Historical documents</button>
<button data-tab="observations">Person appearances</button><button data-tab="hypotheses">Family hypotheses</button><button data-tab="jobs">Research tasks</button>
</nav><main><div id="message" role="status" aria-live="polite"></div>
<section id="overview"><div class="panel"><h2>Research summary</h2><div id="summary" class="grid"></div><p class="hint">Accepted people and relationships remain in Gramps Web. All records and hypotheses here are provisional; no Gramps writes are implemented.</p><a href="/" rel="noopener">Return to foundation</a></div></section>
<section id="documents" hidden><div class="grid"><div class="panel"><h2>Register a historical document</h2>
<form id="document-form">
<label>Provider <input name="provider" required value="manual_collection"></label>
<label>Original record ID <input name="provider_record_id" required placeholder="Unique archive or local reference"></label>
<label>Document title <input name="title" required></label>
<label>Original citation / reference <input name="reference" required></label>
<label>Original source group <input name="origin_group" required placeholder="Archive + original register/page"></label>
<label>Access method <select name="access_method"><option>user_import</option><option>manual</option><option>approved_api</option><option>licensed_dataset</option></select></label>
<label>Rights / licence <input name="licence" value="user_provided_research_only" required></label>
<label>Original URL (optional) <input name="original_url" type="url"></label>
<button class="action primary" type="submit">Register source</button></form></div>
<div class="panel"><h2>Search source catalogue</h2><input id="doc-q" placeholder="Search by provider, title or citation"><button class="action" id="doc-search">Search</button><div id="documents-list" class="results"></div></div></div></section>
<section id="observations" hidden><div class="grid"><div class="panel"><h2>Register a person appearance</h2><p class="hint">Enter a known document UUID from the source catalogue. A baptism is not automatically a birth and a household member is not automatically a relative.</p>
<form id="observation-form"><label>Document UUID <input name="document_id" required></label>
<label>Unique entry key within document <input name="observation_key" required placeholder="entry-0001"></label>
<label>Event type <select name="event_type"><option>baptism</option><option>birth</option><option>marriage</option><option>death</option><option>burial</option><option>census</option><option>other</option></select></label>
<label>Person's name as written <input name="person_name_verbatim" required></label>
<label>Surname as written <input name="surname_verbatim"></label><label>Given name(s) as written <input name="given_names_verbatim"></label>
<label>Date as written <input name="event_date_verbatim"></label>
<label>Earliest possible date <input name="earliest_iso" type="date"></label><label>Latest possible date <input name="latest_iso" type="date"></label>
<label>Place as written <input name="location_verbatim"></label><label>Occupation <input name="occupation_verbatim"></label>
<label>Document transcription <textarea name="transcription_verbatim"></textarea></label>
<button class="action primary" type="submit">Register appearance</button></form></div>
<div class="panel"><h2>Person appearances</h2><input id="ob-q" placeholder="Name, place or event"><button class="action" id="ob-search">Search</button>
<div id="observations-list" class="results"></div><h3>Potential identity matches</h3><p class="hint">Scores rank review candidates; they are not calibrated probability percentages.</p><div id="matches-list"></div></div></div></section>
<section id="hypotheses" hidden><div class="panel"><h2>Competing family hypotheses</h2><p class="warning">The "other or unknown" alternative is mandatory. Unscored hypotheses remain unscored until validated probability calibration is available.</p><div id="hypothesis-list" class="results"></div><p class="hint">Use the API to create structured, evidence-linked alternatives. Detailed interactive graph editing is a later work package.</p></div></section>
<section id="jobs" hidden><div class="grid"><div class="panel"><h2>Research task</h2><form id="job-form"><label>Research objective <textarea name="objective" required placeholder="Investigate parents of ..."></textarea></label>
<label>Mode <select name="mode"><option value="guided">AI guided (planning only)</option><option value="conventional">Conventional</option><option value="autonomous">Autonomous (paused until worker added)</option></select></label>
<label>Budget cap in USD <input name="cost_limit_usd" type="number" min="0" value="0" step="0.01"></label>
<button class="action primary">Create task</button></form><p class="hint">Tasks are tracked only; this version does not call AI APIs or search external websites automatically.</p></div>
<div class="panel"><h2>Task queue</h2><div id="jobs-list" class="results"></div></div></div></section>
</main><script>
'use strict';
const BASE='/api/v1/research';
const msg=document.querySelector('#message');
function notify(text,error=false){msg.className='notice'+(error?' error':'');msg.textContent=text;}
async function api(path,method='GET',body=null){const cfg={method,headers:{'X-24Gen-Intent':'research'}};
if(body!==null){cfg.headers['Content-Type']='application/json';cfg.body=JSON.stringify(body);}
const resp=await fetch(BASE+path,cfg);let data;try{data=await resp.json()}catch{data={detail:'Unexpected response'}};
if(!resp.ok)throw Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));return data;}
function elt(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e;}
function item(target,lines){let d=elt('div',undefined,'item');lines.forEach(t=>d.append(elt('div',t)));target.append(d);return d;}
function formFields(form){let v=Object.fromEntries(new FormData(form).entries());Object.keys(v).forEach(k=>{if(v[k]==='')delete v[k];});return v;}
async function loadSummary(){const data=await api('/summary');const target=document.querySelector('#summary');target.replaceChildren();Object.entries(data).forEach(([k,v])=>{const b=elt('div',undefined,'panel');b.append(elt('h2',k.replaceAll('_',' ')),elt('strong',v));target.append(b)});}
async function loadDocuments(){const q=document.querySelector('#doc-q').value;const data=await api('/documents?q='+encodeURIComponent(q));const root=document.querySelector('#documents-list');root.replaceChildren();data.forEach(x=>item(root,[x.title,x.provider+' | '+x.reference,'ID: '+x.id,'Rights: '+x.licence]));}
async function loadObservations(){const q=document.querySelector('#ob-q').value;const data=await api('/observations?q='+encodeURIComponent(q));const root=document.querySelector('#observations-list');root.replaceChildren();
data.forEach(x=>{const card=item(root,[x.person_name_verbatim,'Event: '+x.event_type+' | '+x.event_date_verbatim+' | '+x.location_verbatim,'ID: '+x.id]);const b=elt('button','Suggest identity matches','action');b.onclick=async()=>{try{const res=await api('/observations/'+x.id+'/suggest-matches','POST');const dest=document.querySelector('#matches-list');dest.replaceChildren();dest.append(elt('p',res.warning,'warning'));res.candidates.forEach(y=>item(dest,[y.person_name_verbatim,'Rank '+y.ranking_score+' (NOT a probability)',y.explanation]));}catch(e){notify(e.message,true)}};card.append(b);});}
async function loadHypotheses(){const data=await api('/hypotheses');const root=document.querySelector('#hypothesis-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.title,x.relation_type,'State: '+x.status]);x.options.forEach(o=>card.append(elt('div',(o.is_unknown?'[Unidentified] ':'')+o.description+' | '+(o.calibrated_probability===null?'unscored':o.calibrated_probability))));});}
async function loadJobs(){const data=await api('/jobs');const root=document.querySelector('#jobs-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.objective,'Mode: '+x.mode+' | '+x.status,'Budget: $'+x.cost_limit_usd]);for(const action of ['pause','resume','cancel']){const b=elt('button',action,'action');b.onclick=async()=>{try{await api('/jobs/'+x.id+'/control','POST',{action});await loadJobs()}catch(e){notify(e.message,true)}};card.append(b);}});}
const loaders={overview:loadSummary,documents:loadDocuments,observations:loadObservations,hypotheses:loadHypotheses,jobs:loadJobs};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=async()=>{document.querySelectorAll('[data-tab]').forEach(c=>c.classList.toggle('active',c===b));document.querySelectorAll('main>section').forEach(s=>s.hidden=(s.id!==b.dataset.tab));try{await loaders[b.dataset.tab]()}catch(e){notify(e.message,true)}});
document.querySelector('#doc-search').onclick=()=>loadDocuments().catch(e=>notify(e.message,true));
document.querySelector('#ob-search').onclick=()=>loadObservations().catch(e=>notify(e.message,true));
document.querySelector('#document-form').onsubmit=async e=>{e.preventDefault();try{const data=await api('/documents','POST',formFields(e.target));notify('Document '+(data.created?'registered':'already exists')+' | UUID: '+data.id);e.target.reset();await loadDocuments()}catch(err){notify(err.message,true)}};
document.querySelector('#observation-form').onsubmit=async e=>{e.preventDefault();try{const data=formFields(e.target);const doc=data.document_id;delete data.document_id;const result=await api('/documents/'+encodeURIComponent(doc)+'/observations','POST',data);notify('Person appearance '+(result.created?'created':'already exists')+' | '+result.id);await loadObservations()}catch(err){notify(err.message,true)}};
document.querySelector('#job-form').onsubmit=async e=>{e.preventDefault();try{const v=formFields(e.target);v.cost_limit_usd=Number(v.cost_limit_usd||0);const result=await api('/jobs','POST',v);notify('Job stored as '+result.status+'; execution engine pending');await loadJobs()}catch(err){notify(err.message,true)}};
loadSummary().catch(e=>notify('Database not ready: '+e.message,true));
</script></body></html>'''


@router.get('/workspace',response_class=HTMLResponse)
def workspace(_:str=Depends(main.authenticate)):
    return HTMLResponse(HTML,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})
