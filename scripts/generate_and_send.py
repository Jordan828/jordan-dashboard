"""
Jordan's Daily Market Briefing — Auto-generator
Google Finance-inspired design
Runs every weekday at 9:00 AM MYT via GitHub Actions
"""

import os, requests, json, random
from datetime import datetime, timezone, timedelta
from pathlib import Path

FMP_API_KEY = os.environ["FMP_API_KEY"]
GITHUB_REPO = "jordan828/jordan-dashboard"
TICKERS     = ["AAPL","AIFF","AMD","INTC","KEYS","META","MSFT","MU","NVDA","PLTR"]
MYT         = timezone(timedelta(hours=8))

ANALYST_DATA = {
    "AAPL":{"rating":"Buy",  "strongBuy":1, "buy":69,"hold":34,"sell":7, "targetConsensus":327,   "targetHigh":400, "targetLow":253},
    "AMD": {"rating":"Buy",  "strongBuy":0, "buy":50,"hold":20,"sell":0, "targetConsensus":490.92,"targetHigh":700, "targetLow":260},
    "META":{"rating":"Buy",  "strongBuy":2, "buy":50,"hold":11,"sell":2, "targetConsensus":827.5, "targetHigh":910, "targetLow":700},
    "MSFT":{"rating":"Buy",  "strongBuy":0, "buy":66,"hold":16,"sell":0, "targetConsensus":550.68,"targetHigh":680, "targetLow":400},
    "NVDA":{"rating":"Buy",  "strongBuy":2, "buy":58,"hold":16,"sell":3, "targetConsensus":316.79,"targetHigh":500, "targetLow":218},
    "PLTR":{"rating":"Buy",  "strongBuy":0, "buy":12,"hold":11,"sell":3, "targetConsensus":187.25,"targetHigh":230, "targetLow":138},
    "KEYS":{"rating":"Buy",  "strongBuy":0, "buy":13,"hold":4, "sell":0, "targetConsensus":383,   "targetHigh":420, "targetLow":300},
    "MU":  {"rating":"Buy",  "strongBuy":2, "buy":38,"hold":5, "sell":0, "targetConsensus":1180,  "targetHigh":1500,"targetLow":850},
    "INTC":{"rating":"Hold", "strongBuy":0, "buy":31,"hold":46,"sell":7, "targetConsensus":None,  "targetHigh":None,"targetLow":None},
    "AIFF":{"rating":"N/A",  "strongBuy":0, "buy":0, "hold":0, "sell":0, "targetConsensus":None,  "targetHigh":None,"targetLow":None},
}

COMPANY_NAMES = {
    "AAPL":"Apple Inc","AIFF":"Firefly Neuroscience","AMD":"Advanced Micro Devices",
    "INTC":"Intel Corp","KEYS":"Keysight Technologies","META":"Meta Platforms",
    "MSFT":"Microsoft Corp","MU":"Micron Technology","NVDA":"NVIDIA Corp","PLTR":"Palantir Technologies"
}

SECTORS = {
    "NVDA":"AI Infra & Chips","AMD":"AI Infra & Chips","INTC":"AI Infra & Chips",
    "MU":"Memory & Semis","KEYS":"Memory & Semis",
    "PLTR":"AI Software","META":"AI Software",
    "MSFT":"Cloud & Enterprise","AAPL":"Consumer Tech","AIFF":"Speculative",
}

# ── FETCH ─────────────────────────────────────────────────────────────────────
def fetch_quotes():
    url = "https://financialmodelingprep.com/stable/batch-quote-short?symbols=" + ",".join(TICKERS) + "&apikey=" + FMP_API_KEY
    try:
        r = requests.get(url, timeout=15); r.raise_for_status()
        data = r.json(); return {d["symbol"]:d for d in data} if data else {}
    except Exception as e:
        print("[WARN] quotes:", e); return {}

def fetch_news():
    url = "https://financialmodelingprep.com/stable/news/stock?symbols=" + ",".join(TICKERS) + "&limit=20&apikey=" + FMP_API_KEY
    try:
        r = requests.get(url, timeout=15); r.raise_for_status(); return r.json() or []
    except Exception as e:
        print("[WARN] news:", e); return []

