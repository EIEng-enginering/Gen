'''Dedicated no-CDN acquisition workspace. Designed for local, authenticated use.'''
from fastapi import APIRouter,Depends
from fastapi.responses import HTMLResponse
from app import main
router=APIRouter()
HTML=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>24 Gen | Evidence Acquisition</title>
<style>
*{box-sizing:border-box}body{font:15px/1.45 system-ui,Segoe UI,sans-serif;color:#173040;background:#f3f7f9;margin:0}
header{background:#16405a;color:white;padding:20px max(18px,calc((100vw - 1130px)/2))}header a{color:#fff}
main{max-width:1130px;margin:24px auto;padding:0 15px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
section{background:white;border:1px solid #cfdce4;border-radius:10px;padding:19px;margin-bottom:16px}h1{margin:0;font-size:24px}h2{font-size:18px;margin:0 0 9px}
label{display:block;font-weight:600;margin:10px 0 4px}input,textarea,select,button{font:inherit}input,textarea,select{width:100%;border:1px solid #afc2cd;padding:9px;border-radius:6px}textarea{min-height:115px}button{border:0;border-radius:6px;padding:10px 15px;background:#165373;color:white;cursor:pointer;margin-top:10px}button:disabled{opacity:.6}button:focus,input:focus,textarea:focus{outline:3px solid #efac40}
pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow-y:auto;background:#edf3f6;border-radius:6px;padding:12px}.muted{color:#556c7a}.warning{color:#7c3415;font-weight:600}.item{border-top:1px solid #d8e4ea;padding:10px 0}.item button{margin:4px}.tiny{font-size:13px}
</style></head><body><header><h1>24 Gen | Evidence acquisition</h1><p>Offline-first intake · review before acceptance · never writes Gramps</p><a href="/workspace#ai-research">← Research workspace</a></header>
<main><section><p class="warning">Only use records you may lawfully retain. AI output, catalogue searches and source hints are unverified. Manual-only genealogy websites must not be scraped. Large imports require an approved/licensed dataset.</p><p class="muted">Record intake requires your local 24 Gen credentials. Incoming entries remain quarantined until individually reviewed against a real historical source.</p></section>
<div class="grid"><section><h2>1. Generate a prompt for any AI chatbot</h2>
<form id="promptform"><label>Surname<input name="surname" value="Oldham" required></label><label>County or historic area<input name="county" value="Cheshire" required></label>
<label>Start year<input name="year_start" type="number" value="1800" min="1500" max="2026"></label>
<label>End year<input name="year_end" type="number" value="1900" min="1500" max="2026"></label>
<label>Research mode<select name="mode"><option>guided</option><option>conventional</option><option>autonomous</option></select></label>
<button type="submit">Build source-controlled research prompt</button></form><label>Copy prompt into ChatGPT, Claude, Gemini, Grok or another chatbot</label><textarea id="promptout" rows="12" readonly></textarea><button type="button" id="copyprompt">Copy prompt</button><p class="muted tiny">Chatbot must return source-cited JSONL, never fabricated records. No external request is made by this page.</p></section>
<section><h2>2. Stage AI JSONL or permitted records</h2><p class="muted">Paste one JSON object per line from a chatbot or a permitted export. Maximum 100 records per request; use the streaming CLI for larger files.</p>
<label>Batch key<input id="batch-key" placeholder="cheshire-oldham-1800-1900-shard01"></label>
<label>Input type<select id="input-kind"><option value="ai_return">AI-produced JSONL</option><option value="manual">Individually researched records</option><option value="licensed_bulk">Licensed bulk extract</option><option value="user_export">Own exported records</option></select></label>
<label>JSONL<textarea id="jsonl" rows="11" spellcheck="false"></textarea></label><label><input id="rights" type="checkbox" style="width:auto"> I have checked rights to retain this material locally</label>
<button id="stage">Validate and stage (never auto-import)</button><pre id="staging-response"></pre></section></div>
<section><h2>3. Review staged records</h2><button id="refresh" type="button">Refresh batches</button><div id="batch-list"></div><div id="row-list"></div></section>
<section><h2>4. Sources and safe acquisition policy</h2><div id="policies"></div></section>
<div id="status" role="status" aria-live="polite"></div></main>
<script>
const base='/api/v1/research/acquisition';const $=s=>document.querySelector(s);
function txt(tag,value){const e=document.createElement(tag);e.textContent=String(value??'');return e}
async function call(path,method='GET',body){const x=await fetch(base+path,{method,headers:{'X-24Gen-Intent':'research','Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),credentials:'same-origin'});let d;try{d=await x.json()}catch{throw new Error('Server did not return JSON')};if(!x.ok)throw new Error(JSON.stringify(d).slice(0,1500));return d}
function fields(form){return Object.fromEntries(new FormData(form).entries())}
function notice(x){$('#status').textContent=x}
$('#promptform').onsubmit=async e=>{e.preventDefault();try{const b=fields(e.target);for(const key of ['year_start','year_end'])b[key]=Number(b[key]);const r=await call('/prompt','POST',b);$('#promptout').value=r.prompt;notice('Prompt prepared. No chatbot was contacted.')}catch(err){notice(err.message)}};
$('#copyprompt').onclick=()=>{const t=$('#promptout');t.select();navigator.clipboard?navigator.clipboard.writeText(t.value).then(()=>notice('Copied')).catch(()=>notice('Select prompt and copy manually.')):notice('Select prompt and copy manually.')};
$('#stage').onclick=async()=>{try{let lines=$('#jsonl').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);if(lines.length>100)throw Error('Use streaming CLI for more than 100 records');const records=lines.map(s=>JSON.parse(s));const r=await call('/batches','POST',{batch_key:$('#batch-key').value,records,input_kind:$('#input-kind').value,rights_attestation:$('#rights').checked});$('#staging-response').textContent=JSON.stringify(r,null,2);await loadBatches()}catch(err){$('#staging-response').textContent=err.message}};
async function loadBatches(){const rs=await call('/batches');const root=$('#batch-list');root.replaceChildren();for(const x of rs){const b=txt('button',x.batch_key+' | '+x.received+' rows');b.onclick=()=>loadRows(x.id,0).catch(e=>notice(e.message));root.append(b)}}
async function loadRows(id,offset){const rs=await call('/batches/'+id+'/rows?limit=25&offset='+offset),root=$('#row-list');root.replaceChildren();root.append(txt('h3','Batch '+id));for(const x of rs){const d=document.createElement('div');d.className='item';d.append(txt('p','Row '+x.row_number+' — '+x.status),txt('p',(x.payload.person_name_verbatim||'(catalogue lead)')+' | '+x.payload.source_reference),txt('p','Rights: '+x.payload.rights_note));const details=document.createElement('details');details.append(txt('summary','Full staged record'));details.append(txt('pre',JSON.stringify(x.payload,null,2)));d.append(details);if(!['imported','rejected'].includes(x.status)){const box=document.createElement('textarea');box.placeholder='Detailed source-check rationale (minimum 12 characters)';d.append(box);const checked=document.createElement('label');const cb=document.createElement('input');cb.type='checkbox';cb.style.width='auto';checked.append(cb,txt('span',' I independently checked the underlying original/source against this entry'));d.append(checked);for(const decision of ['import_verified','defer','reject']){const b=txt('button',decision);b.onclick=async()=>{if(decision==='import_verified' && !confirm('Are you certain the SOURCE and TRANSCRIPTION have been independently verified?'))return;try{const result=await call('/rows/'+x.id+'/review','POST',{decision,rationale:box.value,independently_checked:cb.checked});notice(JSON.stringify(result));await loadRows(id,offset)}catch(err){notice(err.message)}};d.append(b)}}root.append(d)}if(offset){const back=txt('button','Previous page');back.onclick=()=>loadRows(id,Math.max(0,offset-25));root.append(back)}if(rs.length===25){const next=txt('button','Next page');next.onclick=()=>loadRows(id,offset+25);root.append(next)}}
(async()=>{try{const p=await call('/provider-policies');const root=$('#policies');for(const [name,item] of Object.entries(p.policies)){const d=txt('p',name+': '+item.mode+'; bulk: '+item.bulk);root.append(d)}await loadBatches()}catch(err){notice(err.message)}})();
</script></body></html>'''
@router.get('/acquisition',response_class=HTMLResponse)
def acquisition_workspace(_:str=Depends(main.authenticate)):
    return HTMLResponse(HTML,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
     'Content-Security-Policy':"default-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})
