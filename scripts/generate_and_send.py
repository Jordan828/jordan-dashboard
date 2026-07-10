"""
Jordan's Daily Market Briefing — Auto-generator
Google Finance-inspired design
Runs every weekday at 9:00 AM MYT via GitHub Actions
"""

import os, requests, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
FMP_API_KEY  = os.environ["FMP_API_KEY"]
GITHUB_REPO  = "jordan828/jordan-dashboard"

TICKERS = ["AAPL", "AIFF", "AMD", "INTC", "KEYS", "META", "MSFT", "MU", "NVDA", "PLTR"]

ANALYST_DATA = {
    "AAPL": {"rating":"Buy",  "strongBuy":1,  "buy":69, "hold":34, "sell":7,  "targetConsensus":327,    "targetHigh":400,  "targetLow":253},
    "AMD":  {"rating":"Buy",  "strongBuy":0,  "buy":50, "hold":20, "sell":0,  "targetConsensus":490.92, "targetHigh":700,  "targetLow":260},
    "META": {"rating":"Buy",  "strongBuy":2,  "buy":50, "hold":11, "sell":2,  "targetConsensus":827.5,  "targetHigh":910,  "targetLow":700},
    "MSFT": {"rating":"Buy",  "strongBuy":0,  "buy":66, "hold":16, "sell":0,  "targetConsensus":550.68, "targetHigh":680,  "targetLow":400},
    "NVDA": {"rating":"Buy",  "strongBuy":2,  "buy":58, "hold":16, "sell":3,  "targetConsensus":316.79, "targetHigh":500,  "targetLow":218},
    "PLTR": {"rating":"Buy",  "strongBuy":0,  "buy":12, "hold":11, "sell":3,  "targetConsensus":187.25, "targetHigh":230,  "targetLow":138},
    "KEYS": {"rating":"Buy",  "strongBuy":0,  "buy":13, "hold":4,  "sell":0,  "targetConsensus":383,    "targetHigh":420,  "targetLow":300},
    "MU":   {"rating":"Buy",  "strongBuy":2,  "buy":38, "hold":5,  "sell":0,  "targetConsensus":1180,   "targetHigh":1500, "targetLow":850},
    "INTC": {"rating":"Hold", "strongBuy":0,  "buy":31, "hold":46, "sell":7,  "targetConsensus":None,   "targetHigh":None, "targetLow":None},
    "AIFF": {"rating":"N/A",  "strongBuy":0,  "buy":0,  "hold":0,  "sell":0,  "targetConsensus":None,   "targetHigh":None, "targetLow":None},
}

COMPANY_NAMES = {
    "AAPL":"Apple Inc", "AIFF":"Firefly Neuroscience", "AMD":"Advanced Micro Devices",
    "INTC":"Intel Corp", "KEYS":"Keysight Technologies", "META":"Meta Platforms",
    "MSFT":"Microsoft Corp", "MU":"Micron Technology", "NVDA":"NVIDIA Corp", "PLTR":"Palantir Technologies"
}

SECTORS = {
    "NVDA":"AI Infra & Chips", "AMD":"AI Infra & Chips", "INTC":"AI Infra & Chips",
    "MU":"Memory & Semis", "KEYS":"Memory & Semis",
    "PLTR":"AI Software", "META":"AI Software",
    "MSFT":"Cloud & Enterprise", "AAPL":"Consumer Tech", "AIFF":"Speculative",
}

MYT = timezone(timedelta(hours=8))

# ─── FMP DATA FETCH ───────────────────────────────────────────────────────────
def fetch_quotes():
    symbols = ",".join(TICKERS)
    url = f"https://financialmodelingprep.com/stable/batch-quote-short?symbols={symbols}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15); r.raise_for_status()
        data = r.json()
        return {d["symbol"]: d for d in data} if data else {}
    except Exception as e:
        print(f"[WARN] Quote fetch failed: {e}"); return {}

def fetch_news():
    symbols = ",".join(TICKERS)
    url = f"https://financialmodelingprep.com/stable/news/stock?symbols={symbols}&limit=20&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15); r.raise_for_status()
        return r.json() or []
    except Exception as e:
        print(f"[WARN] News fetch failed: {e}"); return []