def fetch_indices():
    url = "https://financialmodelingprep.com/stable/batch-quote-short?symbols=^GSPC,^IXIC,^DJI,^VIX&apikey=" + FMP_API_KEY
    try:
        r = requests.get(url, timeout=15); r.raise_for_status()
        data = r.json(); return {d["symbol"]:d for d in data} if data else {}
    except Exception as e:
        print("[WARN] indices:", e); return {}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_action(sym, price, analyst):
    target = analyst.get("targetConsensus")
    up = ((target - price) / price * 100) if target and price else None
    if sym == "INTC": return "HOLD",    "#f5a623", "Turnaround uncertain"
    if sym == "AIFF": return "SPEC",    "#ff4d6a", "Micro-cap, high risk"
    if sym == "MSFT": return "HOLD",    "#f5a623", "Watch earnings"
    if up and up > 40: return "BUY",    "#00c98d", "+%.0f%% upside" % up
    if up and up > 15: return "HOLD/ADD","#4d9fff", "+%.0f%% upside" % up
    if up and up < 0:  return "CAUTION","#ff4d6a", "Above target"
    return "HOLD","#f5a623","Monitor"

def sentiment(title):
    tl = title.lower()
    pos = ["buy","upgrade","beat","record","strong","growth","bullish","rally","gain","surge"]
    neg = ["sell","downgrade","miss","loss","weak","bearish","drop","cut","lawsuit","decline"]
    s = sum(1 for w in pos if w in tl) - sum(1 for w in neg if w in tl)
    if s > 0: return "Bullish","#00c98d","▲"
    if s < 0: return "Bearish","#ff4d6a","▼"
    return "Neutral","#f5a623","●"

def sparkline(pct, color, w=80, h=32):
    random.seed(abs(int(pct*1000)))
    pts = [50]
    for _ in range(9):
        pts.append(max(5, min(95, pts[-1] + random.uniform(-8,8) + pct*0.3)))
    pts[-1] = min(95, max(5, 50 + pct*2))
    xs = [i*w/(len(pts)-1) for i in range(len(pts))]
    ys = [h-(p/100*h) for p in pts]
    d  = " ".join(("M" if i==0 else "L")+"%.1f,%.1f"%(x,y) for i,(x,y) in enumerate(zip(xs,ys)))
    fd = d+" L%.1f,%d L0,%d Z"%(w,h,h)
    g  = abs(int(pct*100))
    return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">'
            '<defs><linearGradient id="g%d" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0%%" stop-color="%s" stop-opacity="0.3"/>'
            '<stop offset="100%%" stop-color="%s" stop-opacity="0.02"/>'
            '</linearGradient></defs>'
            '<path d="%s" fill="url(#g%d)"/>'
            '<path d="%s" fill="none" stroke="%s" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg>') % (w,h,w,h, g, color,color, fd,g, d,color)

