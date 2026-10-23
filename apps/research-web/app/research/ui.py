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
<button data-tab="observations">Person appearances</button><button data-tab="historical">Historical places</button><button data-tab="hypotheses">Family hypotheses</button><button data-tab="gramps">Gramps review (dry-run)</button><button data-tab="jobs">Research tasks</button>
</nav><main><div id="message" role="status" aria-live="polite"></div>
<section id="overview"><div class="panel"><h2>Research summary</h2><div id="summary" class="grid"></div><p class="hint">Accepted people and relationships remain in Gramps Web. All records and hypotheses here are provisional; no Gramps writes are implemented.</p><a href="/" rel="noopener">Return to foundation</a></div></section>
<section id="documents" hidden><div class="panel"><h2>WP-010 — Original-source dependence</h2>
<p class="warning">Two websites reproducing one original register are not independent corroborating evidence. These checks never merge documents or identities.</p>
<label>Source document UUIDs (comma-separated, up to 100) <input id="dependence-ids" placeholder="First source UUID, second source UUID"></label>
<button class="action" id="dependence-check" type="button">Assess possible shared originals</button>
<pre id="dependence-results" aria-live="polite">No assessment requested.</pre>
</div><div class="grid"><div class="panel"><h2>Register a historical document</h2>
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
<section id="historical" hidden><div class="grid"><div class="panel"><h2>Historic parish / place evidence</h2>
<p class="warning">Locations must be supported by a registered document. These records do not automatically establish jurisdiction boundaries or distances.</p>
<form id="historical-form">
<label>Source document UUID <input name="source_document_id" required></label>
<label>Unique source place key <input name="place_key" required></label>
<label>Historic place label <input name="label" required></label>
<label>County name in source <input name="county_label"></label>
<label>Jurisdiction <select name="jurisdiction_type"><option>undetermined</option><option>parish</option><option>chapelry</option><option>settlement</option><option>county</option><option>registration_district</option></select></label>
<label>From year (optional) <input name="valid_from_year" type="number" min="1000" max="2100"></label>
<label>To year (optional) <input name="valid_to_year" type="number" min="1000" max="2100"></label>
<label>Original evidence explanation <textarea name="evidence_note" required></textarea></label>
<button class="action primary">Register source-backed place</button></form></div>
<div class="panel"><h2>Search historic labels</h2><label>Place or county <input id="historical-q" placeholder="Parish, settlement or county"></label>
<button class="action" id="historical-search" type="button">Search registered places</button><div id="historical-list" class="results"></div>
<p class="hint">The programme does not have an authoritative complete English parish gazetteer yet. Do not infer actual distances from text matches.</p></div></div></section>
<section id="hypotheses" hidden><div class="panel"><h2>Competing family hypotheses</h2><p class="warning">The "other or unknown" alternative is mandatory. Unscored hypotheses remain unscored until validated probability calibration is available.</p><div id="hypothesis-list" class="results"></div><div id="graph-comparison" class="panel"><h3>Alternative branch comparison</h3><p class="hint">Select a hypothesis above to inspect versioned proposed relationships, source-group warnings and unknown possibilities. No numerical probabilities or accepted-tree updates are implied.</p></div><p class="hint">Versioned graph editing and research reviews are available through the documented local API.</p></div></section>
<section id="gramps" hidden><div class="panel"><h2>Gramps change preview — no accepted-tree writes</h2>
<p class="warning">WP-006 only prepares and records proposals. A human approval here permits future validation, <strong>not execution</strong>. The supplied handles are not checked against a live Gramps installation. Do not use real family data until recovery testing is accepted.</p>
<form id="gramps-preview-form">
<label>Hypothesis set UUID <input name="hypothesis_set_id" required></label>
<label>Selected option key <input name="option_key" required></label>
<label>Current set version <input name="expected_set_version" type="number" min="1" required></label>
<label>Latest branch revision UUID <input name="expected_revision_id" required></label>
<label>Edge mappings as JSON array (edge_key, from_handle, to_handle)<textarea name="bindings" required placeholder='[{"edge_key":"edge-1","from_handle":"ABC","to_handle":"DEF"}]'></textarea></label>
<button type="submit" class="action primary">Preview proposed links</button></form>
<h3>Immutable proposed changes</h3><pre id="gramps-preview-result">No preview generated</pre>
<label>Reason for recording this proposal <textarea id="gramps-note" placeholder="Explain candidate family and supporting original sources"></textarea></label>
<button class="action" id="gramps-store" type="button" disabled>Record reviewed proposal</button>
<div id="gramps-approval" hidden><h3>Research approval record</h3>
<p class="hint">Only a previously research-supported branch can be recorded and approved. This action never modifies Gramps.</p>
<label>Decision <select id="gramps-decision"><option value="approve_for_future_validation">Approve for future live validation</option><option value="reject">Reject plan</option></select></label>
<label>Exact confirmation phrase <input id="gramps-confirm" placeholder="APPROVE PLAN [12-character digest prefix]"></label>
<label>Decision rationale <textarea id="gramps-rationale" required></textarea></label>
<button type="button" class="action" id="gramps-decide">Record decision (no Gramps write)</button></div>
<pre id="gramps-output">No proposal recorded</pre>
<div class="panel"><h3>WP-007: Gramps live read-only validation</h3>
<p class="warning">Runs authenticated GET calls to inspect claimed Gramps person and family handles. Read-only findings are NOT approval to modify the accepted tree, and upstream objects can change after the check.</p>
<label>Approved plan UUID <input id="gramps-validate-id" placeholder="Existing approved plan UUID"></label>
<button type="button" class="action" id="gramps-live-read">Validate handles against live Gramps (read-only)</button>
<button type="button" class="action" id="gramps-live-history">View validation history</button>
<pre id="gramps-live-result">No live validation performed</pre></div></div></section>
<section id="jobs" hidden><div class="panel"><h2>WP-011 — Staged research tasks</h2>
<p class="warning">Only local review tasks are claimable. Manual websites, approved APIs, external searches and paid services are not executed by this application.</p>
<form id="task-form">
<label>Job UUID <input name="job_id" required></label>
<label>Idempotency task key <input name="task_key" required placeholder="review-parish-0001"></label>
<label>Task type <select name="kind"><option>local_review</option><option>manual_lookup</option><option>approved_api_request</option></select></label>
<label>Provider/source name <input name="source_provider" required value="local_manual"></label>
<label>Reserved budget (cents) <input type="number" name="reserved_cost_cents" min="0" value="0"></label>
<button class="action primary" type="submit">Register research task</button></form>
<label>Inspect tasks for job UUID <input id="tasks-job-id"></label>
<button class="action" id="tasks-inspect">Show tasks and cost budget</button><pre id="tasks-result" aria-live="polite"></pre>
</div><div class="grid"><div class="panel"><h2>Research task</h2><form id="job-form"><label>Research objective <textarea name="objective" required placeholder="Investigate parents of ..."></textarea></label>
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
data.forEach(x=>{const card=item(root,[x.person_name_verbatim,'Event: '+x.event_type+' | '+x.event_date_verbatim+' | '+x.location_verbatim,'ID: '+x.id]);const hb=elt('button','Historical candidate triage','action');hb.onclick=async()=>{try{const res=await api('/observations/'+x.id+'/historical-candidates');const dest=document.querySelector('#matches-list');dest.replaceChildren();dest.append(elt('p',res.warning,'warning'));res.candidates.forEach(y=>item(dest,[y.name_as_recorded,'Heuristic rank '+y.ranking_score+' — NOT a probability',...y.warnings]));}catch(e){notify(e.message,true)}};card.append(hb);const b=elt('button','Suggest identity matches','action');b.onclick=async()=>{try{const res=await api('/observations/'+x.id+'/suggest-matches','POST');const dest=document.querySelector('#matches-list');dest.replaceChildren();dest.append(elt('p',res.warning,'warning'));res.candidates.forEach(y=>item(dest,[y.person_name_verbatim,'Rank '+y.ranking_score+' (NOT a probability)',y.explanation]));}catch(e){notify(e.message,true)}};card.append(b);});}
async function loadGraph(groupId){
const root=document.querySelector('#graph-comparison');root.replaceChildren();root.append(elt('h3','Competing relationship branches'));
const data=await api('/hypotheses/'+encodeURIComponent(groupId)+'/graph');
root.append(elt('p','Set revision '+data.version+' · unscored hypotheses · accepted tree unchanged','hint'));
for(const o of data.options){
  const card=elt('div',undefined,'item');
  card.append(elt('strong',o.description+(o.is_unknown?' (other / unknown)':'')));
  if(!o.revision){card.append(elt('div','No graph revision supplied'));root.append(card);continue;}
  card.append(elt('div','Revision '+o.revision.revision_number+'; '+o.edges.length+' asserted relationships'));
  for(const e of o.edges){card.append(elt('div',e.relationship_type+': '+e.from_observation_id+' → '+e.to_observation_id));}
  for(const warning of o.revision.assessment.warnings){card.append(elt('p','Review: '+warning,'hint'));}
  root.append(card);
}
root.append(elt('p','Structural comparison only. Original source groups may not be independent.','hint'));
}
async function loadHypotheses(){const data=await api('/hypotheses');const root=document.querySelector('#hypothesis-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.title,x.relation_type,'State: '+x.status]);x.options.forEach(o=>card.append(elt('div',(o.is_unknown?'[Unidentified] ':'')+o.description+' | '+(o.calibrated_probability===null?'unscored':o.calibrated_probability))));const btn=elt('button','Compare proposed branches','action');btn.type='button';btn.addEventListener('click',()=>loadGraph(x.id).catch(e=>notify(e.message,true)));card.append(btn);});}
async function loadJobs(){const data=await api('/jobs');const root=document.querySelector('#jobs-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.objective,'ID: '+x.id,'Mode: '+x.mode+' | '+x.status,'Budget: $'+x.cost_limit_usd]);for(const action of ['pause','resume','cancel']){const b=elt('button',action,'action');b.onclick=async()=>{try{await api('/jobs/'+x.id+'/control','POST',{action});await loadJobs()}catch(e){notify(e.message,true)}};card.append(b);}});}
const loaders={overview:loadSummary,documents:loadDocuments,observations:loadObservations,historical:loadHistorical,hypotheses:loadHypotheses,gramps:async()=>{},jobs:loadJobs};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=async()=>{document.querySelectorAll('[data-tab]').forEach(c=>c.classList.toggle('active',c===b));document.querySelectorAll('main>section').forEach(s=>s.hidden=(s.id!==b.dataset.tab));try{await loaders[b.dataset.tab]()}catch(e){notify(e.message,true)}});
document.querySelector('#dependence-check').onclick=async()=>{
  try{const ids=document.querySelector('#dependence-ids').value.split(',').map(x=>x.trim()).filter(Boolean);
    const data=await api('/source-dependence/assess','POST',{document_ids:ids});
    document.querySelector('#dependence-results').textContent=JSON.stringify(data,null,2);
  }catch(e){notify(e.message,true)}
};
document.querySelector('#task-form').onsubmit=async e=>{e.preventDefault();try{
  const data=formFields(e.target);const id=data.job_id;delete data.job_id;
  data.reserved_cost_cents=Number(data.reserved_cost_cents||0);data.input_json={};
  const result=await api('/jobs/'+encodeURIComponent(id)+'/tasks','POST',data);
  notify('Research task registered '+result.id+'. No external execution occurred.');await loadJobs();
}catch(e){notify(e.message,true)}};
document.querySelector('#tasks-inspect').onclick=async()=>{
  try{const id=encodeURIComponent(document.querySelector('#tasks-job-id').value.trim());
    const tasks=await api('/jobs/'+id+'/tasks');const budget=await api('/jobs/'+id+'/budget');
    document.querySelector('#tasks-result').textContent=JSON.stringify({budget,tasks},null,2);
  }catch(e){notify(e.message,true)}
};
document.querySelector('#doc-search').onclick=()=>loadDocuments().catch(e=>notify(e.message,true));
document.querySelector('#ob-search').onclick=()=>loadObservations().catch(e=>notify(e.message,true));
document.querySelector('#document-form').onsubmit=async e=>{e.preventDefault();try{const data=await api('/documents','POST',formFields(e.target));notify('Document '+(data.created?'registered':'already exists')+' | UUID: '+data.id);e.target.reset();await loadDocuments()}catch(err){notify(err.message,true)}};
document.querySelector('#observation-form').onsubmit=async e=>{e.preventDefault();try{const data=formFields(e.target);const doc=data.document_id;delete data.document_id;const result=await api('/documents/'+encodeURIComponent(doc)+'/observations','POST',data);notify('Person appearance '+(result.created?'created':'already exists')+' | '+result.id);await loadObservations()}catch(err){notify(err.message,true)}};
document.querySelector('#job-form').onsubmit=async e=>{e.preventDefault();try{const v=formFields(e.target);v.cost_limit_usd=Number(v.cost_limit_usd||0);const result=await api('/jobs','POST',v);notify('Job stored as '+result.status+'; execution engine pending');await loadJobs()}catch(err){notify(err.message,true)}};
async function loadHistorical(){const q=document.querySelector('#historical-q').value;
  const rows=await api('/historical-places?q='+encodeURIComponent(q));
  const root=document.querySelector('#historical-list');root.replaceChildren();
  rows.forEach(x=>item(root,[x.label+' · '+x.county_label,'Jurisdiction: '+x.jurisdiction_type,
    'Years: '+(x.valid_from_year??'?')+'–'+(x.valid_to_year??'?'), 'Source UUID: '+x.source_document_id,
    'Evidence: '+x.evidence_note]));}
document.querySelector('#historical-search').onclick=()=>loadHistorical().catch(e=>notify(e.message,true));
document.querySelector('#historical-form').onsubmit=async e=>{e.preventDefault();try{
  const b=formFields(e.target); b.aliases_json=[];
  for(const key of ['valid_from_year','valid_to_year'])if(b[key]==='')delete b[key];else if(b[key]!==undefined)b[key]=Number(b[key]);
  const x=await api('/historical-places','POST',b);notify('Historic place '+(x.created?'registered':'already recorded')+' '+x.id);
  await loadHistorical();
}catch(error){notify(error.message,true)}};
let grampsPreviewRequest=null, grampsPreview=null, grampsPlan=null;
document.querySelector('#gramps-preview-form').onsubmit=async e=>{e.preventDefault();
  try{const b=formFields(e.target);b.expected_set_version=Number(b.expected_set_version);b.bindings=JSON.parse(b.bindings);
    grampsPreview=await api('/gramps/plans/preview','POST',b);grampsPreviewRequest=b;grampsPlan=null;
    document.querySelector('#gramps-preview-result').textContent=JSON.stringify(grampsPreview,null,2);
    document.querySelector('#gramps-store').disabled=false;
    document.querySelector('#gramps-approval').hidden=true;notify('Dry-run preview generated; Gramps is unchanged.');
  }catch(err){grampsPreview=null;document.querySelector('#gramps-store').disabled=true;notify(err.message,true)}};
document.querySelector('#gramps-store').onclick=async()=>{
  if(!grampsPreview||!grampsPreviewRequest)return;
  try{const note=document.querySelector('#gramps-note').value.trim();if(note.length<12)throw Error('Explain the reason in at least 12 characters');
    const input={...grampsPreviewRequest,idempotency_key:crypto.randomUUID(),operator_note:note,expected_preview_digest:grampsPreview.digest_sha256};
    grampsPlan=await api('/gramps/plans','POST',input);
    document.querySelector('#gramps-output').textContent=JSON.stringify(grampsPlan,null,2);
    document.querySelector('#gramps-confirm').placeholder='APPROVE PLAN '+grampsPlan.digest_sha256.slice(0,12);
    document.querySelector('#gramps-approval').hidden=false;
    document.querySelector('#gramps-store').disabled=true;notify('Proposal recorded; accepted Gramps tree remains unchanged.');
  }catch(err){notify(err.message,true)}};
document.querySelector('#gramps-decide').onclick=async()=>{
  if(!grampsPlan)return;
  try{const decision=document.querySelector('#gramps-decision').value;
    const input={decision,expected_set_version:grampsPlan.set_version_after_creation,
      expected_preview_digest:grampsPlan.digest_sha256,confirmation:document.querySelector('#gramps-confirm').value.trim(),
      rationale:document.querySelector('#gramps-rationale').value.trim()};
    const output=await api('/gramps/plans/'+grampsPlan.id+'/decisions','POST',input);
    document.querySelector('#gramps-output').textContent=JSON.stringify(output,null,2);
    document.querySelector('#gramps-approval').hidden=true;notify('Decision recorded. No accepted-tree mutation was performed.');
  }catch(err){notify(err.message,true)}};
document.querySelector('#gramps-live-read').onclick=async()=>{
  const id=document.querySelector('#gramps-validate-id').value.trim();
  try{const result=await api('/gramps/plans/'+encodeURIComponent(id)+'/read-validate','POST');
    document.querySelector('#gramps-live-result').textContent=JSON.stringify(result,null,2);
    notify('Gramps GET-only inspection completed. No accepted-tree change is authorised.');
  }catch(e){notify(e.message,true)}
};
document.querySelector('#gramps-live-history').onclick=async()=>{
  const id=document.querySelector('#gramps-validate-id').value.trim();
  try{const result=await api('/gramps/plans/'+encodeURIComponent(id)+'/read-validations');
    document.querySelector('#gramps-live-result').textContent=JSON.stringify(result,null,2);
  }catch(e){notify(e.message,true)}
};
loadSummary().catch(e=>notify('Database not ready: '+e.message,true));
</script></body></html>'''


@router.get('/workspace',response_class=HTMLResponse)
def workspace(_:str=Depends(main.authenticate)):
    return HTMLResponse(HTML,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})
