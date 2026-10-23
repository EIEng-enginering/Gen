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
.family-diagram{border:1px solid var(--line);border-radius:8px;max-width:100%;overflow:auto;background:#fff}
.family-diagram svg{width:100%;min-width:390px;height:auto;display:block}
.family-branches{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.family-branches .branch-card{border:1px solid var(--line);border-radius:9px;padding:12px;min-width:0}
.family-legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;margin:8px 0}
.family-legend span{padding:2px 6px;border-radius:3px;background:#f3f6f8}
.family-chart-list{font-size:12px;max-height:150px;overflow:auto}
section[hidden]{display:none!important}button:focus,input:focus,select:focus,textarea:focus{outline:2px solid #be812c;outline-offset:2px}
</style></head><body><header><div><strong>24 Gen</strong><small>Research workspace · WP-002–016 provisional research</small></div><span>Private local installation — no automatic external searches</span></header>
<nav aria-label="Research sections">
<button class="active" data-tab="overview">Overview</button><button data-tab="documents">Historical documents</button>
<button data-tab="observations">Person appearances</button><button data-tab="historical">Historical places</button><button data-tab="hypotheses">Family hypotheses</button><button data-tab="gramps">Gramps review (dry-run)</button><button data-tab="jobs">Research tasks</button><button data-tab="evidence">Evidence comparison</button>
<button data-tab="assistant">Guided research assistant</button><button data-tab="ops">Operations dashboard</button>
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

<section id="evidence" hidden><div class="panel"><h2>WP-014 — Document and transcription comparison</h2>
<p class="warning">Historical appearances are not confirmed people. Copies of one original are not independent evidence. Local images below are previewed in your browser only; nothing is uploaded.</p>
<label for="evidence-ids">Two to six observation UUIDs (comma-separated)</label>
<input id="evidence-ids" placeholder="First observation UUID, second observation UUID" aria-describedby="evidence-help">
<p id="evidence-help" class="hint">Register historical records first. Original citation and every available transcription revision will be shown separately.</p>
<button id="evidence-compare" type="button" class="action primary">Compare cited appearances</button>
<div id="evidence-results" class="grid" aria-live="polite"></div>
</div><div class="panel"><h3>Local-only image inspection</h3><p class="hint">Images remain in this browser session. No file is sent to Gramps, 24 Gen or an external service.</p>
<label for="evidence-image">Choose a local image (PNG, JPEG or WebP; maximum 20 MB)</label><input id="evidence-image" type="file" accept="image/png,image/jpeg,image/webp">
<label for="evidence-zoom">Preview zoom</label><input id="evidence-zoom" type="range" min="25" max="300" value="100" step="25">
<div id="evidence-image-panel" class="family-diagram" style="max-height:550px" aria-live="polite"></div>
</div></section>
<section id="assistant" hidden><div class="panel"><h2>WP-015 — Citation-grounded research guidance</h2>
<p class="warning">The current assistant is an offline research guide, not a running language model. It does not search provider websites, run cloud AI or alter Gramps records.</p>
<form id="assistant-form"><label>Research question<textarea name="question" required minlength="4" maxlength="1000" placeholder="Could these appearances be the same person?"></textarea></label>
<label>Research mode<select name="mode"><option value="guided">Guided steps</option><option value="conventional">Conventional record review</option><option value="autonomous">Autonomous plan only — execution disabled</option></select></label>
<label>Observation UUIDs (optional, comma-separated; maximum six)<input name="observation_ids" placeholder="Cited record appearances"></label>
<button class="action primary">Generate source-grounded review plan</button></form>
<div id="assistant-results" aria-live="polite"></div></div></section>
<section id="ops" hidden><div class="panel"><h2>WP-016 — Research operations</h2><p class="warning">Local task reservations and reported costs are not evidence of real provider usage. Paid and automated execution remain disabled.</p>
<button id="ops-refresh" class="action" type="button">Refresh dashboard</button><div id="ops-summary" class="grid" aria-live="polite"></div>
</div><div class="grid"><div class="panel"><h3>Human review queue</h3><div id="ops-reviews" class="results"></div></div>
<div class="panel"><h3>Job and budget inspection</h3><label for="ops-job-id">Research job UUID</label><input id="ops-job-id" placeholder="Existing job UUID">
<button id="ops-inspect" type="button" class="action">Show job detail</button><pre id="ops-detail" aria-live="polite"></pre></div></div></section>
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
// WP-012/013: SVG is assembled through DOM APIs; source-record text is never parsed as HTML.
function svgElement(tag,attributes={}){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
  Object.entries(attributes).forEach(([key,value])=>e.setAttribute(key,String(value)));return e;}
function drawBranch(diagram,target,zoom=100){target.replaceChildren();
  const title=elt('h3',diagram.description+(diagram.is_unknown?' (other / unknown)':''));target.append(title);
  target.append(elt('p',diagram.interpretation+' · Not a verified or accepted tree','hint'));
  if(!diagram.nodes.length){target.append(elt('p','No family relationships asserted in this alternative. An unidentified relative remains possible.','warning'));return;}
  const container=elt('div',undefined,'family-diagram');
  const svg=svgElement('svg',{viewBox:'0 0 '+diagram.width+' '+diagram.height,role:'img',
    'aria-label':'Diagram of '+diagram.nodes.length+' historical appearances and '+diagram.links.length+' proposed relationships'});
  const positions=new Map(diagram.nodes.map(n=>[n.id,n]));
  diagram.links.forEach(link=>{const from=positions.get(link.source_id),to=positions.get(link.target_id);if(!from||!to)return;
    const path=svgElement('path',{d:'M '+(from.x+95)+' '+(from.y+66)+' L '+(to.x+95)+' '+(to.y+4),
      stroke:link.has_contradiction?'#a63d32':'#42657b','stroke-width':'2',fill:'none',
      'stroke-dasharray':link.style==='dashed'?'6 5':'none'});
    path.append(svgElement('title')).textContent=link.relationship_type+(link.has_contradiction?' — contradictory evidence':'');svg.append(path);});
  diagram.nodes.forEach(node=>{const box=svgElement('g');const rect=svgElement('rect',{
    x:node.x,y:node.y,width:190,height:70,rx:7,fill:'#f5f9fb',stroke:'#486778','stroke-width':1.3});box.append(rect);
    const name=svgElement('text',{x:node.x+8,y:node.y+22,'font-size':12,'font-weight':600,fill:'#173654'});
    name.textContent=(node.label||'Unidentified').slice(0,26);box.append(name);
    const detail=svgElement('text',{x:node.x+8,y:node.y+42,'font-size':11,fill:'#465866'});
    detail.textContent=(node.event_type+' '+(node.date_as_written||'')).slice(0,29);box.append(detail);
    const type=svgElement('text',{x:node.x+8,y:node.y+57,'font-size':10,fill:'#657982'});
    type.textContent='Record appearance · not confirmed';box.append(type);
    box.append(svgElement('title')).textContent=node.label+' — '+node.event_type+' '+node.date_as_written+' '+node.place_as_written;
    svg.append(box);});
  svg.style.width=String(zoom)+'%';svg.style.maxWidth='none';container.append(svg);target.append(container);
  const details=elt('details');details.append(elt('summary','Relationship details ('+diagram.links.length+')'));
  const list=elt('div',undefined,'family-chart-list');
  diagram.links.forEach(link=>list.append(elt('div',link.relationship_type+' · '+(positions.get(link.source_id)?.label||link.source_id)+' → '+(positions.get(link.target_id)?.label||link.target_id))));
  details.append(list);target.append(details);
  if(diagram.edge_assessments.length){const warning=elt('p','Potential shared-original evidence groups do not establish independent corroboration.','warning');target.append(warning);
    diagram.edge_assessments.forEach(edge=>target.append(elt('p',edge.edge_key+': '+edge.potential_original_group_count+' possible-original groups · '+
      edge.distinct_declared_origin_groups+' legacy declared-origin groups · independence unverified','hint')));}
  diagram.warnings.forEach(w=>target.append(elt('p','Review: '+w,'hint')));
}
async function loadGraph(groupId){
  const root=document.querySelector('#graph-comparison');root.replaceChildren();root.append(elt('h3','Interactive provisional family tree'));
  const data=await api('/hypotheses/'+encodeURIComponent(groupId)+'/graph');
  root.append(elt('p','Set revision '+data.version+' · all options unscored · accepted Gramps tree unchanged','warning'));
  const options=data.options.map(x=>({key:x.option_key,label:x.description+(x.is_unknown?' (unidentified)':'')}));
  const controls=elt('div',undefined,'grid');
  function selector(label,id,initial){const panel=elt('div');const lbl=elt('label',label);lbl.setAttribute('for',id);panel.append(lbl);
    const sel=elt('select');sel.id=id;options.forEach(o=>{const opt=elt('option',o.label);opt.value=o.key;sel.append(opt)});sel.value=initial;panel.append(sel);controls.append(panel);return sel;}
  const left=selector('Family alternative A','chart-left',options[0]?.key);
  const right=selector('Family alternative B','chart-right',options[1]?.key||options[0]?.key);
  root.append(controls);
  const line=elt('div',undefined,'row');const zoomLabel=elt('label','Diagram zoom');zoomLabel.setAttribute('for','family-zoom');
  const zoom=elt('input');zoom.id='family-zoom';zoom.type='range';zoom.min='80';zoom.max='250';zoom.step='10';zoom.value='100';
  zoom.style.width='200px';line.append(zoomLabel,zoom);
  const go=elt('button','Compare selected alternatives','action');go.type='button';line.append(go);root.append(line);
  const legend=elt('div',undefined,'family-legend');['Solid line: proposed parent link','Dashed: other proposed relationship','Red: recorded contradiction','All nodes: historical appearances'].forEach(x=>legend.append(elt('span',x)));
  root.append(legend);
  const views=elt('div',undefined,'family-branches');const a=elt('div',undefined,'branch-card'),b=elt('div',undefined,'branch-card');views.append(a,b);root.append(views);
  const difference=elt('div',undefined,'panel');root.append(difference);
  async function refresh(){try{
    if(left.value===right.value){notify('Choose two different alternatives for comparison',true);return;}
    const response=await api('/hypotheses/'+encodeURIComponent(groupId)+'/compare-view?left='+encodeURIComponent(left.value)+'&right='+encodeURIComponent(right.value));
    drawBranch(response.left,a,Number(zoom.value));drawBranch(response.right,b,Number(zoom.value));
    difference.replaceChildren(elt('h3','Structural differences'),elt('p','Shared proposed links: '+response.comparison.common.length+
      ' · only A: '+response.comparison.only_left.length+' · only B: '+response.comparison.only_right.length));
    difference.append(elt('p',response.comparison.warning,'hint'));
    if(response.other_or_unknown_available)difference.append(elt('p','Other or unidentified relatives remain an explicit alternative.','hint'));
  }catch(error){notify(error.message,true)}}
  go.onclick=refresh;zoom.onchange=refresh;
  if(options.length>=2)await refresh();else root.append(elt('p','At least two alternatives are required to compare.','hint'));
}
async function loadHypotheses(){const data=await api('/hypotheses');const root=document.querySelector('#hypothesis-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.title,x.relation_type,'State: '+x.status]);x.options.forEach(o=>card.append(elt('div',(o.is_unknown?'[Unidentified] ':'')+o.description+' | '+(o.calibrated_probability===null?'unscored':o.calibrated_probability))));const btn=elt('button','Compare proposed branches','action');btn.type='button';btn.addEventListener('click',()=>loadGraph(x.id).catch(e=>notify(e.message,true)));card.append(btn);});}
async function loadJobs(){const data=await api('/jobs');const root=document.querySelector('#jobs-list');root.replaceChildren();data.forEach(x=>{const card=item(root,[x.objective,'ID: '+x.id,'Mode: '+x.mode+' | '+x.status,'Budget: $'+x.cost_limit_usd]);for(const action of ['pause','resume','cancel']){const b=elt('button',action,'action');b.onclick=async()=>{try{await api('/jobs/'+x.id+'/control','POST',{action});await loadJobs()}catch(e){notify(e.message,true)}};card.append(b);}});}
const loaders={overview:loadSummary,documents:loadDocuments,observations:loadObservations,historical:loadHistorical,hypotheses:loadHypotheses,gramps:async()=>{},jobs:loadJobs,evidence:async()=>{},assistant:async()=>{},ops:loadOperations};
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

// WP-014: source-cited comparison with local-only image preview.
document.querySelector('#evidence-compare').onclick=async()=>{try{
  const ids=document.querySelector('#evidence-ids').value.split(',').map(v=>v.trim()).filter(Boolean);
  const data=await api('/evidence/compare','POST',{observation_ids:ids});
  const out=document.querySelector('#evidence-results');out.replaceChildren();
  out.append(elt('p',data.warning,'warning'));
  for(const d of data.observations){const box=elt('article',undefined,'panel');
    box.append(elt('h3',d.record.name_verbatim+' · '+d.record.event_type),
      elt('p','Event: '+(d.record.event_date_verbatim||'not specified')+' · Place: '+(d.record.place_verbatim||'not specified')),
      elt('p','Citation: '+d.citation.provider+' / '+d.citation.title+' / '+d.citation.reference),
      elt('p','Source ID: '+d.citation.document_id+' · Licence: '+d.citation.licence,'hint'));
    if(d.citation.rights_note)box.append(elt('p','Rights: '+d.citation.rights_note,'hint'));
    box.append(elt('h3','Original recorded reading'),elt('pre',d.record.initial_transcription));
    const rev=elt('details');rev.append(elt('summary','Transcription history ('+d.revision_history.length+')'));
    d.revision_history.forEach(r=>rev.append(elt('p','Editor '+r.editor+' · Reason '+r.reason+' · '+r.created_at),elt('pre',r.text)));
    box.append(rev);out.append(box);
  }
  if(data.literal_differences.length)out.append(elt('p','Literal differences: '+data.literal_differences.map(d=>d.field).join(', '),'warning'));
  out.append(elt('p','Possible original-source groups: '+data.source_dependence_groups.length+'. Separate groups do not prove independent corroboration.','warning'));
  notify('Source-cited comparison retrieved. No source image was uploaded.');
}catch(e){notify(e.message,true)}};
let evidenceImageUrl=null;
const imagePanel=document.querySelector('#evidence-image-panel');
function clearLocalImage(){if(evidenceImageUrl)URL.revokeObjectURL(evidenceImageUrl);evidenceImageUrl=null;imagePanel.replaceChildren();}
document.querySelector('#evidence-image').onchange=e=>{
  clearLocalImage();const file=e.target.files?.[0];if(!file)return;
  if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>20*1024*1024){notify('Choose a PNG, JPEG or WebP under 20 MB.',true);e.target.value='';return;}
  evidenceImageUrl=URL.createObjectURL(file);const pic=elt('img');pic.alt='Local-only document preview';pic.src=evidenceImageUrl;
  pic.style.maxWidth='none';pic.style.width='100%';pic.style.height='auto';pic.onload=()=>notify('Local image preview loaded without upload.');
  imagePanel.append(pic);document.querySelector('#evidence-zoom').value='100';
};
document.querySelector('#evidence-zoom').oninput=e=>{
  const pic=imagePanel.querySelector('img');if(pic)pic.style.width=e.target.value+'%';
};
window.addEventListener('pagehide',clearLocalImage);
// WP-015: evidence-based offline guidance. No LLM or provider request.
document.querySelector('#assistant-form').onsubmit=async e=>{e.preventDefault();try{
  const b=formFields(e.target);b.observation_ids=(b.observation_ids||'').split(',').map(x=>x.trim()).filter(Boolean);
  const a=await api('/assistant/answer','POST',b);const root=document.querySelector('#assistant-results');root.replaceChildren();
  root.append(elt('p',a.warning,'warning'),elt('h3','Cited summary'),elt('p',a.summary),elt('p',a.mode_explanation,'hint'));
  root.append(elt('h3','Source citations'));
  a.citations.forEach(c=>root.append(elt('p',c.provider+' · '+c.reference+' · Observation '+c.observation_id)));
  if(!a.citations.length)root.append(elt('p','No source observations supplied.','hint'));
  root.append(elt('h3','Next research steps'));
  const list=elt('ol');a.research_steps.forEach(step=>list.append(elt('li',step)));root.append(list);
}catch(err){notify(err.message,true)}};
// WP-016: state displays only, existing protected APIs own permitted controls.
async function loadOperations(){const [dashboard,reviews]=await Promise.all([api('/ops/dashboard'),api('/ops/reviews')]);
  const root=document.querySelector('#ops-summary');root.replaceChildren();
  const totals=elt('div',undefined,'panel');totals.append(elt('h3','Records and work'));
  Object.entries(dashboard.counts).forEach(([key,val])=>totals.append(elt('p',key.replaceAll('_',' ')+': '+val)));
  root.append(totals);
  const jobs=elt('div',undefined,'panel');jobs.append(elt('h3','Job status'));
  Object.entries(dashboard.job_states).forEach(([state,n])=>jobs.append(elt('p',state+': '+n)));
  dashboard.recent_jobs.forEach(j=>jobs.append(elt('p',j.objective+' · '+j.mode+' · '+j.status+' · '+j.id)));
  root.append(jobs);
  const policy=elt('div',undefined,'panel');policy.append(elt('h3','Provider and permission policies'));
  dashboard.providers.forEach(p=>policy.append(elt('p',p.provider+': '+p.access_mode+' · calls disabled')));
  if(!dashboard.providers.length)policy.append(elt('p','No provider policies registered.','hint'));
  root.append(policy);
  const review=document.querySelector('#ops-reviews');review.replaceChildren();
  for(const p of reviews.gramps_change_plans)review.append(elt('p','Gramps research plan '+p.plan_id+' · '+p.status));
  for(const b of reviews.branch_revisions)review.append(elt('p','Provisional branch '+b.revision_id+' · '+b.status));
  if(!reviews.gramps_change_plans.length&&!reviews.branch_revisions.length)review.append(elt('p','No pending review entries in the bounded window.'));
}
document.querySelector('#ops-refresh').onclick=()=>loadOperations().catch(e=>notify(e.message,true));
document.querySelector('#ops-inspect').onclick=async()=>{try{
  const id=document.querySelector('#ops-job-id').value.trim();const data=await api('/ops/jobs/'+encodeURIComponent(id));
  document.querySelector('#ops-detail').textContent=JSON.stringify(data,null,2);
}catch(e){notify(e.message,true)}};

loadSummary().catch(e=>notify('Database not ready: '+e.message,true));
</script></body></html>'''


@router.get('/workspace',response_class=HTMLResponse)
def workspace(_:str=Depends(main.authenticate)):
    return HTMLResponse(HTML,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})