# ── HTML ──────────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0f1117;--sb:#13151e;--card:#1a1d27;--card2:#1f2233;--bdr:#252a3a;--tx:#e8eaf0;--sec:#8b90a7;--mt:#4a5068;--gr:#00c98d;--rd:#ff4d6a;--am:#f5a623;--bl:#4d9fff;--r:10px;--g:14px}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;min-height:100vh}
.topbar{background:var(--sb);border-bottom:1px solid var(--bdr);padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:56px;position:sticky;top:0;z-index:100}
.logo{font-size:16px;font-weight:700}
.tr{display:flex;align-items:center;gap:10px}
.lp{display:flex;align-items:center;gap:5px;background:rgba(0,201,141,.1);border:1px solid rgba(0,201,141,.25);border-radius:20px;padding:4px 10px;font-size:11px;color:var(--gr);font-weight:600}
.dot{width:6px;height:6px;background:var(--gr);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.rbtn{display:flex;align-items:center;gap:5px;background:var(--gr);color:#000;border:none;border-radius:20px;padding:6px 14px;font-size:12px;font-weight:700;cursor:pointer;transition:all .2s}
.rbtn:hover{background:#00b07a;transform:scale(1.03)}
.rbtn:disabled{background:#1a2a20;color:var(--mt);cursor:not-allowed;transform:none}
.spin{display:inline-block;animation:spin 1s linear infinite}
@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
.ts{font-size:11px;color:var(--sec)}
.ibar{display:flex;overflow-x:auto;background:var(--sb);border-bottom:1px solid var(--bdr);padding:0 24px}
.ic{padding:10px 24px 10px 0;margin-right:24px;border-right:1px solid var(--bdr);flex-shrink:0}
.ic:last-child{border-right:none}
.in{font-size:11px;color:var(--sec);margin-bottom:2px}
.ip{font-size:14px;font-weight:600}
.ich{font-size:12px;font-weight:500;margin-top:1px}
.layout{display:grid;grid-template-columns:280px 1fr;min-height:calc(100vh - 90px)}
.sidebar{background:var(--sb);border-right:1px solid var(--bdr);padding:16px 0;overflow-y:auto}
.sbs{padding:0 16px;margin-bottom:20px}
.sbt{font-size:11px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px;padding:0 4px}
.sbi{display:flex;justify-content:space-between;align-items:center;padding:8px 4px;border-radius:8px;cursor:pointer;transition:background .15s}
.sbi:hover{background:var(--card2)}
.sl{display:flex;flex-direction:column;gap:2px}
.ss{font-size:13px;font-weight:600;color:var(--tx)}
.sn{font-size:11px;color:var(--sec)}
.sr{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.sp{font-size:13px;font-weight:600}
.spc{font-size:11px;font-weight:500}
.main{padding:20px 24px;overflow-y:auto}
.mt2{font-size:20px;font-weight:700;margin-bottom:4px}
.ms{font-size:12px;color:var(--sec);margin-bottom:18px}
.krow{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--g);margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:14px 16px}
.kl{font-size:11px;color:var(--sec);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.kv{font-size:24px;font-weight:700;letter-spacing:-.5px}
.ks{font-size:11px;color:var(--sec);margin-top:3px}
.wg{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:var(--g);margin-bottom:20px}
.wc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:14px 16px;cursor:pointer;transition:border-color .2s,transform .15s}
.wc:hover{border-color:#4a5068;transform:translateY(-1px)}
.wct{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.wcs{font-size:15px;font-weight:700}
.wcn{font-size:11px;color:var(--sec);margin-top:1px}
.wcse{font-size:10px;color:var(--mt);margin-top:2px}
.wcp{font-size:20px;font-weight:700;letter-spacing:-.5px;margin-bottom:3px}
.wcch{font-size:12px;font-weight:500;margin-bottom:8px}
.wcm{display:flex;gap:5px;flex-wrap:wrap}
.wctg{font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid;font-weight:600}
.nc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);overflow:hidden;margin-bottom:20px}
.nh{padding:12px 16px;border-bottom:1px solid var(--bdr);font-size:12px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.06em}
.nr{display:grid;grid-template-columns:120px 1fr 90px;gap:10px;align-items:center;padding:11px 16px;border-bottom:1px solid var(--bdr);transition:background .15s}
.nr:last-child{border-bottom:none}
.nr:hover{background:var(--card2)}
.nll{display:flex;flex-direction:column;gap:3px}
.nsym{font-size:11px;font-weight:700;color:var(--bl)}
.nsnt{font-size:10px;font-weight:600}
.ntitle{font-size:12px;color:var(--tx);line-height:1.45}
.ntitle a{color:var(--tx);text-decoration:none}
.ntitle a:hover{color:var(--bl)}
.ndate{font-size:11px;color:var(--mt);text-align:right}
.cr{display:grid;grid-template-columns:1fr 1fr;gap:var(--g);margin-bottom:20px}
.cc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px}
.ctit{font-size:12px;font-weight:600;color:var(--sec);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}
.ch{height:200px;position:relative}
.footer{background:var(--sb);border-top:1px solid var(--bdr);padding:14px 24px;font-size:11px;color:var(--mt);text-align:center;line-height:1.7}
@media(max-width:900px){.layout{grid-template-columns:1fr}.sidebar{display:none}.krow,.cr{grid-template-columns:repeat(2,1fr)}.wg{grid-template-columns:repeat(2,1fr)}.nr{grid-template-columns:1fr}}
"""

def generate_html(quotes, news_items, indices, now):
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%I:%M %p MYT")

    # Index bar
    idx_map = {"^GSPC":"S&P 500","^IXIC":"Nasdaq","^DJI":"Dow Jones","^VIX":"VIX"}
    idx_html = ""
    for sym, name in idx_map.items():
        q = indices.get(sym, {})
        p = q.get("price", 0); pct = q.get("changesPercentage", 0)
        c = "#00c98d" if pct >= 0 else "#ff4d6a"; a = "▲" if pct >= 0 else "▼"
        idx_html += '<div class="ic"><div class="in">%s</div><div class="ip">%.2f</div><div class="ich" style="color:%s">%s %.2f%%</div></div>' % (name, p, c, a, abs(pct))

    # Sidebar
    sidebar = ""
    for sym in TICKERS:
        q = quotes.get(sym, {}); p = q.get("price",0); pct = q.get("changesPercentage",0)
        c = "#00c98d" if pct>=0 else "#ff4d6a"; a = "▲" if pct>=0 else "▼"
        nm = COMPANY_NAMES.get(sym,"")[:20]
        sidebar += ('<div class="sbi"><div class="sl"><span class="ss">%s</span><span class="sn">%s</span></div>'
                    '<div class="sr"><span class="sp" style="color:%s">$%.2f</span>'
                    '<span class="spc" style="color:%s">%s %.2f%%</span></div></div>') % (sym, nm, c, p, c, a, abs(pct))

    # Watch cards
    cards = ""
    for sym in TICKERS:
        q = quotes.get(sym,{}); p = q.get("price",0); pct = q.get("changesPercentage",0); chg = q.get("change",0)
        an = ANALYST_DATA.get(sym,{}); tgt = an.get("targetConsensus")
        up = ("+%.1f%%" % ((tgt-p)/p*100)) if tgt and p else "—"
        act, ac, rsn = get_action(sym, p, an)
        c = "#00c98d" if pct>=0 else "#ff4d6a"; a = "▲" if pct>=0 else "▼"
        rat = an.get("rating","N/A"); rc = "#00c98d" if rat=="Buy" else "#f5a623" if rat=="Hold" else "#7a8096"
        uc = "#00c98d" if up.startswith("+") else "#ff4d6a"
        spark = sparkline(pct, c)
        nm = COMPANY_NAMES.get(sym,sym); sec = SECTORS.get(sym,"Other")
        cards += ('<div class="wc"><div class="wct"><div>'
                  '<div class="wcs">%s</div><div class="wcn">%s</div><div class="wcse">%s</div>'
                  '</div><div>%s</div></div>'
                  '<div class="wcp">$%.2f</div>'
                  '<div class="wcch" style="color:%s">%s %.2f%% ($%.2f)</div>'
                  '<div class="wcm">'
                  '<span class="wctg" style="color:%s;border-color:%s33;background:%s22">%s</span>'
                  '<span class="wctg" style="color:%s;border-color:%s33;background:%s22" title="%s">%s</span>'
                  '<span class="wctg" style="color:%s">%s</span>'
                  '</div></div>') % (sym, nm, sec, spark, p, c, a, abs(pct), abs(chg),
                                     rc,rc,rc,rat, ac,ac,ac,rsn,act, uc,up+" upside")

    # News
    news_html = ""
    for n in news_items[:12]:
        s = n.get("symbol",""); t = n.get("title",""); d = n.get("publishedDate","")[:10]; u = n.get("url","#")
        snt, sc, sa = sentiment(t)
        news_html += ('<div class="nr"><div class="nll"><span class="nsym">%s</span>'
                      '<span class="nsnt" style="color:%s">%s %s</span></div>'
                      '<div class="ntitle"><a href="%s" target="_blank">%s</a></div>'
                      '<div class="ndate">%s</div></div>') % (s, sc, sa, snt, u, t, d)

    # Chart data
    sm = {}
    for sym in TICKERS:
        k = SECTORS.get(sym,"Other"); sm[k] = sm.get(k,0)+1
    sl = json.dumps(list(sm.keys())); sc2 = json.dumps(list(sm.values()))
    asy = [s for s in TICKERS if ANALYST_DATA[s]['buy']>0 or ANALYST_DATA[s]['hold']>0]
    ab  = json.dumps([ANALYST_DATA[s]['strongBuy']+ANALYST_DATA[s]['buy'] for s in asy])
    ah  = json.dumps([ANALYST_DATA[s]['hold'] for s in asy])
    ase = json.dumps([ANALYST_DATA[s]['sell'] for s in asy])
    asy = json.dumps(asy)

    w = sum(1 for s in TICKERS if quotes.get(s,{}).get("changesPercentage",0)>0)
    l = sum(1 for s in TICKERS if quotes.get(s,{}).get("changesPercentage",0)<0)
    tq = max(TICKERS, key=lambda s: abs(quotes.get(s,{}).get("changesPercentage",0)), default="—")
    tp = quotes.get(tq,{}).get("changesPercentage",0)
    tc = "#00c98d" if tp>=0 else "#ff4d6a"

    js = """
const sc=['#a78bfa','#4d9fff','#7f77dd','#00c98d','#f5a623','#ff4d6a'];
new Chart(document.getElementById('donut'),{type:'doughnut',data:{labels:"""+sl+""",datasets:[{data:"""+sc2+""",backgroundColor:sc,borderColor:'#0f1117',borderWidth:3,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{legend:{position:'right',labels:{color:'#8b90a7',font:{size:10},boxWidth:10,padding:8}}}}});
new Chart(document.getElementById('analyst'),{type:'bar',data:{labels:"""+asy+""",datasets:[{label:'Buy',data:"""+ab+""",backgroundColor:'rgba(0,201,141,.8)',borderRadius:3},{label:'Hold',data:"""+ah+""",backgroundColor:'rgba(245,166,35,.8)',borderRadius:3},{label:'Sell',data:"""+ase+""",backgroundColor:'rgba(255,77,106,.8)',borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b90a7',font:{size:10},boxWidth:10}}},scales:{x:{stacked:true,grid:{display:false},ticks:{color:'#8b90a7',font:{size:10}}},y:{stacked:true,grid:{color:'rgba(37,42,58,.8)'},ticks:{color:'#8b90a7',font:{size:10}}}}}});
async function triggerRefresh(){
  const btn=document.getElementById('rb');
  btn.disabled=true;btn.innerHTML='<span class="spin">🔄</span> Refreshing...';
  try{
    const token=prompt('Paste your GitHub Personal Access Token:');
    if(!token){btn.disabled=false;btn.innerHTML='🔄 Refresh';return;}
    const r=await fetch('https://api.github.com/repos/"""+GITHUB_REPO+"""/actions/workflows/daily-briefing.yml/dispatches',{method:'POST',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'},body:JSON.stringify({ref:'main'})});
    if(r.status===204){btn.innerHTML='⏳ Wait 30s';setTimeout(()=>{btn.innerHTML='✅ Reload now!';btn.disabled=false;},35000);}
    else{btn.innerHTML='❌ Check token';setTimeout(()=>{btn.innerHTML='🔄 Refresh';btn.disabled=false;},3000);}
  }catch(e){btn.innerHTML='❌ Error';setTimeout(()=>{btn.innerHTML='🔄 Refresh';btn.disabled=false;},3000);}
}
"""

    parts = [
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Jordan Market Briefing — ', now.strftime('%d %b %Y'), '</title>',
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" crossorigin="anonymous"></script>',
        '<style>', CSS, '</style></head><body>',
        '<div class="topbar"><div class="logo">📊 Jordan\'s Market Briefing</div>',
        '<div class="tr"><div class="ts">', date_str, ' · ', time_str, '</div>',
        '<div class="lp"><div class="dot"></div>LIVE</div>',
        '<button class="rbtn" id="rb" onclick="triggerRefresh()">🔄 Refresh</button></div></div>',
        '<div class="ibar">', idx_html, '</div>',
        '<div class="layout">',
        '<div class="sidebar"><div class="sbs"><div class="sbt">Watchlist</div>', sidebar, '</div></div>',
        '<div class="main">',
        '<div class="mt2">Good Morning, Jordan! 👋</div>',
        '<div class="ms">Your market snapshot for ', date_str, '</div>',
        '<div class="krow">',
        '<div class="kpi"><div class="kl">Winners Today</div><div class="kv" style="color:#00c98d">', str(w), '</div><div class="ks">stocks up</div></div>',
        '<div class="kpi"><div class="kl">Losers Today</div><div class="kv" style="color:#ff4d6a">', str(l), '</div><div class="ks">stocks down</div></div>',
        '<div class="kpi"><div class="kl">Biggest Mover</div><div class="kv" style="color:', tc, ';font-size:18px">', tq, ' ', '%+.2f%%' % tp, '</div><div class="ks">largest move</div></div>',
        '<div class="kpi"><div class="kl">Advisor Alerts</div><div class="kv" style="color:#f5a623">↓ Below</div><div class="ks">check actions</div></div>',
        '</div>',
        '<div style="font-size:12px;font-weight:600;color:#8b90a7;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Your Watchlist</div>',
        '<div class="wg">', cards, '</div>',
        '<div class="cr">',
        '<div class="cc"><div class="ctit">Sector Concentration</div><div class="ch"><canvas id="donut"></canvas></div></div>',
        '<div class="cc"><div class="ctit">Analyst Consensus</div><div class="ch"><canvas id="analyst"></canvas></div></div>',
        '</div>',
        '<div class="nc"><div class="nh">📰 Latest News</div>', news_html, '</div>',
        '</div></div>',
        '<div class="footer">🤖 Auto-generated by Jordan\'s AI Financial Advisor · Data via FMP · Updates weekdays 9:00 AM MYT<br>⚠️ Not financial advice.</div>',
        '<script>', js, '</script></body></html>'
    ]
    return "".join(parts)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    now     = datetime.now(MYT)
    print("[%s] Starting..." % now.strftime('%Y-%m-%d %H:%M MYT'))
    quotes  = fetch_quotes();  print("  quotes:", len(quotes))
    news    = fetch_news();    print("  news:",   len(news))
    indices = fetch_indices(); print("  indices:",len(indices))
    html    = generate_html(quotes, news, indices, now)
    out     = Path("docs"); out.mkdir(exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    print("  Saved docs/index.html")
    print("Done! ✅")

if __name__ == "__main__":
    main()
