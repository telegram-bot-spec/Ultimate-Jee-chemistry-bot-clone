# 🔧 Troubleshooting Guide

Common issues and solutions for Ultimate Chemistry Bot.

---

## 🚫 Bot Not Responding

### Symptom
Bot doesn't reply to `/start` or any commands.

### Solutions

#### Check 1: Bot Token
```bash
# Railway
Railway Dashboard → Variables → Check BOT_TOKEN

# Local
grep "BOT_TOKEN" ULTIMATE_JE.py
```

**Fix**: Ensure token is correct (format: `1234567890:ABC...`)

#### Check 2: Bot Running
```bash
# Railway
Dashboard → Deployments → Status should be "Active"

# Local
ps aux | grep ULTIMATE_JE.py
```

**Fix**: Restart bot if crashed

#### Check 3: Logs
```bash
# Railway
Dashboard → Deployments → View Logs → Look for:
✅ Bot ready!

# Local
tail -f *.log
```

**Fix**: Check error messages in logs

---

## 🖼️ Image Upload Issues

### Symptom
Bot receives image but crashes or doesn't respond.

### Solutions

#### Check 1: Image Size
```
Max recommended: 10MB
Bot enhances to max 2048px
```

**Fix**: Compress image before sending

#### Check 2: Image Format
```
Supported: JPG, PNG, WEBP
Not supported: HEIC, GIF, BMP
```

**Fix**: Convert to JPG/PNG

#### Check 3: Memory
```bash
# Railway
Dashboard → Metrics → Memory usage

Free tier: 512MB (may be too low)
Hobby tier: 8GB (recommended)
```

**Fix**: Upgrade Railway plan

---

## 📄 PDF Generation Fails

### Symptom
Bot analyzes but crashes when generating PDF.

### Solutions

#### Check 1: WeasyPrint Dependencies
```bash
# Local - Install system packages
# Ubuntu/Debian:
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0

# Railway - Check Aptfile exists:
cat Aptfile
```

**Fix**: Ensure `Aptfile` is committed

#### Check 2: Solution Text
```
Error: "NoneType has no attribute 'split'"
Cause: Empty solution from Gemini
```

**Fix**: Check Gemini API logs, retry with different image

#### Check 3: Encoding Issues
```
Error: "codec can't encode character"
Cause: Special characters in solution
```

**Fix**: Already handled in `format_chemistry_html()`, update if needed

---

## 🔑 API Key Issues

### Symptom
"API key invalid" or "Quota exceeded" errors.

### Solutions

#### Check 1: Gemini API Key Format
```
Correct: AIzaSy... (39 characters)
Incorrect: Missing characters or extra spaces
```

