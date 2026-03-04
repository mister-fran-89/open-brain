import os
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

BRAIN_URL = os.getenv("BRAIN_URL", "http://open-brain:8000")
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:8000")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

app = FastAPI()

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Mr.Fran</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #1c1c1e;
      --surface:  #2c2c2e;
      --surface2: #3a3a3c;
      --border:   #3a3a3c;
      --text:     #f5f5f7;
      --muted:    #8e8e93;
      --accent:   #e86826;
      --green:    #32d74b;
      --red:      #ff453a;
      --r:        10px;
      --font:     -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
      --mono:     'SF Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    }

    html { background: var(--bg); }

    body {
      font-family: var(--font);
      font-size: 16px;
      line-height: 1.5;
      color: var(--text);
      background: var(--bg);
      max-width: 680px;
      margin: 0 auto;
      padding: 28px 20px env(safe-area-inset-bottom, 24px);
      -webkit-font-smoothing: antialiased;
    }

    /* ── Header ─────────────────────────────── */
    .hdr { margin-bottom: 30px; display: flex; align-items: baseline; gap: 10px; }

    .hdr h1 {
      font-family: var(--mono);
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.01em;
    }

    .hdr .sub {
      font-family: var(--mono);
      font-size: 0.75rem;
      color: var(--muted);
      letter-spacing: 0.04em;
      
    }

    /* ── Tabs ────────────────────────────────── */
    .tabs {
      display: flex;
      border-bottom: 1px solid var(--border);
      margin-bottom: 28px;
    }

    .tab {
      font-family: var(--mono);
      font-size: 0.82rem;
      letter-spacing: 0.04em;
      color: var(--muted);
      background: none;
      border: none;
      padding: 9px 16px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
      transition: color .15s, border-color .15s;
    }

    .tab.active  { color: var(--accent); border-bottom-color: var(--accent); }
    .tab:hover:not(.active) { color: var(--text); }

    /* ── Panels ──────────────────────────────── */
    .panel { display: none; }
    .panel.active { display: block; }

    /* ── Label ───────────────────────────────── */
    .lbl {
      font-family: var(--mono);
      font-size: 0.72rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.09em;
      margin-bottom: 10px;
    }

    /* ── Terminal prompt ─────────────────────── */
    .prompt {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 14px 16px;
      transition: border-color .15s;
    }

    .prompt:focus-within { border-color: var(--accent); }

    .prompt-chr {
      font-family: var(--mono);
      font-size: 1rem;
      color: var(--accent);
      line-height: 1.6;
      user-select: none;
      flex-shrink: 0;
      padding-top: 1px;
    }

    .prompt textarea,
    .prompt input[type=text] {
      background: transparent;
      border: none;
      outline: none;
      color: var(--text);
      font-size: 1rem;
      line-height: 1.6;
      width: 100%;
      resize: none;
      overflow-y: hidden;
      font-family: var(--font);
      caret-color: var(--accent);
    }

    .prompt textarea::placeholder,
    .prompt input[type=text]::placeholder { color: var(--muted); }

    /* ── Buttons ─────────────────────────────── */
    .btn {
      font-family: var(--mono);
      font-size: 0.84rem;
      letter-spacing: 0.04em;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 10px 22px;
      border-radius: var(--r);
      cursor: pointer;
      transition: border-color .15s, color .15s, background .15s;
      white-space: nowrap;
    }

    .btn-accent { border-color: var(--accent); color: var(--accent); }
    .btn-accent:hover { background: rgba(232,104,38,.1); }
    .btn:not(.btn-accent):hover { border-color: var(--accent); color: var(--accent); }
    .btn:active { opacity: .7; }

    /* ── Confirmation card ───────────────────── */
    @keyframes slideUp {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .confirm {
      display: none;
      align-items: flex-start;
      gap: 12px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 3px solid var(--green);
      border-radius: var(--r);
      padding: 14px 16px;
      margin-top: 16px;
      animation: slideUp .2s ease;
    }
    .confirm.show { display: flex; }

    .confirm-chk { font-family: var(--mono); color: var(--green); flex-shrink: 0; margin-top: 1px; }

    .confirm-title { font-size: 0.9rem; color: var(--text); margin-bottom: 7px; }
    .confirm-title strong { color: var(--accent); }

    .confirm-meta {
      font-family: var(--mono);
      font-size: 0.76rem;
      color: var(--muted);
      line-height: 1.9;
    }
    .confirm-meta span { color: var(--text); }

    /* ── Error card ──────────────────────────── */
    .err {
      display: none;
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 3px solid var(--red);
      border-radius: var(--r);
      padding: 14px 16px;
      margin-top: 16px;
      font-family: var(--mono);
      font-size: 0.8rem;
      color: var(--red);
      animation: slideUp .2s ease;
    }
    .err.show { display: block; }

    /* ── Loading ─────────────────────────────── */
    .loading {
      font-family: var(--mono);
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 18px;
      animation: pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.3; } }

    /* ── Result cards ────────────────────────── */
    .r-area { margin-top: 20px; }

    .r-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 14px 16px;
      margin-bottom: 10px;
      animation: slideUp .2s ease;
    }

    .r-meta {
      font-family: var(--mono);
      font-size: 0.71rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 4px;
    }

    .r-title { font-size: 0.95rem; font-weight: 600; margin-bottom: 5px; }
    .r-body  { font-size: 0.85rem; color: var(--muted); line-height: 1.55; }

    .tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 9px; }
    .tag {
      font-family: var(--mono);
      font-size: 0.71rem;
      color: var(--muted);
      background: var(--surface2);
      border-radius: 4px;
      padding: 2px 8px;
    }

    /* ── Answer ──────────────────────────────── */
    .answer {
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 3px solid var(--accent);
      border-radius: var(--r);
      padding: 16px;
      font-size: 0.92rem;
      line-height: 1.75;
      animation: slideUp .2s ease;
    }

    .src-row {
      font-family: var(--mono);
      font-size: 0.73rem;
      color: var(--muted);
      margin-top: 10px;
    }

    /* ── Search filters ──────────────────────── */
    .filter-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; align-items: center; }

    select {
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--mono);
      font-size: 0.8rem;
      padding: 9px 12px;
      border-radius: var(--r);
      outline: none;
      cursor: pointer;
      -webkit-appearance: none;
      appearance: none;
    }
    select:focus { border-color: var(--accent); }

    .tag-input {
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--mono);
      font-size: 0.8rem;
      padding: 9px 12px;
      border-radius: var(--r);
      outline: none;
      width: 130px;
    }
    .tag-input::placeholder { color: var(--muted); }
    .tag-input:focus { border-color: var(--accent); }

    /* ── Period pills ────────────────────────── */
    .pills { display: flex; gap: 8px; margin-bottom: 18px; }

    .pill {
      font-family: var(--mono);
      font-size: 0.8rem;
      padding: 8px 18px;
      border-radius: 20px;
      border: 1px solid var(--border);
      color: var(--muted);
      cursor: pointer;
      background: none;
      transition: all .15s;
    }
    .pill.on { border-color: var(--accent); color: var(--accent); background: rgba(232,104,38,.08); }

    /* ── Digest output ───────────────────────── */
    .digest-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 16px 18px;
      font-size: 0.88rem;
      line-height: 1.8;
      white-space: pre-wrap;
      word-break: break-word;
      animation: slideUp .2s ease;
    }

    .digest-meta {
      font-family: var(--mono);
      font-size: 0.73rem;
      color: var(--muted);
      margin-bottom: 10px;
    }

    /* ── Spacing ─────────────────────────────── */
    .mt12 { margin-top: 12px; }
    .mt16 { margin-top: 16px; }

    /* ── Inline row (ask) ────────────────────── */
    .inline-row { display: flex; gap: 8px; align-items: center; }
    .inline-row .prompt { flex: 1; padding: 10px 14px; }
    .inline-row .prompt textarea,
    .inline-row .prompt input { min-height: unset; }

    /* ── Float trigger button ────────────────── */
    .float-btn {
      position: fixed;
      bottom: max(36px, env(safe-area-inset-bottom, 36px));
      left: 50%;
      transform: translateX(-50%);
      background: var(--surface);
      border: 1px solid var(--accent);
      color: var(--accent);
      font-family: var(--mono);
      font-size: 0.9rem;
      letter-spacing: 0.06em;
      padding: 15px 38px;
      border-radius: 60px;
      cursor: pointer;
      box-shadow: 0 0 0 1px rgba(232,104,38,.15), 0 8px 32px rgba(0,0,0,.5);
      transition: transform .35s cubic-bezier(.4,0,.2,1), opacity .3s ease, box-shadow .2s;
      z-index: 200;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }
    .float-btn:active { box-shadow: 0 0 0 3px rgba(232,104,38,.25), 0 4px 16px rgba(0,0,0,.4); }
    .float-btn.away {
      transform: translateX(-50%) translateY(140%);
      opacity: 0;
      pointer-events: none;
    }
    @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
    .cur { display: inline-block; animation: blink 1.1s step-end infinite; }

    /* ── Textarea expand on focus ────────────── */
    .prompt.open { min-height: 110px; }
    .prompt { transition: min-height .3s ease; }
  </style>