def fetch_indices():
    indices = ["^GSPC","^IXIC","^DJI","^VIX"]
    url = f"https://financialmodelingprep.com/stable/batch-quote-short?symbols={','.join(indices)}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15); r.raise_for_status()
        data = r.json()
        return {d["symbol"]: d for d in data} if data else {}
    except Exception as e:
        print(f"[WARN] Indices fetch failed: {e}"); return {}

# ─── ADVISOR LOGIC ────────────────────────────────────────────────────────────
def get_action(symbol, price, chg_pct, analyst):
    target = analyst.get("targetConsensus")
    upside = ((target - price) / price * 100) if target and price else None
    if symbol == "INTC": return ("HOLD",        "#f5a623", "Turnaround uncertain")
    if symbol == "AIFF": return ("SPECULATIVE",  "#ff4d6a", "Micro-cap, high risk")
    if symbol == "MSFT": return ("HOLD",         "#f5a623", "Watch earnings")
    if upside and upside > 40: return ("BUY",       "#00c98d", f"+{upside:.0f}% analyst upside")
    if upside and upside > 15: return ("HOLD/ADD",  "#4d9fff", f"+{upside:.0f}% upside remaining")
    if upside and upside < 0:  return ("CAUTION",   "#ff4d6a", "Above analyst target")
    return ("HOLD", "#f5a623", "Monitor")

def sentiment_tag(title):
    tl = title.lower()
    pos = ["buy","upgrade","beat","record","strong","growth","bullish","rally","gain","partner","opportunity","surge","high"]
    neg = ["sell","downgrade","miss","loss","weak","bearish","drop","cut","concern","risk","sold","lawsuit","decline"]
    score = sum(1 for w in pos if w in tl) - sum(1 for w in neg if w in tl)
    if score > 0:  return ("Bullish", "#00c98d", "▲")
    if score < 0:  return ("Bearish", "#ff4d6a", "▼")
    return ("Neutral", "#f5a623", "●")

# ─── SPARKLINE SVG ────────────────────────────────────────────────────────────
def mini_spark(pct, color, w=80, h=32):
    import math, random
    random.seed(abs(int(pct * 1000)))
    pts = [50]
    for _ in range(9):
        pts.append(max(5, min(95, pts[-1] + random.uniform(-8, 8) + pct * 0.3)))
    pts[-1] = 50 + pct * 2
    xs = [i * w / (len(pts)-1) for i in range(len(pts))]
    ys = [h - (p / 100 * h) for p in pts]
    path = " ".join(f"{'M' if i==0 else 'L'}{x:.1f},{y:.1f}" for i,(x,y) in enumerate(zip(xs,ys)))
    fill_path = f"{path} L{w},{ h} L0,{h} Z"
    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="g{abs(int(pct*100))}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
      </linearGradient></defs>
      <path d="{fill_path}" fill="url(#g{abs(int(pct*100))})" />
      <path d="{path}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>'''

