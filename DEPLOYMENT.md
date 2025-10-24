# 🚀 Complete Deployment Guide

## 📋 Pre-Deployment Checklist

- [ ] Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather)
- [ ] Gemini API Keys obtained from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] GitHub account created
- [ ] Railway account created (sign up at [railway.app](https://railway.app))

---

## 🔑 Step 1: Get Required Tokens

### 1.1 Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name: `Ultimate Chemistry Bot`
4. Choose a username: `your_chemistry_bot` (must end in 'bot')
5. Copy the token (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2 Gemini API Keys

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Select project or create new
4. Copy the key (format: `AIzaSy...`)
5. Repeat to create 3-5 keys for rotation

---

## 📁 Step 2: Prepare Your Repository

### 2.1 Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click "New Repository"
3. Name: `chemistry-bot` (or your choice)
4. Description: "AI-powered chemistry problem solver"
5. Choose "Public" or "Private"
6. **DO NOT** initialize with README (we have our own)
7. Click "Create repository"

### 2.2 Clone and Setup

```bash
# Navigate to your project folder
cd /path/to/your/project

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Chemistry bot"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/chemistry-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2.3 Verify Files on GitHub

Ensure these files are visible:
- ✅ ULTIMATE_JE.py
- ✅ requirements.txt
- ✅ runtime.txt
- ✅ Procfile
- ✅ Aptfile
- ✅ nixpacks.toml
- ✅ railway.json
- ✅ .gitignore
- ✅ README.md
- ✅ LICENSE

---

## 🚂 Step 3: Deploy on Railway

### 3.1 Connect GitHub

1. Go to [railway.app](https://railway.app)
2. Click "Login" → Choose "GitHub"
3. Authorize Railway to access your repositories

### 3.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `chemistry-bot` repository
4. Railway will automatically:
   - Detect Python project
   - Read `nixpacks.toml`
   - Install dependencies
   - Start the bot

### 3.3 Monitor Deployment

Watch the build logs:
```
[nixpacks] Installing python311, cairo, pango...
[nixpacks] Running: pip install -r requirements.txt
[nixpacks] Installing python-telegram-bot...
[nixpacks] Installing weasyprint...
[build] ✅ Build successful
[deploy] Starting: python ULTIMATE_JE.py
[app] 🔬 ULTIMATE CHEMISTRY BOT - STARTUP
[app] ✅ Bot ready!
```

**Deployment time:** 3-5 minutes (first time)

---

## 🔧 Step 4: Configure Environment Variables

### 4.1 Add Variables in Railway

1. Go to your project dashboard
2. Click "Variables" tab
3. Click "New Variable"
4. Add each variable:

```
BOT_TOKEN = 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_KEY_1 = AIzaSyBWQEmryVqkUnP3t4iFNl5plli35CoGOEQ
GEMINI_KEY_2 = AIzaSyC7uXsCyD24g49LJE2XIcOKUNoNWdmzHdc
GEMINI_KEY_3 = AIzaSyCXCI8-Qvzm2q9M0nUupuApfwFW6W1x2-A
GEMINI_KEY_4 = AIzaSyBjPZulnxVYYpo2pRcgNQb6rJGHb4-H698
GEMINI_KEY_5 = AIzaSyATmG9i_yiRNGIgzAQWz7nPNsAQgdXN6hA
```

5. Click "Save"

### 4.2 Update Code to Use Environment Variables

Open `ULTIMATE_JE.py` and replace the configuration section:

```python
# OLD (Hardcoded):
BOT_TOKEN = "8466654130:AAE2MLI9nR6Bg5R5wLh4jH43t7TgyoNyTpA"

# NEW (Environment variables):
import os
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_fallback_token")

# OLD (Hardcoded API keys):
GEMINI_API_KEYS = [
    "AIzaSyBWQEmryVqkUnP3t4iFNl5plli35CoGOEQ",
    # ...
]

# NEW (Environment variables):
GEMINI_API_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
    os.getenv("GEMINI_KEY_5"),
]
# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
```

6. Commit and push changes:
```bash
git add ULTIMATE_JE.py
git commit -m "Use environment variables for tokens"
git push
```

7. Railway will auto-redeploy

---

## 💾 Step 5: Setup Persistent Storage (Optional but Recommended)

### 5.1 Why Persistent Storage?

Without it, `chemistry_knowledge_cache.json` is deleted on every restart.

### 5.2 Add Volume

1. Railway Dashboard → Your Project
2. Click "Settings" tab
3. Scroll to "Volumes"
4. Click "New Volume"
5. Mount path: `/app/data`
6. Click "Add"

### 5.3 Update Cache Path

In `ULTIMATE_JE.py`, change:

```python
# OLD:
CHEMISTRY_CACHE_FILE = "chemistry_knowledge_cache.json"

# NEW:
CHEMISTRY_CACHE_FILE = os.getenv(
    "CACHE_FILE_PATH",
    "/app/data/chemistry_knowledge_cache.json"
)

# Create directory if needed
os.makedirs(os.path.dirname(CHEMISTRY_CACHE_FILE), exist_ok=True)
```

Commit and push.

---

## ✅ Step 6: Test Your Bot

### 6.1 Check Deployment Status

In Railway:
- Status should show "Active" (green)
- Logs should show: `✅ Bot ready!`

### 6.2 Test in Telegram

1. Open Telegram
2. Search for your bot username (e.g., `@your_chemistry_bot`)
3. Send `/start`
4. Expected response:
```
🔬 ULTIMATE CHEMISTRY BOT

Triple-Strategy | 98-99% Accuracy
📚 GitHub Knowledge: ⏳ Loading...

📸 Send chemistry problem photo
⏱️ Analysis: 3-8 minutes

MS Chouhan + Bruice + GitHub DB
```

### 6.3 Test Image Analysis

1. Send a clear photo of a chemistry problem
2. Bot responds:
```
🔬 ANALYSIS STARTED

📸 Image received
🌐 Loading knowledge...

Please wait...
```

3. Wait 2-8 minutes
4. Receive PDF solution

---

## 🔍 Step 7: Monitor and Debug

### 7.1 View Logs

Railway Dashboard → Deployments → View Logs

Key log messages:
```
📂 Loaded cache: 6 sections
✅ Downloaded! Total: 6 sections
✅ Solution generated (5247 chars)
✅ Delivered in 245s
```

### 7.2 Common Issues

**Issue:** Build fails with "cairo not found"
```
Solution: Ensure Aptfile and nixpacks.toml are present
```

**Issue:** Bot doesn't respond
```
Solution: Check BOT_TOKEN is correct in Railway Variables
```

**Issue:** "API key invalid" error
```
Solution: Verify GEMINI_KEY_X values are correct
```

**Issue:** Out of memory
```
Solution: 
- Upgrade Railway plan (Hobby: 8GB RAM)
- Or optimize image sizes in code
```

### 7.3 View Metrics

Railway Dashboard → Metrics:
- CPU usage
- Memory usage
- Network traffic

---

## 🔄 Step 8: Updates and Maintenance

### 8.1 Push Updates

```bash
# Make changes to code
vim ULTIMATE_JE.py

# Commit
git add .
git commit -m "Update: improved PDF formatting"

# Push
git push

# Railway auto-deploys in 1-2 minutes
```

### 8.2 Rollback if Needed

Railway Dashboard → Deployments → Select previous deployment → Rollback

### 8.3 Monitor API Usage

- Telegram: Check Bot Father for message count
- Gemini: Check [Google AI Studio](https://makersuite.google.com) for quota

---

## 💰 Step 9: Cost Estimation

### Railway Plans

| Plan | Price | RAM | Features |
|------|-------|-----|----------|
| Free | $0 | 512MB | Good for testing |
| Hobby | $5/mo | 8GB | Recommended |
| Pro | $20/mo | 32GB | High traffic |

### Gemini API

- Free tier: 60 requests/minute
- Each analysis = 1 request
- Sufficient for 3,600 problems/hour

### Total Monthly Cost

- Hobby Railway: $5
- Gemini API: $0 (free tier)
- **Total: $5/month**

---

## 🎯 Step 10: Production Checklist

Before going live:

- [ ] Environment variables configured
- [ ] Persistent storage enabled
- [ ] Logs showing "Bot ready"
- [ ] Test `/start` command works
- [ ] Test image analysis works
- [ ] PDF generation works
- [ ] Response time acceptable (2-8 min)
- [ ] Error handling tested
- [ ] API keys rotated if exposed
- [ ] README.md updated with your info

---

## 📞 Support Resources

### Railway
- Docs: [docs.railway.app](https://docs.railway.app)
- Discord: [discord.gg/railway](https://discord.gg/railway)
- Status: [railway.statuspage.io](https://railway.statuspage.io)

### Telegram Bots
- Docs: [core.telegram.org/bots](https://core.telegram.org/bots)
- API: [core.telegram.org/bots/api](https://core.telegram.org/bots/api)

### Gemini API
- Docs: [ai.google.dev](https://ai.google.dev)
- Studio: [makersuite.google.com](https://makersuite.google.com)

---

## 🎉 Success!

Your bot is now live! Share with friends:

```
🔬 Try my Chemistry Bot!
@your_chemistry_bot

✅ 98-99% Accuracy
✅ Triple-Strategy Analysis
✅ Beautiful PDF Reports
✅ JEE Advanced Focused
```

---

**Questions?** Open an issue on GitHub or check Railway logs.
