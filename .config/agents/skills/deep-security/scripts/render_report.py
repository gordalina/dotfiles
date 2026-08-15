#!/usr/bin/env python3
"""Render findings.json -> a single self-contained, modern report.html.

Design grounded in security-report UX research (2026): 3-layer information
architecture (Verdict → Themes+Charts → Finding detail), horizontal-bar charts
(donuts bury the few Criticals under the Low/Medium mass), the verification
funnel as the differentiator, and the Okabe-Ito colorblind-safe severity palette
with redundant shape icons. Inline SVG charts (no CDN/libs). Data is embedded as
a JSON island (`<script type="application/json" id="findings">`) so an LLM can
read the structured data from the HTML alone.
"""
import argparse, json, os


def load(path, default):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>deep-security report</title>
<style>
:root{
  --bg:#f6f7f9;--panel:#ffffff;--panel2:#fbfcfd;--ink:#16181d;--muted:#697586;--line:#e4e7ec;
  --accent:#3b5bdb;--chip:#eef1f5;--code:#f4f6f8;--shadow:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.04);
  /* Okabe-Ito, colorblind-safe + grayscale-distinct. Severity = luminance+icon+label, not hue alone. */
  --crit:#D55E00;--high:#E69F00;--med:#C8A200;--med-fill:#F0E442;--low:#3a8fd0;--low-fill:#56B4E9;--info:#8a909a;
  --pass:#2f9e44;--font:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace;
}
[data-theme=dark]{
  --bg:#0d0f14;--panel:#15181f;--panel2:#1a1e27;--ink:#e6e8ec;--muted:#9aa2af;--line:#262b36;
  --accent:#8aa0ff;--chip:#1f2430;--code:#0f1218;--shadow:none;--med:#F0E442;--low:#56B4E9;--info:#9aa2af;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);line-height:1.55;font-size:14px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1200px;margin:0 auto;padding:24px 22px 96px}
h1{font-size:19px;margin:0;letter-spacing:-.01em} h2{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:34px 0 12px}
.sub{color:var(--muted);font-size:12.5px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:var(--shadow)}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:18px}
.btn{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:6px 11px;font-size:12px;cursor:pointer;color:var(--ink);font-family:var(--font)}
.btn:hover{border-color:var(--accent)}

/* LAYER 1 — verdict */
.verdict-band{display:flex;gap:16px;align-items:stretch;flex-wrap:wrap}
.verdict-card{flex:1 1 340px;border-radius:14px;padding:18px 20px;border:1px solid var(--line);box-shadow:var(--shadow)}
.verdict-card.block{background:linear-gradient(135deg,rgba(213,94,0,.12),transparent);border-color:var(--crit)}
.verdict-card.caution{background:linear-gradient(135deg,rgba(230,159,0,.12),transparent);border-color:var(--high)}
.verdict-card.pass{background:linear-gradient(135deg,rgba(47,158,68,.12),transparent);border-color:var(--pass)}
.verdict-label{font-size:24px;font-weight:800;letter-spacing:-.01em;display:flex;align-items:center;gap:10px}
.verdict-card.block .verdict-label{color:var(--crit)} .verdict-card.caution .verdict-label{color:var(--high)} .verdict-card.pass .verdict-label{color:var(--pass)}
.verdict-why{margin-top:8px;font-size:13.5px}
.headline{margin-top:10px;color:var(--muted);font-size:13px}

/* KPI tiles */
.tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:16px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 12px;cursor:pointer;transition:.12s;box-shadow:var(--shadow);position:relative}
.tile:hover{transform:translateY(-2px)} .tile.active{outline:2px solid var(--accent);outline-offset:-1px}
.tile .ic{font-size:13px;opacity:.85}.tile .n{font-size:30px;font-weight:800;line-height:1.05;letter-spacing:-.02em}
.tile .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-top:2px;font-weight:600}
.tile .q{font-size:10.5px;color:var(--muted);margin-top:3px}
.tile.Critical .n{color:var(--crit)}.tile.High .n{color:var(--high)}.tile.Medium .n{color:var(--med)}.tile.Low .n{color:var(--low)}.tile.Info .n{color:var(--info)}