# ─── HTML GENERATOR ───────────────────────────────────────────────────────────
def generate_html(quotes, news_items, indices, now):
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%I:%M %p MYT")

    # Market index bar
    idx_map = {"^GSPC":"S&P 500","^IXIC":"Nasdaq","^DJI":"Dow Jones","^VIX":"VIX"}
    idx_html = ""
    for sym, name in idx_map.items():
        q = indices.get(sym, {})
        price = q.get("price", 0)
        pct   = q.get("changesPercentage", 0)
        color = "#00c98d" if pct >= 0 else "#ff4d6a"
        arrow = "▲" if pct >= 0 else "▼"
        idx_html += f'''<div class="idx-card">
          <div class="idx-name">{name}</div>
          <div class="idx-price">{price:,.2f}</div>
          <div class="idx-chg" style="color:{color}">{arrow} {abs(pct):.2f}%</div>
        </div>'''

    # Watchlist cards
    watch_cards = ""
    for sym in TICKERS:
        q       = quotes.get(sym, {})
        price   = q.get("price", 0)
        pct     = q.get("changesPercentage", 0)
        chg     = q.get("change", 0)
        analyst = ANALYST_DATA.get(sym, {})
        target  = analyst.get("targetConsensus")
        upside  = f"+{((target-price)/price*100):.1f}%" if target and price else "—"
        action, act_color, reason = get_action(sym, price, pct, analyst)
        color   = "#00c98d" if pct >= 0 else "#ff4d6a"
        arrow   = "▲" if pct >= 0 else "▼"
        rating  = analyst.get("rating","N/A")
        rat_col = "#00c98d" if rating=="Buy" else "#f5a623" if rating=="Hold" else "#7a8096"
        sector  = SECTORS.get(sym,"Other")
        name    = COMPANY_NAMES.get(sym, sym)
        spark   = mini_spark(pct, color)
        up_color = "#00c98d" if upside.startswith("+") else "#ff4d6a"

        watch_cards += f'''<div class="wcard">
          <div class="wcard-top">
            <div>
              <div class="wcard-sym">{sym}</div>
              <div class="wcard-name">{name}</div>
              <div class="wcard-sector">{sector}</div>
            </div>
            <div class="wcard-spark">{spark}</div>
          </div>
          <div class="wcard-price">${price:,.2f}</div>
          <div class="wcard-chg" style="color:{color}">{arrow} {abs(pct):.2f}% (${abs(chg):.2f})</div>
          <div class="wcard-meta">
            <span class="wcard-tag" style="color:{rat_col};border-color:{rat_col}20;background:{rat_col}12">{rating}</span>
            <span class="wcard-tag" style="color:{act_color};border-color:{act_color}20;background:{act_color}12" title="{reason}">{action}</span>
            <span class="wcard-tag" style="color:{up_color}">{upside} upside</span>
          </div>
        </div>'''

    # News items
    news_html = ""
    for n in news_items[:12]:
        sym_n   = n.get("symbol","")
        title_n = n.get("title","")
        pub     = n.get("publishedDate","")[:10]
        url_n   = n.get("url","#")
        sent, sent_color, sent_arrow = sentiment_tag(title_n)
        news_html += f'''<div class="news-row">
          <div class="news-left">
            <span class="news-sym">{sym_n}</span>
            <span class="news-sent" style="color:{sent_color}">{sent_arrow} {sent}</span>
          </div>
          <div class="news-title"><a href="{url_n}" target="_blank">{title_n}</a></div>
          <div class="news-date">{pub}</div>
        </div>'''

    # Sector concentration data
    sector_map = {}
    for sym in TICKERS:
        sec = SECTORS.get(sym,"Other")
        sector_map[sec] = sector_map.get(sec,0)+1
    sector_labels = list(sector_map.keys())
    sector_counts  = list(sector_map.values())

    # Analyst bar data
    a_syms  = [s for s in TICKERS if ANALYST_DATA[s]['buy']>0 or ANALYST_DATA[s]['hold']>0]
    a_buys  = [ANALYST_DATA[s]['strongBuy']+ANALYST_DATA[s]['buy'] for s in a_syms]
    a_holds = [ANALYST_DATA[s]['hold'] for s in a_syms]
    a_sells = [ANALYST_DATA[s]['sell'] for s in a_syms]

    winners = sum(1 for s in TICKERS if quotes.get(s,{}).get("changesPercentage",0)>0)
    losers  = sum(1 for s in TICKERS if quotes.get(s,{}).get("changesPercentage",0)<0)
    top_q   = max(TICKERS, key=lambda s: abs(quotes.get(s,{}).get("changesPercentage",0)), default="—")
    top_pct = quotes.get(top_q,{}).get("changesPercentage",0)
    top_col = "#00c98d" if top_pct>=0 else "#ff4d6a"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jordan's Market Briefing — {now.strftime('%d %b %Y')}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" crossorigin="anonymous"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f1117;--sidebar:#13151e;--card:#1a1d27;--card2:#1f2233;
  --border:#252a3a;--text:#e8eaf0;--sec:#8b90a7;--muted:#4a5068;
  --green:#00c98d;--red:#ff4d6a;--amber:#f5a623;--blue:#4d9fff;--purple:#a78bfa;
  --r:10px;--gap:14px;
}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;min-height:100vh}}