</head>
<body>

  <header class="hdr">
    <h1 id="hdr-title">open-brain</h1>
    <div class="sub" id="hdr-sub">Mr.Fran</div>
  </header>

  <nav class="tabs">
    <button class="tab active" onclick="go('capture')">capture</button>
    <button class="tab" onclick="go('ask')">ask</button>
    <button class="tab" onclick="go('search')">search</button>
    <button class="tab" onclick="go('digest')">digest</button>
  </nav>

  <!-- CAPTURE ──────────────────────────────── -->
  <section id="tab-capture" class="panel active">
    <div class="lbl">Capture thought:</div>
    <div class="prompt">
      <span class="prompt-chr">&gt;</span>
      <textarea id="cap" rows="3" placeholder="type or dictate…" autofocus></textarea>
    </div>
    <div class="mt16">
      <button class="btn btn-accent" onclick="doCapture()">[ capture ]</button>
    </div>
    <div id="cap-ok" class="confirm">
      <div class="confirm-chk">✓</div>
      <div>
        <div class="confirm-title">Note captured — stored in <strong id="ok-cat">—</strong></div>
        <div class="confirm-meta">
          id:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span id="ok-id">—</span><br>
          category: <span id="ok-cat2">—</span>
        </div>
      </div>
    </div>
    <div id="cap-err" class="err"></div>
  </section>

  <!-- ASK ──────────────────────────────────── -->
  <section id="tab-ask" class="panel">
    <div class="lbl">Ask a question:</div>
    <div class="inline-row">
      <div class="prompt">
        <span class="prompt-chr">&gt;</span>
        <input type="text" id="ask-q" placeholder="what did I decide about…" onkeydown="if(event.key==='Enter')doAsk()">
      </div>
      <button class="btn btn-accent" onclick="doAsk()">[ ask ]</button>
    </div>
    <div id="ask-out" class="r-area"></div>
  </section>

  <!-- SEARCH ───────────────────────────────── -->
  <section id="tab-search" class="panel">
    <div class="lbl">Search notes:</div>
    <div class="prompt">
      <span class="prompt-chr">&gt;</span>
      <input type="text" id="s-q" placeholder="full-text search…" onkeydown="if(event.key==='Enter')doSearch()">
    </div>
    <div class="filter-row">
      <select id="s-cat">
        <option value="">all categories</option>
        <option value="admin">admin</option>
        <option value="idea">idea</option>
        <option value="person">person</option>
        <option value="project">project</option>
      </select>
      <input class="tag-input" type="text" id="s-tags" placeholder="tag, tag…">
      <button class="btn btn-accent" onclick="doSearch()">[ search ]</button>
    </div>
    <div id="search-out" class="r-area"></div>
  </section>

  <!-- DIGEST ───────────────────────────────── -->
  <section id="tab-digest" class="panel">
    <div class="lbl">Generate digest:</div>
    <div class="pills">
      <button class="pill on" id="p-daily"  onclick="setPeriod('daily')">daily</button>
      <button class="pill"    id="p-weekly" onclick="setPeriod('weekly')">weekly</button>
    </div>
    <button class="btn btn-accent" onclick="doDigest()">[ generate ]</button>
    <div id="digest-out" class="r-area"></div>
  </section>