/* badges & chips */
.badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;white-space:nowrap}
.sev-Critical{background:var(--crit);color:#fff}.sev-High{background:var(--high);color:#fff}.sev-Medium{background:var(--med-fill);color:#3a2e00}.sev-Low{background:var(--low-fill);color:#08263a}.sev-Info{background:var(--info);color:#fff}
.tag{background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:1px 7px;font-size:10.5px;color:var(--muted);white-space:nowrap}
.tag.ok{color:var(--pass);border-color:var(--pass)} .tag.warn{color:var(--high);border-color:var(--high)}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer;user-select:none}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}

/* charts */
.charts{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.charts .full{grid-column:1/-1}
figure{margin:0}figcaption{font-size:12px;font-weight:600;color:var(--ink);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
figcaption .hint{font-weight:400;color:var(--muted);font-size:11px}
.svg-wrap{width:100%}.svg-wrap svg{width:100%;height:auto;display:block}
.barlabel{fill:var(--ink);font-size:11px}.barval{fill:var(--ink);font-size:11px;font-weight:700}.axis{fill:var(--muted);font-size:10px}

/* themes / highlights */
.themes{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.theme{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:10px;padding:11px 13px;font-size:13px}
.theme .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700;margin-bottom:3px}

/* meta details */
details.meta{margin-top:14px}
details.meta>summary{cursor:pointer;font-size:12px;font-weight:600;color:var(--muted);padding:6px 0;list-style:none}
details.meta>summary::-webkit-details-marker{display:none}
details.meta>summary::before{content:"▸ ";color:var(--accent)} details.meta[open]>summary::before{content:"▾ "}
.metagrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:10px}
.metagrid .big{font-size:20px;font-weight:800} .metagrid ul{margin:4px 0;padding-left:16px} .metagrid li{margin:2px 0;font-size:12.5px}
.skip{color:var(--high)}

/* findings */
.filterbar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input[type=search]{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 12px;color:var(--ink);font-family:var(--font);min-width:240px;font-size:13px}
table{width:100%;border-collapse:collapse;table-layout:fixed}
thead th{position:sticky;top:54px;background:var(--panel);z-index:4}
th,td{text-align:left;padding:10px 10px;border-bottom:1px solid var(--line);vertical-align:top;font-size:13px;overflow-wrap:anywhere}
th{color:var(--muted);font-size:10.5px;text-transform:uppercase;letter-spacing:.05em}
th button{all:unset;cursor:pointer;font:inherit;color:inherit;text-transform:inherit;letter-spacing:inherit}
th:nth-child(1),td:nth-child(1){width:11%}
th:nth-child(2),td:nth-child(2){width:30%}
th:nth-child(3),td:nth-child(3){width:14%}
th:nth-child(4),td:nth-child(4){width:13%}
th:nth-child(5),td:nth-child(5){width:10%}
th:nth-child(6),td:nth-child(6){width:22%}
tr.f{cursor:pointer}tr.f:hover{background:var(--chip)}
.detail{display:none}.detail.open{display:table-row}.detail td{background:var(--code)}
.kvs{display:grid;grid-template-columns:118px 1fr;gap:6px 14px;margin:4px 0}
.kvs div:nth-child(odd){color:var(--muted);font-size:12px}
pre{background:var(--code);border:1px solid var(--line);border-radius:8px;padding:11px;overflow:auto;font-family:var(--mono);font-size:12.5px;margin:8px 0}
a.loc{font-family:var(--mono);font-size:12px;color:var(--accent);text-decoration:none}a.loc:hover{text-decoration:underline}
button.cp{background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:3px 9px;font-size:11px;cursor:pointer;color:var(--ink)}
.muted{color:var(--muted)}.small{font-size:12px}.empty{padding:16px;text-align:center;color:var(--muted)}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}

