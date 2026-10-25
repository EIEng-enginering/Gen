"""No external scripts or HTML injection from genealogy data."""
from fastapi import APIRouter,Depends
from fastapi.responses import HTMLResponse
from app import main
router=APIRouter(dependencies=[Depends(main.authenticate)])
HTML='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>24 Gen — General Record Search</title>
<style>
:root{font:16px system-ui,Segoe UI,Arial,sans-serif;color:#203246;background:#eef3f7}
body{margin:0}header{background:#153958;color:white;padding:1.4rem clamp(1rem,4vw,4rem)}main{max-width:1200px;margin:1rem auto;padding:0 1rem}
article{background:white;border:1px solid #cbd8e3;border-radius:12px;margin:1rem 0;padding:1.2rem}
form{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:1rem}
label{font-weight:650;display:grid;gap:.4rem}input,select,button{font:inherit;padding:.5rem;border:1px solid #9cadbe;border-radius:6px;max-width:100%;min-width:0}
button{background:#145b8e;color:white;cursor:pointer}button:focus,a:focus{outline:3px solid #eaad29;outline-offset:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem}
.results{list-style:none;padding:0}.results>li{padding:.85rem 0;border-top:1px solid #dce5ed}
small,.muted{color:#476077}.warning{background:#fff7e5;border-left:4px solid #ba7b18;padding:.75rem}
.item-header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.7rem}
#correlations{max-height:600px;overflow:auto;white-space:normal}pre{white-space:pre-wrap;word-break:break-word}
@media(max-width:550px){header{padding:1rem}h1{font-size:1.5rem}}
</style></head><body><header><h1>24 Gen — General Historical Record Search</h1><p>Local, source-aware research • unverified records remain leads • Gramps is read-only</p></header>
<main><article><p><a href="/workspace">Back to Research Workspace</a> · <a href="/acquisition">Evidence intake</a> · <a href="/">Home</a></p>
<form id="search"><label>Surname / variants separated by |<input name="surname" minlength="2" maxlength="120" placeholder="Smith | Smyth"></label>
<label>Given names to compare (does not filter results)<input name="given" maxlength="120" placeholder="Elizabeth"></label>
<label>Historical county (optional)<input name="county" maxlength="100" placeholder="Cheshire"></label>
<label>Year from<input name="year_from" type="number" min="1500" max="2026"></label>
<label>Year to<input name="year_to" type="number" min="1500" max="2026"></label>
<label>Record class<input name="record_type" maxlength="60" placeholder="census"></label>
<label>Name matching<select name="mode"><option value="exact">Literal/declared variants</option><option value="phonetic">Phonetic retrieval (review)</option><option value="prefix">Prefix retrieval</option></select></label>
<label>Record status<select name="include_staged"><option value="true">Reviewed + staged leads</option><option value="false">Reviewed evidence only</option></select></label>
<button type="submit">Search local records</button></form>
<p class="warning">Records in this view are not genealogical proof. No remote provider is queried. Similar names do not confirm identity.</p>
<p id="status" aria-live="polite"></p></article>
<div class="grid"><article><h2>Search results</h2><ul class="results" id="results"></ul><button id="more" type="button" hidden>More results</button></article>
<article><h2>Possible identity correlations</h2><div id="correlations" aria-live="polite" class="muted">Choose “Compare” next to a result. An unknown/unmatched person remains possible.</div></article></div>
</main><script>
const root='/api/v1/research/general/';let next=null,query=null;
function node(tag,t,cls){const x=document.createElement(tag);if(t!==undefined)x.textContent=String(t);if(cls)x.className=cls;return x}
async function api(path){const r=await fetch(root+path,{credentials:'same-origin'});const v=await r.json();if(!r.ok)throw new Error(typeof v.detail==='string'?v.detail:'Request failed');return v}
function params(o){const p=new URLSearchParams();Object.entries(o).forEach(([k,v])=>{if(v!==''&&v!=null)p.set(k,v)});return p.toString()}
function clear(el){el.replaceChildren()}
function showResults(data,append){const el=document.querySelector('#results');if(!append)clear(el);
  for(const r of data.results){const li=node('li');const hd=node('div',undefined,'item-header');hd.append(node('strong',r.name_literal||'(name not present)'));
    const b=node('button','Compare');b.type='button';b.onclick=()=>compare(r.id).catch(err=>message(err.message,true));hd.append(b);li.append(hd);
    li.append(node('p',[r.event_type,r.year??'date uncertain',r.place_literal||'place unspecified'].join(' · ')));
    li.append(node('small',r.provider+' · '+r.source_reference+' · '+r.status+' · '+r.rights_label));
    li.append(node('p','Potential original group: '+(r.possible_original_group||'unknown')+'; '+(r.source_checked?'Source check recorded':'Source check not established in this index'),'muted'));
    el.append(li)}next=data.next_cursor;document.querySelector('#more').hidden=!next;
  message((append?'Additional':'Local')+' records: '+data.results.length+'. Only the indexed local corpus was searched.');}
function message(m,error=false){const e=document.querySelector('#status');e.textContent=m;e.style.color=error?'#9d2c2c':'#204b6e'}
async function compare(id){const v=await api('mentions/'+encodeURIComponent(id)+'/correlations');const el=document.querySelector('#correlations');clear(el);
  el.append(node('p','Unknown/unmatched alternative: available. No calibrated identity probability.','warning'));
  if(!v.candidates.length)el.append(node('p','No candidate found in the bounded local index. This is not evidence that a person is absent.'));
  for(const c of v.candidates){const section=node('section');section.append(node('h3',c.record.name_literal+' · '+(c.record.year??'unknown year')));
    section.append(node('p','Retrieval score '+c.comparison.ranking_score+' — NOT a probability.'));
    section.append(node('p','Support: '+(c.comparison.supports.join('; ')||'None recorded')));
    section.append(node('p','Conflicts/cautions: '+(c.comparison.conflicts.join('; ')||'None identified by current features')));
    section.append(node('small',c.record.source_reference));el.append(section)}
}
document.querySelector('#search').addEventListener('submit',async e=>{e.preventDefault();const f=Object.fromEntries(new FormData(e.target));query=f;try{const v=await api('search?'+params({...f,limit:30}));showResults(v,false)}catch(error){message(error.message,true)}});
document.querySelector('#more').onclick=async()=>{if(!next)return;try{showResults(await api('search?'+params({...query,cursor:next,limit:30})),true)}catch(e){message(e.message,true)}};
</script></body></html>'''

@router.get('/general-search',response_class=HTMLResponse)
def page():
    return HTMLResponse(HTML,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
      'Content-Security-Policy':"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})