/* TOP BAR */
.topbar{{background:var(--sidebar);border-bottom:1px solid var(--border);padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:56px;position:sticky;top:0;z-index:100}}
.topbar-logo{{font-size:16px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:8px}}
.topbar-right{{display:flex;align-items:center;gap:10px}}
.live-pill{{display:flex;align-items:center;gap:5px;background:rgba(0,201,141,.1);border:1px solid rgba(0,201,141,.25);border-radius:20px;padding:4px 10px;font-size:11px;color:var(--green);font-weight:600}}
.dot{{width:6px;height:6px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.rbtn{{display:flex;align-items:center;gap:5px;background:var(--green);color:#000;border:none;border-radius:20px;padding:6px 14px;font-size:12px;font-weight:700;cursor:pointer;transition:all .2s}}
.rbtn:hover{{background:#00b07a;transform:scale(1.03)}}
.rbtn:disabled{{background:#1a2a20;color:var(--muted);cursor:not-allowed;transform:none}}
.spin{{display:inline-block;animation:spin 1s linear infinite}}
@keyframes spin{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}
.time-stamp{{font-size:11px;color:var(--sec)}}

/* INDEX BAR */
.idx-bar{{display:flex;gap:0;overflow-x:auto;background:var(--sidebar);border-bottom:1px solid var(--border);padding:0 24px}}
.idx-card{{padding:10px 24px 10px 0;margin-right:24px;border-right:1px solid var(--border);flex-shrink:0;cursor:pointer}}
.idx-card:last-child{{border-right:none}}
.idx-name{{font-size:11px;color:var(--sec);margin-bottom:2px}}
.idx-price{{font-size:14px;font-weight:600;color:var(--text)}}
.idx-chg{{font-size:12px;font-weight:500;margin-top:1px}}

/* LAYOUT */
.layout{{display:grid;grid-template-columns:280px 1fr;min-height:calc(100vh - 90px)}}

/* SIDEBAR */
.sidebar{{background:var(--sidebar);border-right:1px solid var(--border);padding:16px 0;overflow-y:auto}}
.sb-section{{padding:0 16px;margin-bottom:20px}}
.sb-title{{font-size:11px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px;padding:0 4px}}
.sb-item{{display:flex;justify-content:space-between;align-items:center;padding:8px 4px;border-radius:8px;cursor:pointer;transition:background .15s}}
.sb-item:hover{{background:var(--card2)}}
.sb-left{{display:flex;flex-direction:column;gap:2px}}
.sb-sym{{font-size:13px;font-weight:600;color:var(--text)}}
.sb-name{{font-size:11px;color:var(--sec)}}
.sb-right{{display:flex;flex-direction:column;align-items:flex-end;gap:2px}}
.sb-price{{font-size:13px;font-weight:600}}
.sb-pct{{font-size:11px;font-weight:500}}

/* MAIN */
.main{{padding:20px 24px;overflow-y:auto}}
.main-title{{font-size:20px;font-weight:700;margin-bottom:4px}}
.main-sub{{font-size:12px;color:var(--sec);margin-bottom:18px}}

/* KPI ROW */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap);margin-bottom:20px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px}}
.kpi-l{{font-size:11px;color:var(--sec);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}}
.kpi-v{{font-size:24px;font-weight:700;letter-spacing:-.5px}}
.kpi-s{{font-size:11px;color:var(--sec);margin-top:3px}}

/* WATCHLIST CARDS GRID */
.wgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:var(--gap);margin-bottom:20px}}
.wcard{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;cursor:pointer;transition:border-color .2s,transform .15s}}
.wcard:hover{{border-color:#4a5068;transform:translateY(-1px)}}
.wcard-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}}
.wcard-sym{{font-size:15px;font-weight:700;color:var(--text)}}
.wcard-name{{font-size:11px;color:var(--sec);margin-top:1px}}
.wcard-sector{{font-size:10px;color:var(--muted);margin-top:2px}}
.wcard-spark{{opacity:.9}}
.wcard-price{{font-size:20px;font-weight:700;letter-spacing:-.5px;margin-bottom:3px}}
.wcard-chg{{font-size:12px;font-weight:500;margin-bottom:8px}}
.wcard-meta{{display:flex;gap:5px;flex-wrap:wrap}}
.wcard-tag{{font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid;font-weight:600}}

/* NEWS */
.news-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;margin-bottom:20px}}
.news-hdr{{padding:12px 16px;border-bottom:1px solid var(--border);font-size:12px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.06em}}
.news-row{{display:grid;grid-template-columns:120px 1fr 90px;gap:10px;align-items:center;padding:11px 16px;border-bottom:1px solid var(--border);transition:background .15s}}
.news-row:last-child{{border-bottom:none}}
.news-row:hover{{background:var(--card2)}}
.news-left{{display:flex;flex-direction:column;gap:3px}}
.news-sym{{font-size:11px;font-weight:700;color:var(--blue)}}
.news-sent{{font-size:10px;font-weight:600}}
.news-title{{font-size:12px;color:var(--text);line-height:1.45}}
.news-title a{{color:var(--text);text-decoration:none}}
.news-title a:hover{{color:var(--blue)}}
.news-date{{font-size:11px;color:var(--muted);text-align:right}}