<script>
// ── Tabs ────────────────────────────────────
const TABS = ['capture','ask','search','digest'];
function go(name) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', TABS[i] === name));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
}

// ── Auto-grow textarea ──────────────────────
const cap = document.getElementById('cap');
cap.addEventListener('input', () => { cap.style.height = 'auto'; cap.style.height = cap.scrollHeight + 'px'; });

// ── Capture ─────────────────────────────────
cap.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) doCapture(); });

async function doCapture() {
  const text = cap.value.trim();
  if (!text) return;
  hide('cap-ok'); hide('cap-err');

  try {
    const r = await fetch('/ingest/text', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    const j = await r.json().catch(() => ({error:'bad json'}));
    if (!r.ok) return showErr('cap-err', j.error || j.detail || JSON.stringify(j));

    document.getElementById('ok-cat').textContent  = j.category;
    document.getElementById('ok-cat2').textContent = j.category;
    document.getElementById('ok-id').textContent   = j.id;
    document.getElementById('cap-ok').classList.add('show');
    cap.value = ''; cap.style.height = 'auto';
  } catch(e) { showErr('cap-err', e.message); }
}

// ── Ask ─────────────────────────────────────
async function doAsk() {
  const q = document.getElementById('ask-q').value.trim();
  if (!q) return;
  busy('ask-out', 'thinking…');
  try {
    const r = await fetch('/api/query', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({question: q, limit: 5})
    });
    const j = await r.json().catch(() => ({error:'bad json'}));
    if (!r.ok) return setHtml('ask-out', errHtml(j.error || JSON.stringify(j)));

    const srcs = (j.sources || []).map(s =>
      `<span class="tag">${x(s.category)}: ${x(s.title)}</span>`).join(' ');
    setHtml('ask-out',
      `<div class="answer">${x(j.answer)}</div>` +
      (srcs ? `<div class="src-row">sources: ${srcs}</div>` : '')
    );
  } catch(e) { setHtml('ask-out', errHtml(e.message)); }
}

