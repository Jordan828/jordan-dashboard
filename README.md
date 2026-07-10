# 📊 Jordan's Daily Market Briefing — Setup Guide

Your personal AI-powered stock dashboard, delivered to WhatsApp every weekday at **9:00 AM Malaysia Time** — completely free.

---

## How It Works

```
Every weekday 9AM MYT
        ↓
GitHub Actions wakes up
        ↓
Fetches live prices + news from FMP
        ↓
Generates your HTML dashboard
        ↓
Sends WhatsApp summary via CallMeBot (free)
        ↓
Updates your live dashboard website
```

---

## ✅ Step-by-Step Setup (follow in order)

### STEP 1 — Create a GitHub Account
1. Go to **https://github.com** and sign up (free)
2. Remember your username — you'll need it later

---

### STEP 2 — Create Your Repository
1. Click the **+** button (top right) → **New repository**
2. Name it: `jordan-dashboard`
3. Set to **Public** (required for free GitHub Pages)
4. Click **Create repository**

---

### STEP 3 — Upload These Files
Upload all files from this folder into your new repository, keeping the same folder structure:
```
jordan-dashboard/
├── .github/
│   └── workflows/
│       └── daily-briefing.yml
├── scripts/
│   └── generate_and_send.py
├── docs/
│   └── index.html          ← upload your current dashboard here
└── README.md
```

To upload: In your GitHub repo, click **Add file → Upload files**

---

### STEP 4 — Get Your FMP API Key
1. Go to **https://financialmodelingprep.com**
2. Sign up for a free account
3. Go to **Dashboard → API Key**
4. Copy your API key

---

### STEP 5 — Set Up CallMeBot WhatsApp (FREE)
1. Add this contact to your phone's WhatsApp:
   - Name: `CallMeBot`
   - Number: **+34 644 86 24 12** (Spain number, don't worry)

2. Send this exact message to that contact on WhatsApp:
   ```
   I allow callmebot to send me messages
   ```

3. Within a minute, you'll receive a reply with your **API Key** — looks like: `1234567`

4. Save your:
   - **Phone number** (with country code, no + sign): e.g. `60123456789`
   - **CallMeBot API key**: e.g. `1234567`

---

### STEP 6 — Add Your Secret Keys to GitHub
1. In your GitHub repo, click **Settings** (top menu)
2. Click **Secrets and variables → Actions** (left sidebar)
3. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value |
|---|---|
| `FMP_API_KEY` | Your FMP API key from Step 4 |
| `CALLMEBOT_PHONE` | Your phone with country code e.g. `60123456789` |
| `CALLMEBOT_APIKEY` | Your CallMeBot API key from Step 5 |

---

### STEP 7 — Enable GitHub Pages (your live dashboard URL)
1. In your GitHub repo, click **Settings**
2. Click **Pages** (left sidebar)
3. Under **Source**, select: `Deploy from a branch`
4. Branch: `gh-pages` | Folder: `/ (root)`
5. Click **Save**

Your dashboard will be live at:
```
https://YOUR-GITHUB-USERNAME.github.io/jordan-dashboard/
```

---

### STEP 8 — Update Your Username in the Script
Open `scripts/generate_and_send.py` and find this line:
```python
f"📱 Full dashboard: https://YOUR-GITHUB-USERNAME.github.io/jordan-dashboard/"
```
Replace `YOUR-GITHUB-USERNAME` with your actual GitHub username.

---

### STEP 9 — Test It Manually
1. In your GitHub repo, click **Actions** (top menu)
2. Click **Jordan's Daily Market Briefing** (left sidebar)
3. Click **Run workflow → Run workflow**
4. Watch it run — within 1–2 minutes you should get a WhatsApp message! 🎉

---

## 📅 Schedule

The briefing runs automatically:
- **Every weekday (Mon–Fri) at 9:00 AM MYT**
- Skips weekends (markets are closed)
- You can also trigger it manually anytime via the Actions tab

---

## 🔧 Customise Your Watchlist

To add or remove stocks, edit `scripts/generate_and_send.py`:
```python
TICKERS = ["AAPL", "AIFF", "AMD", "INTC", "KEYS", "META", "MSFT", "MU", "NVDA", "PLTR"]
```
Just add or remove tickers from this list.

---

## 💡 Troubleshooting

| Problem | Fix |
|---|---|
| No WhatsApp received | Check CALLMEBOT_PHONE has no + sign |
| FMP data missing | Check FMP_API_KEY is correct |
| Dashboard not updating | Check Actions tab for error logs |
| WhatsApp message delayed | CallMeBot free tier may have ~5 min delay |

---

## 💰 Total Cost

| Service | Cost |
|---|---|
| GitHub (hosting + automation) | **FREE** |
| CallMeBot WhatsApp | **FREE** |
| FMP API (basic quotes + news) | **FREE** |
| **TOTAL** | **$0/month** |

---

*Built by your AI Financial Advisor · Not financial advice*
