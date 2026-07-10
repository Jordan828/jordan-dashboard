"""
Jordan's Daily Market Briefing — Auto-generator
Runs every weekday at 9:00 AM MYT via GitHub Actions
- Fetches live data from FMP API
- Generates a full HTML dashboard saved to /docs/index.html
- Deploys to GitHub Pages automatically
"""

import os, requests, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
FMP_API_KEY = os.environ["FMP_API_KEY"]

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

SECTORS = {
    "NVDA": "AI Infra & Chips", "AMD": "AI Infra & Chips", "INTC": "AI Infra & Chips",
    "MU":   "Memory & Semis",   "KEYS": "Memory & Semis",
    "PLTR": "AI Software",      "META": "AI Software",
    "MSFT": "Cloud & Enterprise",
    "AAPL": "Consumer Tech",
    "AIFF": "Speculative",
}

MYT = timezone(timedelta(hours=8))

# ─── FMP DATA FETCH ───────────────────────────────────────────────────────────
def fetch_quotes():
    symbols = ",".join(TICKERS)
    url = f"https://financialmodelingprep.com/stable/batch-quote-short?symbols={symbols}&apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {d["symbol"]: d for d in data} if data else {}
    except Exception as e:
        print(f"[WARN] Quote fetch failed: {e}")
        return {}

def fetch_news():
    symbols = ",".join(TICKERS)
    url = f"https://financialmodelingprep.com/stable/news/stock?symbols={symbols}&limit=15&apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json() or []
    except Exception as e:
        print(f"[WARN] News fetch failed: {e}")
        return []

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
    title_l = title.lower()
    pos_words = ["buy","upgrade","beat","record","strong","growth","bullish","rally","gain","partner","opportunity"]
    neg_words = ["sell","downgrade","miss","loss","weak","bearish","drop","cut","concern","risk","sold","lawsuit"]
    score = sum(1 for w in pos_words if w in title_l) - sum(1 for w in neg_words if w in title_l)
    if score > 0:  return ("📈 Bullish", "#00c98d")
    if score < 0:  return ("📉 Bearish", "#ff4d6a")
    return ("⚖️ Neutral", "#f5a623")

