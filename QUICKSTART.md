# ⚡ Quick Start Guide

Get your Chemistry Bot running in **10 minutes**!

---

## 📋 Prerequisites (2 minutes)

### 1. Get Telegram Bot Token
```
1. Open Telegram → Search @BotFather
2. Send: /newbot
3. Name: Ultimate Chemistry Bot
4. Username: your_chemistry_bot
5. Copy token: 1234567890:ABC...
```

### 2. Get Gemini API Key
```
1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy key: AIzaSy...
```

---

## 🚀 Option A: Deploy on Railway (5 minutes)

### Step 1: Push to GitHub
```bash
git clone https://github.com/YOUR_USERNAME/chemistry-bot.git
cd chemistry-bot

# Add your repository
git remote set-url origin https://github.com/YOUR_USERNAME/chemistry-bot.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Select `chemistry-bot` repository
4. Wait 3-5 minutes ☕

### Step 3: Add Environment Variables
```
Railway Dashboard → Variables → New Variable

BOT_TOKEN = your_telegram_token
GEMINI_KEY_1 = your_gemini_key
```

### Step 4: Test!
```
1. Open Telegram
2. Search: @your_chemistry_bot
3. Send: /start
4. Upload chemistry problem image
5. Wait 2-5 minutes
6. Receive PDF! 🎉
```

---

## 💻 Option B: Run Locally (3 minutes)

### Step 1: Install
```bash
git clone https://github.com/YOUR_USERNAME/chemistry-bot.git
cd chemistry-bot
pip install -r requirements.txt
```

### Step 2: Configure
Edit `ULTIMATE_JE.py`:
```python
BOT_TOKEN = "your_telegram_token"
GEMINI_API_KEYS = ["your_gemini_key"]
```

### Step 3: Run
```bash
python ULTIMATE_JE.py
```

### Step 4: Test
```
Telegram → @your_chemistry_bot → /start
```

---

## ✅ Verify It's Working

### Check 1: Bot Responds
```
You: /start
Bot: 🔬 ULTIMATE CHEMISTRY BOT
     Triple-Strategy | 98-99% Accuracy
     ...
```

### Check 2: Image Analysis
```
You: [Send chemistry image]
Bot: 🔬 ANALYSIS STARTED
     📸 Image received
     ...
```

### Check 3: PDF Received
```
Bot: ✅ Analysis complete!
     ⏱️ 245s
     📄 Chem_20250124_143022.pdf
```

---

## 🐛 Quick Troubleshooting

### Bot doesn't respond
```bash
# Check token
echo $BOT_TOKEN  # Railway
# Or check ULTIMATE_JE.py line 38

# Check Railway logs
Railway Dashboard → Deployments → View Logs
```

### "Invalid token" error
```
- Verify token from @BotFather
- Check no extra spaces
- Ensure token in environment variables (Railway)
```

### Build fails
```
- Ensure all files present:
  ✅ requirements.txt
  ✅ Procfile
  ✅ Aptfile
  ✅ nixpacks.toml
```

### PDF not generated
```bash
# Check WeasyPrint installed
pip list | grep weasyprint

# Check logs for errors
tail -f *.log  # Local
Railway → Logs  # Railway
```

---

## 📚 Next Steps

1. **Read Full Documentation**: [README.md](README.md)
2. **Configure Storage**: [DEPLOYMENT.md](DEPLOYMENT.md) - Step 5
3. **Customize Prompts**: Edit `build_enhanced_chemistry_prompt()` in code
4. **Monitor Usage**: Railway Dashboard → Metrics

---

## 🎯 Quick Commands

| Command | Action |
|---------|--------|
| `/start` | Welcome message |
| `/help` | Usage instructions |
| `/stats` | Knowledge base info |

---

## ⏱️ Expected Performance

- **First Request**: 30-90 seconds (downloads knowledge)
- **Subsequent**: 2-5 minutes (analysis + PDF)
- **Accuracy**: 98-99% (triple-strategy)

---

## 💰 Cost

- **Railway Hobby**: $5/month (recommended)
- **Gemini API**: Free (60 req/min)
- **Total**: $5/month

---

## 🆘 Need Help?

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/chemistry-bot/issues)
- **Docs**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🎉 Success Checklist

- [ ] Bot responds to `/start`
- [ ] Accepts image uploads
- [ ] Generates PDF solutions
- [ ] PDF opens correctly
- [ ] Solution is accurate
- [ ] Response time < 8 minutes

---

**Ready?** Start with Option A (Railway) for easiest deployment! 🚀