@media (max-width:860px){.tiles{grid-template-columns:repeat(2,1fr)}.charts,.themes{grid-template-columns:1fr}.metagrid{grid-template-columns:1fr}}
@media print{
  :root{--bg:#fff;--ink:#000;--panel:#fff}
  .filterbar,.btn,.chip,#tool-chips,button.cp{display:none!important}
  .panel,figure,tr,.theme,.tile{break-inside:avoid}
  thead{display:table-header-group}
  .badge,.tile,thead th,.verdict-card{print-color-adjust:exact;-webkit-print-color-adjust:exact}
  a[href^="http"]::after,a.loc::after{content:" (" attr(href) ")";font-size:9px;color:#555}
}
</style></head>
<body>
<div class="wrap">
  <div class="topbar">
    <div><h1>deep-security report</h1><div class="sub" id="hdr"></div></div>
    <div class="row"><button class="btn" id="ed-toggle"></button><button class="btn" id="theme-toggle">◐ theme</button><button class="btn" onclick="window.print()">⎙ print</button></div>
  </div>

  <!-- LAYER 1: VERDICT -->
  <div class="verdict-band" id="verdict-band"></div>
  <div class="tiles" id="tiles"></div>

  <!-- LAYER 2: CHARTS + THEMES -->
  <h2>At a glance</h2>
  <div class="charts">
    <figure class="panel" id="fig-sev"></figure>
    <figure class="panel" id="fig-funnel"></figure>
    <figure class="panel full" id="fig-owasp"></figure>
  </div>

  <h2 id="themes-h">Key themes <span class="hint sub" id="themes-scope"></span></h2>
  <div class="themes" id="themes"></div>

  <details class="meta"><summary>Run details — scanners, AI lenses, cost, timing, scope</summary>
    <div class="panel" id="meta-body" style="margin-top:8px"></div>
  </details>

  <!-- LAYER 3: FINDINGS -->
  <h2>Findings</h2>
  <div class="panel">
    <div class="filterbar">
      <input type="search" id="q" placeholder="search title, file, CWE, OWASP…" aria-label="search findings">
      <span class="chip" id="new-chip">new only</span>
      <span class="chip" id="dismissed-chip" style="display:none"></span>
      <span id="tool-chips" class="row"></span>
    </div>
    <table id="tbl"><caption class="sr-only">Findings. Click a column header to sort; click a row to expand details.</caption>
    <thead><tr>
      <th data-s="severity"><button>Severity</button></th>
      <th data-s="title"><button>Finding</button></th>
      <th data-s="status"><button>Status</button></th>
      <th data-s="owasp"><button>OWASP / CWE</button></th>
      <th data-s="confidence"><button>Source · Trust</button></th>
      <th data-s="file"><button>Location</button></th>
    </tr></thead><tbody id="rows"></tbody></table>
    <div id="empty" class="empty" style="display:none">No findings match the current filters.</div>
  </div>

  <h2>Methodology</h2>
  <div class="panel small muted" id="method"></div>
</div>

<script type="application/json" id="findings">__FINDINGS__</script>
<script type="application/json" id="meta">__META__</script>
<script type="application/json" id="owaspmap">__OWASPMAP__</script>
<script>
const F=JSON.parse(document.getElementById('findings').textContent);
const M=JSON.parse(document.getElementById('meta').textContent);
const OM=JSON.parse(document.getElementById('owaspmap').textContent);
const S=M.summary||{}, RS=M.run_summary||{};
const ORDER=["Critical","High","Medium","Low","Info"];
const SEV={Critical:{c:'#D55E00',ic:'⛔'},High:{c:'#E69F00',ic:'▲'},Medium:{c:'#F0E442',ic:'◆'},Low:{c:'#56B4E9',ic:'●'},Info:{c:'#999999',ic:'○'}};
let edition=(M.owasp_default==='2021')?'2021':'2025';
const editor=M.editor==='zed'?'zed':'vscode';
const root=(M.repo_root||'').replace(/\/$/,'');
const ACTIVE=F.filter(f=>!f.dismissed);
const DISMISSED_N=F.length-ACTIVE.length;
const state={sev:new Set(),tools:new Set(),newOnly:false,showDismissed:false,q:'',sortKey:'severity',sortDir:1};

function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function ocat(f){return edition==='2021'?(f.owasp_2021||'Unmapped'):(f.owasp_2025||'Unmapped');}
function absLink(f){const p=root?root+'/'+f.file:f.file;return editor==='zed'?`zed://file/${p}:${f.line}`:`vscode://file/${p}:${f.line||1}:1`;}
function statusOf(f){
  if(f.dismissed)return {t:'dismissed',cls:''};
  if(f.needs_review||f.triage==='context_dependent')return {t:'needs-review',cls:'warn'};
  if(f.source_kind==='both')return {t:'confirmed ⊕',cls:'ok'};
  if(f.triage==='confirmed')return {t:'confirmed',cls:'ok'};
  if(f.verified)return {t:'verified',cls:'ok'};
  if(f.triage==='adjust')return {t:'sev-adjusted',cls:''};
  return {t:'unverified',cls:''};
}

// ---------- inline SVG charts (no libs) ----------
function hbars(data,opts){ // data:[{label,value,color}]  horizontal bars, value labels outside
  opts=opts||{}; const W=opts.w||520, rh=opts.rh||26, gut=opts.gut||150, pad=10;
  const max=Math.max(1,...data.map(d=>d.value)); const H=data.length*rh+pad;
  const inner=W-gut-46;
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria||'bar chart')}">`;
  data.forEach((d,i)=>{const y=i*rh+pad/2; const bw=Math.max(d.value>0?3:0,(d.value/max)*inner);
    s+=`<text class="barlabel" x="${gut-8}" y="${y+rh/2}" text-anchor="end" dominant-baseline="middle">${esc(d.label)}</text>`;
    s+=`<rect x="${gut}" y="${y+4}" width="${bw}" height="${rh-10}" rx="3" fill="${d.color||'var(--accent)'}"><title>${esc(d.label)}: ${d.value}</title></rect>`;
    s+=`<text class="barval" x="${gut+bw+6}" y="${y+rh/2}" dominant-baseline="middle">${d.value}</text>`;});
  return s+`</svg>`;
}
function renderSevChart(){
  const c={}; ORDER.forEach(l=>c[l]=0); ACTIVE.forEach(f=>c[f.severity]=(c[f.severity]||0)+1);
  const data=ORDER.map(l=>({label:`${SEV[l].ic} ${l}`,value:c[l]||0,color:SEV[l].c}));
  document.getElementById('fig-sev').innerHTML=
    `<figcaption>Severity distribution <span class="hint">active findings (post-triage)</span></figcaption>`+
    `<div class="svg-wrap">${hbars(data,{aria:'severity distribution'})}</div>`;
}
function renderOwaspChart(){
  const c={}; ACTIVE.forEach(f=>{const k=ocat(f);c[k]=(c[k]||0)+1;});
  let arr=Object.entries(c).sort((a,b)=>b[1]-a[1]).slice(0,10);
  const data=arr.map(([k,v])=>({label:k.replace(/:20\d\d/,''),value:v,color:'var(--accent)'}));
  document.getElementById('fig-owasp').innerHTML=
    `<figcaption>OWASP ${edition} categories <span class="hint">top ${data.length} by count · click bar to filter</span></figcaption>`+
    `<div class="svg-wrap">${hbars(data,{w:1040,gut:300,aria:'owasp categories'})}</div>`;
  // click-to-filter
  const cats=arr.map(x=>x[0]);
  document.querySelectorAll('#fig-owasp rect').forEach((r,i)=>{r.style.cursor='pointer';r.onclick=()=>{state.q=cats[i];document.getElementById('q').value=cats[i];renderRows();document.getElementById('q').scrollIntoView({block:'center'});};});
}
function renderFunnel(){
  const total=F.length, active=ACTIVE.length, verified=F.filter(f=>f.verified).length;
  const steps=[{label:'All findings',value:total,color:'var(--info)'},
               {label:'Active (noise removed)',value:active,color:'var(--low-fill)'},
               {label:'Verified / confirmed',value:verified,color:'var(--pass)'}];
  document.getElementById('fig-funnel').innerHTML=
    `<figcaption>Verification funnel <span class="hint">adversarial + rule-class triage</span></figcaption>`+
    `<div class="svg-wrap">${hbars(steps,{aria:'verification funnel'})}</div>`+
    `<div class="sub small" style="margin-top:8px">${DISMISSED_N} dismissed as noise/not-applicable · ${(S.needs_review_count||0)} need review · `+
    `${RS.funnel?`agent pass: ${RS.funnel.candidates}→${RS.funnel.verified} (${RS.funnel.refuted} refuted)`:''}</div>`;
}