/* CHARTS ROW */
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);margin-bottom:20px}}
.chart-card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px}}
.chart-title{{font-size:12px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}}
.ch{{height:200px;position:relative}}

/* FOOTER */
.footer{{background:var(--sidebar);border-top:1px solid var(--border);padding:14px 24px;font-size:11px;color:var(--muted);text-align:center;line-height:1.7}}

@media(max-width:900px){{
  .layout{{grid-template-columns:1fr}}
  .sidebar{{display:none}}
  .kpi-row,.charts-row{{grid-template-columns:repeat(2,1fr)}}
  .wgrid{{grid-template-columns:repeat(2,1fr)}}
  .news-row{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
  <div class="topbar-logo">📊 Jordan's Market Briefing</div>
  <div class="topbar-right">
    <div class="time-stamp">{date_str} · {time_str}</div>
    <div class="live-pill"><div class="dot"></div>LIVE</div>
    <button class="rbtn" id="refreshBtn" onclick="triggerRefresh()">🔄 Refresh</button>
  </div>
</div>

<!-- INDEX BAR -->
<div class="idx-bar">{idx_html}</div>

<!-- LAYOUT -->
<div class="layout">

  <!-- SIDEBAR WATCHLIST -->
  <div class="sidebar">
    <div class="sb-section">
      <div class="sb-title">Watchlist</div>
      {''.join(f"""<div class="sb-item">
        <div class="sb-left">
          <span class="sb-sym">{sym}</span>
          <span class="sb-name">{COMPANY_NAMES.get(sym,'')[:20]}</span>
        </div>
        <div class="sb-right">
          <span class="sb-price" style="color:{'#00c98d' if quotes.get(sym,{{}}).get('changesPercentage',0)>=0 else '#ff4d6a'}">${quotes.get(sym,{{}}).get('price',0):,.2f}</span>
          <span class="sb-pct" style="color:{'#00c98d' if quotes.get(sym,{{}}).get('changesPercentage',0)>=0 else '#ff4d6a'}">{'▲' if quotes.get(sym,{{}}).get('changesPercentage',0)>=0 else '▼'} {abs(quotes.get(sym,{{}}).get('changesPercentage',0)):.2f}%</span>
        </div>
      </div>""" for sym in TICKERS)}
    </div>
  </div>

  <!-- MAIN CONTENT -->
  <div class="main">
    <div class="main-title">Good Morning, Jordan! 👋</div>
    <div class="main-sub">Here's your market snapshot for {date_str}</div>

    <!-- KPI ROW -->
    <div class="kpi-row">
      <div class="kpi"><div class="kpi-l">Winners Today</div><div class="kpi-v" style="color:var(--green)">{winners}</div><div class="kpi-s">stocks up</div></div>
      <div class="kpi"><div class="kpi-l">Losers Today</div><div class="kpi-v" style="color:var(--red)">{losers}</div><div class="kpi-s">stocks down</div></div>
      <div class="kpi"><div class="kpi-l">Biggest Mover</div><div class="kpi-v" style="color:{top_col};font-size:18px">{top_q} {top_pct:+.2f}%</div><div class="kpi-s">largest move</div></div>
      <div class="kpi"><div class="kpi-l">Advisor Alerts</div><div class="kpi-v" style="color:var(--amber)">↓ Below</div><div class="kpi-s">check actions</div></div>
    </div>

    <!-- WATCHLIST CARDS -->
    <div style="font-size:12px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Your Watchlist</div>
    <div class="wgrid">{watch_cards}</div>

    <!-- CHARTS -->
    <div class="charts-row">
      <div class="chart-card"><div class="chart-title">Sector Concentration</div><div class="ch"><canvas id="donut"></canvas></div></div>
      <div class="chart-card"><div class="chart-title">Analyst Consensus</div><div class="ch"><canvas id="analyst"></canvas></div></div>
    </div>

    <!-- NEWS -->
    <div class="news-card">
      <div class="news-hdr">📰 Latest News</div>
      {news_html}
    </div>
  </div>
</div>

<!-- FOOTER -->
<div class="footer">
  🤖 Auto-generated by Jordan's AI Financial Advisor · Data via Financial Modeling Prep (FMP) · Updates every weekday 9:00 AM MYT<br>
  ⚠️ Not financial advice. Past performance does not guarantee future results.
</div>

<script>
// ─── CHARTS ───────────────────────────────────────────────────────────────────
const sColors = ['#a78bfa','#4d9fff','#7f77dd','#00c98d','#f5a623','#ff4d6a'];
new Chart(document.getElementById('donut'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(sector_labels)},datasets:[{{data:{json.dumps(sector_counts)},backgroundColor:sColors,borderColor:'#0f1117',borderWidth:3,hoverOffset:6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{{legend:{{position:'right',labels:{{color:'#8b90a7',font:{{size:10}},boxWidth:10,padding:8}}}}}}}}
}});
new Chart(document.getElementById('analyst'),{{
  type:'bar',
  data:{{labels:{json.dumps(a_syms)},datasets:[
    {{label:'Buy', data:{json.dumps(a_buys)}, backgroundColor:'rgba(0,201,141,.8)',borderRadius:3}},
    {{label:'Hold',data:{json.dumps(a_holds)},backgroundColor:'rgba(245,166,35,.8)',borderRadius:3}},
    {{label:'Sell',data:{json.dumps(a_sells)},backgroundColor:'rgba(255,77,106,.8)',borderRadius:3}},
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{labels:{{color:'#8b90a7',font:{{size:10}},boxWidth:10}}}}}},
    scales:{{
      x:{{stacked:true,grid:{{display:false}},ticks:{{color:'#8b90a7',font:{{size:10}}}}}},
      y:{{stacked:true,grid:{{color:'rgba(37,42,58,.8)'}},ticks:{{color:'#8b90a7',font:{{size:10}}}}}}
    }}
  }}
}});