# ─── HTML DASHBOARD GENERATOR ─────────────────────────────────────────────────
def generate_html(quotes, news_items, now):
    date_str = now.strftime("%A, %d %B %Y — %I:%M %p MYT")

    rows_html = ""
    for sym in TICKERS:
        q        = quotes.get(sym, {})
        price    = q.get("price", 0)
        pct      = q.get("changesPercentage", 0)
        analyst  = ANALYST_DATA.get(sym, {})
        target   = analyst.get("targetConsensus")
        upside   = f"{((target - price)/price*100):+.1f}%" if target and price else "—"
        action, action_color, reason = get_action(sym, price, pct, analyst)
        pct_color = "#00c98d" if pct >= 0 else "#ff4d6a"
        arrow     = "▲" if pct >= 0 else "▼"
        rating    = analyst.get("rating", "N/A")
        rat_color = "#00c98d" if rating == "Buy" else "#f5a623" if rating == "Hold" else "#7a8096"
        sector    = SECTORS.get(sym, "Other")

        rows_html += f"""
        <tr>
          <td><strong style="color:#e8eaf0">{sym}</strong><div style="font-size:11px;color:#7a8096">{sector}</div></td>
          <td style="font-size:15px;font-weight:600">${price:,.2f}</td>
          <td><span style="background:{'rgba(0,201,141,.15)' if pct>=0 else 'rgba(255,77,106,.15)'};color:{pct_color};padding:2px 8px;border-radius:10px;font-weight:600;font-size:12px">{arrow} {abs(pct):.2f}%</span></td>
          <td style="color:#7a8096;font-size:12px">{f'${target:,.0f}' if target else '—'}</td>
          <td style="color:{'#00c98d' if upside != '—' and upside[0]=='+' else '#ff4d6a'};font-size:12px;font-weight:600">{upside}</td>
          <td><span style="background:rgba(0,0,0,.3);color:{rat_color};padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600">{rating}</span></td>
          <td><span style="background:rgba(0,0,0,.3);color:{action_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700" title="{reason}">{action}</span></td>
        </tr>"""

    news_html = ""
    for n in news_items[:10]:
        sym_n   = n.get("symbol", "")
        title_n = n.get("title", "")
        pub     = n.get("publishedDate", "")[:10]
        sent, sent_color = sentiment_tag(title_n)
        url_n   = n.get("url", "#")
        news_html += f"""
        <div style="padding:10px 0;border-bottom:1px solid #252a38">
          <div style="font-size:11px;font-weight:700;color:#4d9fff;margin-bottom:3px">{sym_n}</div>
          <div style="font-size:13px;color:#e8eaf0;line-height:1.4;margin-bottom:4px">
            <a href="{url_n}" target="_blank" style="color:#e8eaf0;text-decoration:none">{title_n}</a>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <span style="font-size:11px;color:{sent_color}">{sent}</span>
            <span style="font-size:11px;color:#4a5068">{pub}</span>
          </div>
        </div>"""

    winners_count = sum(1 for s in TICKERS if quotes.get(s, {}).get("changesPercentage", 0) > 0)
    losers_count  = sum(1 for s in TICKERS if quotes.get(s, {}).get("changesPercentage", 0) < 0)
    top_q  = max(TICKERS, key=lambda s: abs(quotes.get(s, {}).get("changesPercentage", 0)), default="—")
    top_pct = quotes.get(top_q, {}).get("changesPercentage", 0)

    sector_map = {}
    for sym in TICKERS:
        sec = SECTORS.get(sym, "Other")
        sector_map[sec] = sector_map.get(sec, 0) + 1
    sector_labels = list(sector_map.keys())
    sector_counts  = list(sector_map.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jordan's Morning Briefing — {now.strftime('%d %b %Y')}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" crossorigin="anonymous"></script>
<style>
  :root{{--bg:#0d0f14;--card:#151820;--card2:#1a1e28;--border:#252a38;--text:#e8eaf0;--sec:#7a8096;--muted:#4a5068;--green:#00c98d;--red:#ff4d6a;--amber:#f5a623;--blue:#4d9fff;--r:12px;--gap:16px}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px}}
  .wrap{{max-width:1400px;margin:0 auto;padding:24px 20px}}
  .hdr{{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px}}
  h1{{font-size:22px;font-weight:700;letter-spacing:-.3px}}
  .sub{{font-size:13px;color:var(--sec);margin-top:3px}}
  .live{{display:flex;align-items:center;gap:8px}}
  .dot{{width:8px;height:8px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
  .stamp{{font-size:12px;color:var(--sec);background:var(--card);border:1px solid var(--border);border-radius:20px;padding:4px 12px}}
  .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap);margin-bottom:var(--gap)}}
  .kpi{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px 18px}}
  .kpi-l{{font-size:11px;color:var(--sec);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}}
  .kpi-v{{font-size:26px;font-weight:700}}
  .kpi-s{{font-size:12px;color:var(--sec);margin-top:4px}}
  .grid2{{display:grid;grid-template-columns:1fr 360px;gap:var(--gap);margin-bottom:var(--gap)}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:18px 20px}}
  .ct{{font-size:11px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.07em;margin-bottom:14px}}
  table{{width:100%;border-collapse:collapse}}
  thead th{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;padding:6px 10px;text-align:right;border-bottom:1px solid var(--border)}}
  thead th:first-child{{text-align:left}}
  tbody tr{{border-bottom:1px solid #1e2230;transition:background .15s}}
  tbody tr:hover{{background:var(--card2)}}
  td{{padding:11px 10px;text-align:right;vertical-align:middle}}
  td:first-child{{text-align:left}}
  .charts{{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);margin-bottom:var(--gap)}}
  .ch{{height:220px;position:relative}}
  .footer{{text-align:center;font-size:11px;color:var(--muted);margin-top:24px;padding-top:16px;border-top:1px solid var(--border);line-height:1.7}}
  @media(max-width:900px){{.grid2,.kpis,.charts{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div>
      <h1>📊 Good Morning, Jordan!</h1>
      <div class="sub">Daily Market Briefing · {date_str}</div>
    </div>
    <div class="live">
      <div class="dot"></div>
      <span style="font-size:12px;color:var(--green);font-weight:500">LIVE</span>
      <div class="stamp">Auto-generated 9:00 AM MYT</div>
    </div>
  </div>

  <div class="kpis">
    <div class="kpi"><div class="kpi-l">Winners Today</div><div class="kpi-v" style="color:var(--green)">{winners_count}</div><div class="kpi-s">stocks up</div></div>
    <div class="kpi"><div class="kpi-l">Losers Today</div><div class="kpi-v" style="color:var(--red)">{losers_count}</div><div class="kpi-s">stocks down</div></div>
    <div class="kpi"><div class="kpi-l">Biggest Mover</div><div class="kpi-v" style="color:{'var(--green)' if top_pct>=0 else 'var(--red)'}">{top_q} {top_pct:+.2f}%</div><div class="kpi-s">largest % move</div></div>
    <div class="kpi"><div class="kpi-l">Stocks to Watch</div><div class="kpi-v" style="color:var(--amber)">↑ See below</div><div class="kpi-s">advisor picks</div></div>
  </div>

  <div class="grid2">
    <div class="card">
      <div class="ct">Your Watchlist — Live Prices</div>
      <table>
        <thead><tr><th>Stock</th><th>Price</th><th>Day Chg</th><th>Target</th><th>Upside</th><th>Analyst</th><th>Action</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <div class="card">
      <div class="ct">📰 Today's Top News</div>
      {news_html}
    </div>
  </div>

  <div class="charts">
    <div class="card"><div class="ct">🧩 Sector Concentration</div><div class="ch"><canvas id="donut"></canvas></div></div>
    <div class="card"><div class="ct">📊 Analyst Consensus (Buy / Hold / Sell)</div><div class="ch"><canvas id="analyst"></canvas></div></div>
  </div>

  <div class="footer">
    🤖 Auto-generated by Jordan's AI Financial Advisor · Data via Financial Modeling Prep (FMP)<br>
    ⚠️ This dashboard is for informational purposes only and does not constitute financial advice.<br>
    Past performance does not guarantee future results. Always consult a licensed advisor before investing.
  </div>
</div>
<script>
const sColors = ['#a78bfa','#4d9fff','#7f77dd','#00c98d','#f5a623','#ff4d6a'];
new Chart(document.getElementById('donut'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(sector_labels)},datasets:[{{data:{json.dumps(sector_counts)},backgroundColor:sColors,borderColor:'#0d0f14',borderWidth:3,hoverOffset:8}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'62%',plugins:{{legend:{{position:'right',labels:{{color:'#7a8096',font:{{size:11}},boxWidth:12,padding:10}}}}}}}}
}});
const aSyms  = {json.dumps([s for s in TICKERS if ANALYST_DATA[s]['buy'] > 0 or ANALYST_DATA[s]['hold'] > 0])};
const aBuys  = {json.dumps([ANALYST_DATA[s]['strongBuy']+ANALYST_DATA[s]['buy'] for s in TICKERS if ANALYST_DATA[s]['buy'] > 0 or ANALYST_DATA[s]['hold'] > 0])};
const aHolds = {json.dumps([ANALYST_DATA[s]['hold'] for s in TICKERS if ANALYST_DATA[s]['buy'] > 0 or ANALYST_DATA[s]['hold'] > 0])};
const aSells = {json.dumps([ANALYST_DATA[s]['sell'] for s in TICKERS if ANALYST_DATA[s]['buy'] > 0 or ANALYST_DATA[s]['hold'] > 0])};
new Chart(document.getElementById('analyst'),{{
  type:'bar',
  data:{{labels:aSyms,datasets:[
    {{label:'Buy',data:aBuys,backgroundColor:'rgba(0,201,141,.8)',borderRadius:3}},
    {{label:'Hold',data:aHolds,backgroundColor:'rgba(245,166,35,.8)',borderRadius:3}},
    {{label:'Sell',data:aSells,backgroundColor:'rgba(255,77,106,.8)',borderRadius:3}},
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#7a8096',font:{{size:11}}}}}}}},scales:{{x:{{stacked:true,grid:{{display:false}},ticks:{{color:'#7a8096',font:{{size:10}}}}}},y:{{stacked:true,grid:{{color:'#1e2230'}},ticks:{{color:'#7a8096',font:{{size:10}}}}}}}}}}
}});
</script>
</body>
</html>"""
    return html

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(MYT)
    print(f"[{now.strftime('%Y-%m-%d %H:%M MYT')}] Starting Jordan's daily briefing...")

    print("Fetching quotes from FMP...")
    quotes = fetch_quotes()
    print(f"  Got {len(quotes)} quotes")

    print("Fetching news from FMP...")
    news = fetch_news()
    print(f"  Got {len(news)} news items")

    print("Generating HTML dashboard...")
    html = generate_html(quotes, news, now)

    out_dir = Path("docs")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  Dashboard saved to docs/index.html")

    print("Done! ✅")

if __name__ == "__main__":
    main()