// ---------- layer 1 ----------
function renderVerdict(){
  const v=S.verdict||'pass'; const vt={block:'BLOCK',caution:'CAUTION',pass:'PASS'}[v]||v.toUpperCase();
  const vic={block:'⛔',caution:'▲',pass:'✓'}[v]||'';
  document.getElementById('verdict-band').innerHTML=
    `<div class="verdict-card ${v}"><div class="verdict-label">${vic} ${vt}</div>`+
    `<div class="verdict-why">${esc(S.verdict_rationale||'')}</div>`+
    `<div class="headline">${esc(S.headline||'')}</div></div>`;
}
function renderTiles(){
  const c={}; ORDER.forEach(l=>c[l]=0); ACTIVE.forEach(f=>c[f.severity]=(c[f.severity]||0)+1);
  const verifiedBySev=l=>ACTIVE.filter(f=>f.severity===l&&f.verified).length;
  document.getElementById('tiles').innerHTML=ORDER.map(l=>{
    const q=l==='Critical'||l==='High'?`${verifiedBySev(l)} verified`:(l==='Info'?'':`${verifiedBySev(l)} verified`);
    return `<div class="tile ${l} ${state.sev.has(l)?'active':''}" data-sev="${l}" role="button" tabindex="0">`+
      `<div class="ic" style="color:${SEV[l].c}">${SEV[l].ic}</div><div class="n">${c[l]||0}</div>`+
      `<div class="l">${l}</div>${q?`<div class="q">${q}</div>`:''}</div>`;}).join('');
  document.querySelectorAll('.tile').forEach(t=>{const f=()=>{const l=t.dataset.sev;state.sev.has(l)?state.sev.delete(l):state.sev.add(l);renderTiles();renderRows();document.getElementById('rows').scrollIntoView({block:'start',behavior:'smooth'});};t.onclick=f;t.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();f();}};});
}