// ─── REFRESH BUTTON ───────────────────────────────────────────────────────────
async function triggerRefresh() {{
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin">🔄</span> Refreshing...';
  try {{
    const token = prompt("Paste your GitHub Personal Access Token:");
    if (!token) {{ btn.disabled=false; btn.innerHTML='🔄 Refresh'; return; }}
    const r = await fetch('https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/daily-briefing.yml/dispatches', {{
      method:'POST',
      headers:{{'Authorization':`Bearer ${{token}}`,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}},
      body:JSON.stringify({{ref:'main'}})
    }});
    if (r.status===204) {{
      btn.innerHTML='⏳ Wait 30s then reload';
      setTimeout(()=>{{btn.innerHTML='✅ Reload now!';btn.disabled=false;}},35000);
    }} else {{
      btn.innerHTML='❌ Check token';
      setTimeout(()=>{{btn.innerHTML='🔄 Refresh';btn.disabled=false;}},3000);
    }}
  }} catch(e) {{
    btn.innerHTML='❌ Error';
    setTimeout(()=>{{btn.innerHTML='🔄 Refresh';btn.disabled=false;}},3000);
  }}
}}
</script>
</body>
</html>"""
    return html

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(MYT)
    print(f"[{now.strftime('%Y-%m-%d %H:%M MYT')}] Starting Jordan's daily briefing...")
    quotes  = fetch_quotes();  print(f"  Got {len(quotes)} quotes")
    news    = fetch_news();    print(f"  Got {len(news)} news items")
    indices = fetch_indices(); print(f"  Got {len(indices)} indices")
    html    = generate_html(quotes, news, indices, now)
    out_dir = Path("docs"); out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print("  Dashboard saved to docs/index.html")
    print("Done! ✅")

if __name__ == "__main__":
    main()