**Fix**: Verify key from [Google AI Studio](https://makersuite.google.com/app/apikey)

#### Check 2: Key Rotation
```python
# Bot cycles through 5 keys automatically
current_key_index = 0  # Check this in logs

# Log message:
Using API Key #1
```

**Fix**: Add more keys if all exhausted

#### Check 3: Quota
```
Free tier: 60 requests/minute
Each analysis: 1 request
```

**Fix**: Wait 1 minute, or upgrade API plan

---

## 🌐 Knowledge Base Issues

### Symptom
"Knowledge base not loaded" or slow first request.

### Solutions

#### Check 1: Network Access
```bash
# Test GitHub connectivity
curl https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/functional_groups/functional_groups.json

# Should return JSON
```

**Fix**: Check firewall/network settings

#### Check 2: Cache File
```bash
# Check if cache exists
ls -la chemistry_knowledge_cache.json

# Check contents
cat chemistry_knowledge_cache.json | jq 'keys'
```

**Fix**: Delete cache and let bot re-download
```bash
rm chemistry_knowledge_cache.json
```

#### Check 3: Persistent Storage (Railway)
```
Without volume: Cache lost on restart
With volume: Cache persists
```

**Fix**: Add volume at `/app/data` in Railway

---

## 🚀 Railway Deployment Issues

### Symptom
Build fails or bot crashes on Railway.

### Solutions

#### Check 1: Build Logs
```
Common errors:
- "cairo not found" → Missing Aptfile
- "No module named 'weasyprint'" → requirements.txt issue
- "Command not found: python" → Missing runtime.txt
```

**Fix**: Ensure all config files exist:
```
✅ requirements.txt
✅ runtime.txt
✅ Procfile
✅ Aptfile
✅ nixpacks.toml
```

#### Check 2: Start Command
```bash
# Procfile should contain:
web: python ULTIMATE_JE.py
```

**Fix**: Ensure filename matches exactly

#### Check 3: Resource Limits
```
Free tier: 512MB RAM (often insufficient)
Hobby tier: 8GB RAM (recommended)
```

**Fix**: Upgrade plan

---

## ⏱️ Timeout Issues

### Symptom
Bot takes too long (> 10 minutes) or times out.

### Solutions

#### Check 1: Image Complexity
```
Simple diagram: 2-3 min
Complex multi-step: 5-8 min
Handwritten messy: 8-10 min
```

**Fix**: Send clearer images

#### Check 2: Gemini API Response Time
```python
# Check logs for:
logger.info(f"✅ Solution generated ({len(solution)} chars)")

# If this never appears, API is slow/stuck
```

**Fix**: Retry, or check [Gemini status](https://status.cloud.google.com/)

#### Check 3: PDF Generation Time
```python
# Check logs for:
await status.edit_text("📄 Generating PDF...")

# If stuck here, WeasyPrint issue
```

**Fix**: Check solution length, may be too long

---

## 💾 Memory Issues

### Symptom
"Out of memory" or bot crashes randomly.

### Solutions

#### Check 1: Railway Memory Usage
```
Dashboard → Metrics → Memory graph

Approaching limit? Upgrade plan
```

#### Check 2: Image Enhancement
```python
# In code, reduce max size:
if max(img.size) > 2048:  # Try 1024 instead
    ratio = 1024 / max(img.size)
```

#### Check 3: Cache Size
```bash
# Check cache file size
ls -lh chemistry_knowledge_cache.json

# If > 10MB, something is wrong
```

**Fix**: Delete and re-download cache

---

## 📊 Error Code Reference

| Error | Meaning | Fix |
|-------|---------|-----|
| 401 | Invalid API key | Check GEMINI_KEY_X |
| 403 | Forbidden | Check API quotas |
| 404 | Bot not found | Check BOT_TOKEN |
| 429 | Rate limit | Wait 1 minute |
| 500 | Server error | Retry, check status |
| 503 | Service unavailable | Wait, check status page |

---

## 🔍 Debug Mode

Enable detailed logging:

```python
# In ULTIMATE_JE.py, change:
logging.basicConfig(level=logging.DEBUG)  # Was INFO

# Restart bot
```

---

## 📝 Log Analysis

### Good Startup:
```
🔬 ULTIMATE CHEMISTRY BOT - STARTUP
📂 Checking cache...
✅ Using cached knowledge
✅ Sections: 6
✅ API Keys: 5
✅ Bot ready!
```

### Bad Startup:
```
🔬 ULTIMATE CHEMISTRY BOT - STARTUP
❌ Download error: ConnectionError
⚠️ Cache save error: PermissionError
```

---

## 🆘 Still Stuck?

### 1. Collect Information
```
- Error message (exact text)
- Railway/Local deployment
- Bot logs (last 50 lines)
- Image type and size
- Steps to reproduce
```

### 2. Open GitHub Issue
[Create Issue](https://github.com/YOUR_USERNAME/chemistry-bot/issues/new)

Include:
- Description
- Logs (remove sensitive info)
- Screenshots
- Expected vs actual behavior

### 3. Check Existing Issues
[Browse Issues](https://github.com/YOUR_USERNAME/chemistry-bot/issues)

Your problem may already be solved!

---

## ✅ Prevention Checklist

Before deploying:
- [ ] All tokens in environment variables
- [ ] All config files committed
- [ ] `.gitignore` includes cache files
- [ ] Railway plan sufficient (Hobby recommended)
- [ ] Test locally first
- [ ] Monitor logs during first run
- [ ] Test with sample image
- [ ] Verify PDF opens correctly

---

## 📞 Emergency Recovery

### Complete Reset:
```bash
# 1. Stop bot
Railway Dashboard → Settings → Stop

# 2. Clear variables
Variables → Delete all → Re-add

# 3. Clear cache
Volumes → Delete → Re-create

# 4. Redeploy
Settings → Redeploy

# 5. Monitor logs
Deployments → View Logs
```

---

**Remember**: Most issues are token/config related. Double-check environment variables first! 🔐