// ---------- layer 2 themes ----------
function renderThemes(){
  const ai=S.ai_highlights||{}; const themes=ai.themes||S.top_themes||[];
  document.getElementById('themes-scope').textContent=themes.length?`· ${ai.scope||'from analysis'}`:'';
  const notable=(S.notable||[]).filter(n=>n.severity==='Critical'||n.severity==='High').slice(0,4);
  let html='';
  if(notable.length) html+=notable.map(n=>
    `<div class="theme"><div class="k">${esc(n.severity)}${n.verified?' · verified':''}</div>${esc(n.title)}<div class="sub small" style="margin-top:4px">${esc((n.tool||[]).join(', '))} · ${esc(n.file||'')}:${n.line||''}</div></div>`).join('');
  html+=themes.map(t=>`<div class="theme"><div class="k">theme</div>${esc(t)}</div>`).join('');
  document.getElementById('themes').innerHTML=html||'<div class="theme muted">No high-severity themes.</div>';
}

// ---------- meta ----------
function renderMeta(){
  const tr=(M.tools_run||[]).map(t=>`<li>✓ <b>${esc(t.name)}</b> ${esc(t.version||'')}</li>`).join('');
  const sk=(M.skipped||[]).map(t=>`<li class="skip">• <b>${esc(t.name||t.tool)}</b> — ${esc(t.install||'not run')}</li>`).join('');
  const lenses=(M.lenses||[]).map(l=>`<li>◆ ${esc(l)}</li>`).join('');
  const ph=(RS.phases||[]).map(p=>`${esc(p.name)} ${esc(p.duration)}`).join(' · ');
  const cs=Object.entries(RS.cost_by_stage||{}).map(([k,v])=>`${esc(k)} $${v}`).join(' · ');
  document.getElementById('meta-body').innerHTML=`<div class="metagrid">`+
    `<div><div class="muted small">Cost (est)</div><div class="big">$${RS.cost_usd??'—'}</div><div class="sub small">${(RS.total_tokens||0).toLocaleString()} tokens${cs?'<br>'+cs:''}</div></div>`+
    `<div><div class="muted small">Wall-clock</div><div class="big">${esc(RS.wall_clock||'—')}</div><div class="sub small">${ph}</div></div>`+
    `<div><div class="muted small">Scope</div><div class="sub small">${esc(M.scope||'')}<br>${esc(M.files_scanned||'')}<br>Verification: ${esc(M.verification||'adversarial + triage')}</div></div>`+
    `</div><div class="metagrid" style="margin-top:14px">`+
    `<div><div class="muted small">Scanners</div><ul>${tr||'<li class="muted">none</li>'}${sk}</ul></div>`+
    `<div><div class="muted small">AI lenses</div><ul>${lenses||'<li class="muted">none</li>'}</ul></div>`+
    `<div><div class="muted small">Run</div><div class="sub small">${esc(M.git_sha||'')} · ${esc(M.generated_at||'')} · mode ${esc(M.mode||'')}</div></div></div>`;
}