// ── Search ───────────────────────────────────
async function doSearch() {
  const text = document.getElementById('s-q').value.trim()   || null;
  const cat  = document.getElementById('s-cat').value        || null;
  const tags = document.getElementById('s-tags').value.trim()|| null;
  const p = new URLSearchParams({limit: 20});
  if (text) p.set('text', text);
  if (cat)  p.set('category', cat);
  if (tags) p.set('tags', tags);
  busy('search-out', 'searching…');
  try {
    const r = await fetch('/api/search?' + p);
    const j = await r.json().catch(() => ({error:'bad json'}));
    if (!r.ok) return setHtml('search-out', errHtml(j.error || JSON.stringify(j)));
    if (!j.items?.length) return setHtml('search-out', `<div class="loading" style="animation:none">no results.</div>`);

    setHtml('search-out',
      `<div class="loading" style="animation:none;margin-bottom:4px">${j.count} result(s)</div>` +
      j.items.map(i => `
        <div class="r-card">
          <div class="r-meta">${x(i.category)} · ${x(i.id)}</div>
          <div class="r-title">${x(i.title)}</div>
          <div class="r-body">${x(i.content)}</div>
          <div class="tags">${(i.tags||[]).map(t=>'<span class="tag">'+x(t)+'</span>').join('')}</div>
        </div>`).join('')
    );
  } catch(e) { setHtml('search-out', errHtml(e.message)); }
}

