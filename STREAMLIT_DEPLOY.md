# Streamlit Cloud Deployment Guide
## Quick Deploy to Streamlit Cloud

**Time to Deploy:** 15-30 minutes

---

## ✅ Pre-Deployment Checklist

Before pushing to GitHub, verify:

- [x] **.gitignore is configured** - No secrets will be committed
- [x] **config.py reads from Streamlit secrets** - Works both locally and in cloud
- [x] **requirements.txt is complete** - All dependencies listed
- [x] **main.py runs locally** - Test with `streamlit run main.py`
- [ ] **Groq API key ready** - Get from https://console.groq.com/

---

## Step 1: Get Groq API Key

1. Go to https://console.groq.com/
2. Sign up or log in
3. Click **"API Keys"** in sidebar
4. Click **"Create API Key"**
5. Copy the key (starts with `gsk_...`)
6. **Save it somewhere safe** (you'll need it in Step 4)

**Cost:** Free tier available (14,400 requests/day)

---

## Step 2: Push to GitHub

### Option A: First Time Push

```bash
# Navigate to project folder
cd C:\Users\safix\Desktop\rag_langgraph

# Initialize git (if not already done)
git init

# Add all files (secrets are excluded by .gitignore)
git add .

# Commit
git commit -m "Initial commit: RAG Contract Analysis System"

# Create repository on GitHub (github.com/new)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/rag-contract-analysis.git
git branch -M main
git push -u origin main
```

### Option B: Update Existing Repository

```bash
cd C:\Users\safix\Desktop\rag_langgraph

# Add changes
git add .

# Commit
git commit -m "Update: Ready for Streamlit Cloud deployment"

# Push
git push origin main
```

### ⚠️ IMPORTANT: Verify No Secrets Committed

After pushing, check your GitHub repository:

```bash
# Check what was pushed
git log --oneline -5
```

Go to https://github.com/YOUR_USERNAME/rag-contract-analysis and verify:
- ❌ `.env` file is NOT visible
- ❌ `chroma_db/` folder is NOT visible
- ❌ `.streamlit/secrets.toml` is NOT visible
- ✅ `main.py`, `config.py`, `requirements.txt` ARE visible

---

## Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit https://share.streamlit.io/
   - Click **"Sign in"** (use GitHub account)

2. **Authorize Streamlit:**
   - Click **"Authorize Streamlit"**
   - Grant access to your GitHub repositories

3. **Create New App:**
   - Click **"New app"** button
   - Select:
     - **Repository:** `YOUR_USERNAME/rag-contract-analysis`
     - **Branch:** `main`
     - **Main file path:** `main.py`
   - Click **"Deploy!"**

4. **Wait for Deployment:**
   - Streamlit will install dependencies (2-5 minutes)
   - You'll see build logs
   - **It will fail first** because secrets are missing (expected!)

---

## Step 4: Add Secrets (API Key)

1. **Click "Settings" (⚙️ icon)** in your app dashboard

2. **Click "Secrets"** tab

3. **Paste your Groq API key:**
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```

4. **Click "Save"**

5. **App will automatically restart** and should work now!

---

## Step 5: Test Your Deployed App

1. **Access your app:**
   - URL: `https://YOUR_APP_NAME.streamlit.app`
   - Example: `https://rag-contract-analysis.streamlit.app`

2. **Upload a test contract:**
   - Click "Browse files"
   - Upload a PDF or Excel file
   - Click "Process Documents"

3. **Ask a question:**
   - Type in chat: "What are the payment terms?"
   - Verify you get a response

4. **If it works** → Done! 🎉

---

## Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Solution:**
1. Go to app Settings → Secrets
2. Make sure you have:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
3. No quotes around the key itself, but quotes around the value
4. Click "Save" and wait for restart

### Issue: "Module not found" errors

**Solution:**
1. Check `requirements.txt` includes all dependencies
2. Push updated `requirements.txt` to GitHub
3. App will automatically rebuild

### Issue: App is slow or crashes

**Solution:**
1. Streamlit free tier has resource limits
2. Reduce `CHUNK_SIZE` in secrets:
   ```toml
   CHUNK_SIZE = "800"
   ```
3. Or upgrade to Streamlit Cloud Teams ($20/month)

### Issue: ChromaDB persistence not working

**Solution:**
- Streamlit Cloud apps restart frequently
- ChromaDB data in `./chroma_db/` is **ephemeral** (lost on restart)
- **This is expected** - users need to re-upload contracts after app restarts
- For persistent storage, use self-hosted deployment instead

---

## Optional: Custom Domain

To use your own domain (e.g., `contracts.yourcompany.com`):

1. **Upgrade to Streamlit Cloud Teams** ($20/month)
2. Go to Settings → General
3. Add custom domain
4. Update DNS records (follow Streamlit instructions)

---

## Optional: Add Authentication

To require login before access:

1. **Update code** (see `AUTHENTICATION_GUIDE.md`)
2. **Add user credentials to secrets:**
   ```toml
   [passwords]
   admin = "$2b$12$hashed_password_here"
   user1 = "$2b$12$another_hashed_password"
   ```
3. **Push to GitHub** and app will rebuild

---

## Security Notes

### ✅ What's Secure:

- API keys stored in Streamlit secrets (encrypted)
- No secrets in GitHub repository
- HTTPS encryption by default
- Streamlit manages infrastructure security

### ⚠️ What's NOT Secure:

- **Anyone with URL can access** (no authentication by default)
- **Data on third-party servers** (Streamlit's AWS)
- **ChromaDB data is ephemeral** (lost on restart)

### Recommendations:

1. **Don't share URL publicly** if contracts are sensitive
2. **Add authentication** (see `AUTHENTICATION_GUIDE.md`)
3. **For highly sensitive data**, use self-hosted deployment instead

---

## App Management

### Update Your App

```bash
# Make changes locally
# Test with: streamlit run main.py

# Commit and push
git add .
git commit -m "Update: description of changes"
git push origin main

# Streamlit Cloud auto-deploys (1-2 minutes)
```

### View Logs

1. Go to your app on share.streamlit.io
2. Click "Manage app"
3. Click "Logs" tab
4. See real-time application logs

### Pause/Delete App

1. Go to app dashboard
2. Click "⋮" (three dots)
3. Select "Pause app" or "Delete app"

---

## Cost Summary

| Item | Cost |
|------|------|
| **Streamlit Cloud (Free Tier)** | $0/month |
| **Groq API (Free Tier)** | $0/month (up to 14,400 requests/day) |
| **GitHub (Public Repository)** | $0 |
| **Total** | **$0/month** |

### If You Need More:

| Upgrade | Cost | Benefits |
|---------|------|----------|
| **Streamlit Cloud Teams** | $20/month | More resources, custom domain, priority support |
| **Groq Pay-as-you-go** | ~$0.10/1M tokens | Higher rate limits |

---

## Next Steps After Deployment

1. **Share URL** with team members
2. **Upload contracts** and test thoroughly
3. **Monitor usage** (check Streamlit dashboard)
4. **Add authentication** if needed (see `AUTHENTICATION_GUIDE.md`)
5. **Gather feedback** from users

---

## Support

### Streamlit Issues:
- Docs: https://docs.streamlit.io/
- Community: https://discuss.streamlit.io/
- Status: https://status.streamlit.io/

### Groq Issues:
- Docs: https://console.groq.com/docs
- Discord: https://discord.gg/groq

### This App Issues:
- Check logs in Streamlit dashboard
- Review `README.md` and `TECH_STACK.md`

---

## Quick Reference

### Streamlit Cloud URLs:
- **Dashboard:** https://share.streamlit.io/
- **Your app:** `https://YOUR_APP_NAME.streamlit.app`

### Common Commands:
```bash
# Test locally
streamlit run main.py

# Push updates
git add . && git commit -m "Update" && git push origin main

# Check deployment status
# (Go to share.streamlit.io and check app dashboard)
```

### Secrets Format:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```

---

**Deployment Complete!** 🚀

Your contract analysis system is now live and accessible from anywhere.