// ---------- layer 3 findings ----------
function renderToolChips(){
  const tools=new Set(); ACTIVE.forEach(f=>(f.tool||[]).forEach(t=>tools.add(t)));
  document.getElementById('tool-chips').innerHTML=[...tools].sort().map(t=>`<span class="chip ${state.tools.has(t)?'on':''}" data-tool="${esc(t)}">${esc(t)}</span>`).join('');
  document.querySelectorAll('[data-tool]').forEach(c=>c.onclick=()=>{const t=c.dataset.tool;state.tools.has(t)?state.tools.delete(t):state.tools.add(t);renderToolChips();renderRows();});
}
function visible(){
  let r=(state.showDismissed?F:ACTIVE).slice();
  if(state.sev.size)r=r.filter(f=>state.sev.has(f.severity));
  if(state.tools.size)r=r.filter(f=>(f.tool||[]).some(t=>state.tools.has(t)));
  if(state.newOnly)r=r.filter(f=>f.is_new);
  if(state.q){const q=state.q.toLowerCase();r=r.filter(f=>JSON.stringify([f.title,f.file,f.cwe,f.description,ocat(f),f.owasp_llm]).toLowerCase().includes(q));}
  const k=state.sortKey;
  r.sort((a,b)=>{let av,bv;
    if(k==='severity'){av=ORDER.indexOf(a.severity);bv=ORDER.indexOf(b.severity);}
    else if(k==='owasp'){av=ocat(a);bv=ocat(b);} else if(k==='status'){av=statusOf(a).t;bv=statusOf(b).t;}
    else{av=a[k];bv=b[k];}
    return (av>bv?1:av<bv?-1:0)*state.sortDir;});
  return r;
}
function renderRows(){
  const rows=visible();
  document.getElementById('empty').style.display=rows.length?'none':'block';
  document.getElementById('rows').innerHTML=rows.map((f,i)=>{
    const st=statusOf(f); const prov=(f.tool||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join(' ');
    const trust=`${f.confidence??'—'}/10`;
    return `<tr class="f" data-i="${i}">
      <td><span class="badge sev-${f.severity}">${SEV[f.severity]?SEV[f.severity].ic:''} ${f.severity}</span></td>
      <td>${esc(f.title)}</td>
      <td><span class="tag ${st.cls}">${esc(st.t)}</span>${f.is_new?' <span class="tag">new</span>':''}</td>
      <td class="small">${esc(ocat(f))}${f.owasp_llm?`<br><span class="tag">${esc(f.owasp_llm.split('-')[0])}</span>`:''}<br><span class="muted">${esc(f.cwe||'')}</span></td>
      <td class="small">${prov}<br><span class="muted">trust ${trust}</span></td>
      <td><a class="loc" href="${absLink(f)}">${esc(f.file)}:${f.line}</a></td>
    </tr>
    <tr class="detail" id="d${i}"><td colspan="6">${detail(f)}</td></tr>`;}).join('');
  document.querySelectorAll('tr.f').forEach(tr=>tr.onclick=e=>{if(e.target.tagName==='A'||e.target.tagName==='BUTTON')return;document.getElementById('d'+tr.dataset.i).classList.toggle('open');});
  document.querySelectorAll('button.cp').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(b.dataset.copy);const o=b.textContent;b.textContent='copied';setTimeout(()=>b.textContent=o,1200);});
}
function detail(f){
  const fix=`Fix this ${f.severity} security finding (${f.cwe||''} / ${ocat(f)}${f.owasp_llm?' / '+f.owasp_llm:''}) at ${f.file}:${f.line}: ${f.title}. ${f.description||''} Suggested remediation: ${f.remediation||''}`;
  return `<div class="kvs">
    <div>Why it matters</div><div>${esc(f.description||'')}</div>
    <div>Remediation</div><div>${esc(f.remediation||'—')}</div>
    <div>Evidence</div><div>${esc((f.tool||[]).join(', '))} (${esc(f.source_kind||'')}) · trust ${f.confidence??'—'}/10${f.verification_note?` — ${esc(f.verification_note)}`:''}${f.triage_note?` — ${esc(f.triage_note)}`:''}</div>
    <div>Classification</div><div>${esc(ocat(f))}${f.owasp_llm?` · <b>${esc(f.owasp_llm)}</b>`:''} · CWE ${esc(f.cwe||'—')}${f.cvss_from_advisory?` · CVSS ${f.cvss_from_advisory} (advisory)`:''}</div>
    <div>Location</div><div><a class="loc" href="${absLink(f)}">${esc(f.file)}:${f.line}</a></div>
  </div><div class="row"><button class="cp" data-copy="${esc(f.file)}:${f.line}">copy file:line</button><button class="cp" data-copy="${esc(fix)}">copy fix-prompt</button></div>`;
}