// ── Digest ───────────────────────────────────
let period = 'daily';
function setPeriod(p) {
  period = p;
  document.getElementById('p-daily').classList.toggle('on', p === 'daily');
  document.getElementById('p-weekly').classList.toggle('on', p === 'weekly');
}

async function doDigest() {
  busy('digest-out', 'generating digest…');
  try {
    const r = await fetch('/api/digest', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({period})
    });
    const j = await r.json().catch(() => ({error:'bad json'}));
    if (!r.ok) return setHtml('digest-out', errHtml(j.error || JSON.stringify(j)));
    setHtml('digest-out',
      `<div class="digest-meta">${j.period} · ${j.start_date.slice(0,10)} → ${j.end_date.slice(0,10)} · ${j.items.length} items</div>` +
      `<div class="digest-box">${x(j.content)}</div>`
    );
  } catch(e) { setHtml('digest-out', errHtml(e.message)); }
}

// ── Helpers ──────────────────────────────────
function x(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function setHtml(id, html) { document.getElementById(id).innerHTML = html; }
function busy(id, msg)     { setHtml(id, `<div class="loading">${msg}</div>`); }
function errHtml(msg)      { return `<div class="err show">${x(msg)}</div>`; }
function hide(id)          { document.getElementById(id).classList.remove('show'); }
function showErr(id, msg)  { const e = document.getElementById(id); e.textContent = msg; e.classList.add('show'); }

// ── Float button ─────────────────────────────
const floatBtn = document.getElementById('float-btn');
const capPrompt = cap.closest('.prompt');

function activateCapture() {
  floatBtn.classList.add('away');
  capPrompt.classList.add('open');
}

// label for="cap" handles iOS focus natively — no JS focus() needed
// animate away on cap focus, return on blur

cap.addEventListener('focus', activateCapture);

cap.addEventListener('blur', () => {
  setTimeout(() => {
    if (document.activeElement !== cap) {
      floatBtn.classList.remove('away');
      capPrompt.classList.remove('open');
    }
  }, 250);
});

// show/hide button with tab switches
const _go = go;
go = function(name) {
  _go(name);
  if (name === 'capture') {
    floatBtn.style.display = '';
  } else {
    floatBtn.classList.add('away');
    setTimeout(() => { if (document.querySelector('#tab-'+name+'.active')) floatBtn.style.display = 'none'; }, 380);
  }
};
</script>

  <!-- Floating type trigger (capture tab only) -->
  <label for="cap" id="float-btn" class="float-btn">&gt;&nbsp;<span class="cur">_</span></label>

</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.post("/ingest/text")
async def ingest_text(payload: dict):
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BRAIN_URL}/api/capture", json={"text": text, "source": "web_text"})
    if r.status_code != 200:
        return JSONResponse({"error": "brain capture failed", "detail": r.text}, status_code=502)
    return r.json()


@app.post("/api/query")
async def proxy_query(payload: dict):
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{BRAIN_URL}/api/query", json=payload)
    return JSONResponse(r.json(), status_code=r.status_code)


@app.get("/api/search")
async def proxy_search(category: str = None, tags: str = None, text: str = None, limit: int = 20):
    params = {"limit": limit}
    if category: params["category"] = category
    if tags:     params["tags"] = tags
    if text:     params["text"] = text
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BRAIN_URL}/api/search", params=params)
    return JSONResponse(r.json(), status_code=r.status_code)


@app.post("/api/digest")
async def proxy_digest(payload: dict):
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BRAIN_URL}/api/digest", json=payload)
    return JSONResponse(r.json(), status_code=r.status_code)