function renderAll(){renderVerdict();renderTiles();renderSevChart();renderFunnel();renderOwaspChart();renderThemes();renderMeta();renderToolChips();renderRows();
  document.getElementById('hdr').textContent=`${M.repo||'repo'} · ${M.mode||''} · ${M.scope||''} · ${M.git_sha||''} · ${M.generated_at||''}`;
  document.getElementById('ed-toggle').textContent=`OWASP ${edition} ▸ ${edition==='2025'?'2021':'2025'}`;
  document.getElementById('method').innerHTML=`Hybrid review: FOSS scanners + parallel AI lens agents across the OWASP web + LLM Top 10, every finding adversarially verified (agents) or rule-class triaged (scanners). Severity is an editorial 5-level scale (not CVSS; CVSS shown only when passed through from an advisory). OWASP categories derived from CWE (edition ${edition}${edition==='2025'?' — RC1':''}). Severity palette is Okabe-Ito (colorblind-safe) with redundant shape icons. <b>AI-assisted findings are advisory — verify before acting.</b>`;
}
// controls
document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value;renderRows();});
document.getElementById('new-chip').onclick=function(){state.newOnly=!state.newOnly;this.classList.toggle('on',state.newOnly);renderRows();};
(function(){const dc=document.getElementById('dismissed-chip');if(DISMISSED_N>0){dc.style.display='inline-block';dc.textContent=`show dismissed (${DISMISSED_N})`;dc.onclick=function(){state.showDismissed=!state.showDismissed;this.classList.toggle('on',state.showDismissed);renderRows();};}})();
document.getElementById('ed-toggle').onclick=()=>{edition=edition==='2025'?'2021':'2025';renderAll();};
document.querySelectorAll('th[data-s]').forEach(th=>th.onclick=()=>{const k=th.dataset.s;if(state.sortKey===k)state.sortDir*=-1;else{state.sortKey=k;state.sortDir=1;}document.querySelectorAll('th[data-s]').forEach(x=>x.removeAttribute('aria-sort'));th.setAttribute('aria-sort',state.sortDir>0?'ascending':'descending');renderRows();});
document.getElementById('theme-toggle').onclick=()=>{const d=document.documentElement;d.dataset.theme=d.dataset.theme==='dark'?'':'dark';};
if(matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches)document.documentElement.dataset.theme='dark';
if(M.mode==='full')document.getElementById('new-chip').style.display='none';
window.addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>d.open=true));
renderAll();
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--owasp-map", required=True)
    ap.add_argument("--owasp-default", default="2025")
    ap.add_argument("--editor", default="vscode")
    ap.add_argument("--skipped")
    ap.add_argument("--meta")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    findings = load(a.findings, [])
    omap = load(a.owasp_map, {"categories": {"2021": {}, "2025": {}}})
    meta = load(a.meta, {})
    meta.setdefault("owasp_default", a.owasp_default)
    meta.setdefault("editor", a.editor)
    meta.setdefault("repo_root", os.getcwd())
    meta["skipped"] = load(a.skipped, meta.get("skipped", []))

    htmlout = (TEMPLATE
               .replace("__FINDINGS__", json.dumps(findings))
               .replace("__META__", json.dumps(meta))
               .replace("__OWASPMAP__", json.dumps(omap)))
    with open(a.out, "w") as f:
        f.write(htmlout)
    print(f"wrote report -> {a.out} ({len(findings)} findings)")


if __name__ == "__main__":
    main()
