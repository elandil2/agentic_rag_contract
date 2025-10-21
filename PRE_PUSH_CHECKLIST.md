# ⚠️ PRE-PUSH SECURITY CHECKLIST

**BEFORE PUSHING TO GITHUB, VERIFY THESE ITEMS:**

---

## ✅ Checklist

### 1. Verify .gitignore is Working

Run this command to see what will be committed:

```bash
git status
```

**MUST NOT see these files/folders:**
- ❌ `.env`
- ❌ `chroma_db/`
- ❌ `.streamlit/secrets.toml`
- ❌ `config_auth.yaml`
- ❌ `__pycache__/`
- ❌ `rag_env/`

**SHOULD see these files:**
- ✅ `main.py`
- ✅ `config.py`
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ Documentation files (.md)

### 2. Check for Accidental API Keys in Code

Search for your API key in code:

```bash
# Search for "gsk_" (Groq API key prefix)
grep -r "gsk_" . --exclude-dir=rag_env --exclude-dir=.git --exclude=.env

# Should return: No results (except in .env which is ignored)
```

**Windows PowerShell:**
```powershell
Select-String -Path .\*.py -Pattern "gsk_"

# Should return: No results
```

### 3. Verify Sensitive Files are Ignored

```bash
# Check .gitignore contains these lines
cat .gitignore | grep -E "\.env|chroma_db|secrets\.toml"
```

**Should output:**
```
.env
chroma_db/
.streamlit/secrets.toml
```

### 4. Test Git Add (Dry Run)

```bash
# See what WOULD be added (without actually adding)
git add --dry-run .

# Review output - NO .env, chroma_db/, or secrets.toml should appear
```

### 5. Double-Check Recent Commits

```bash
# If you already committed, check last commit
git log -1 --stat

# Make sure no .env or secret files in the commit
```

### 6. If You Accidentally Committed Secrets

**STOP! Don't push yet. Remove them first:**

```bash
# Remove file from last commit (keep file locally)
git rm --cached .env
git commit --amend -m "Remove .env from tracking"

# Or reset to previous commit
git reset HEAD~1
```

---

## 🔒 Final Verification Before Push

Run these commands:

```bash
# 1. Check git status
git status

# 2. List files to be pushed
git ls-files

# 3. Search for API keys in tracked files
git grep "gsk_"
# Should return nothing or only references to secrets.toml.example

# 4. Check .env is ignored
git check-ignore .env
# Should output: .env
```

---

## ✅ Safe to Push Checklist

Check all boxes before pushing:

- [ ] `.env` file is NOT in `git status` output
- [ ] `chroma_db/` folder is NOT in `git status` output
- [ ] `.streamlit/secrets.toml` is NOT in `git status` output
- [ ] `git grep "gsk_"` returns no results (or only in .example files)
- [ ] `git check-ignore .env` returns `.env`
- [ ] All code files (main.py, config.py) use `get_config()` function
- [ ] `secrets.toml.example` contains ONLY placeholder text

---

## 🚀 Ready to Push

Once all checks pass:

```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

---

## 🆘 Emergency: API Key Was Pushed

If you accidentally pushed your Groq API key:

1. **Immediately rotate the API key:**
   - Go to https://console.groq.com/
   - Delete the old API key
   - Create a new one

2. **Remove from Git history:**
   ```bash
   # Install BFG Repo Cleaner
   # Download from: https://rtyley.github.io/bfg-repo-cleaner/

   # Remove .env from entire history
   bfg --delete-files .env

   # Or use git filter-branch (slower)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (⚠️ CAUTION)
   git push origin --force --all
   ```

3. **Update new API key:**
   - Update `.env` locally with new key
   - Add to Streamlit Cloud secrets (Settings → Secrets)

---

## 📝 Post-Push Verification

After pushing, verify on GitHub:

1. Go to `https://github.com/YOUR_USERNAME/rag-contract-analysis`
2. Click on files and folders
3. Confirm:
   - ❌ `.env` is NOT visible
   - ❌ `chroma_db/` is NOT visible
   - ❌ `.streamlit/` folder is NOT visible
   - ✅ `.gitignore` IS visible and contains correct entries
   - ✅ `secrets.toml.example` IS visible (this is safe - it's just a template)

---

## 🔐 Security Summary

**Files that MUST BE ignored (.gitignore):**
- `.env` - Contains GROQ_API_KEY
- `chroma_db/` - Contains user-uploaded contract data
- `.streamlit/secrets.toml` - Contains production secrets
- `config_auth.yaml` - Contains user passwords (if using authentication)
- `rag_env/` - Virtual environment
- `__pycache__/` - Python cache

**Files that are SAFE to commit:**
- `main.py` - Application code (no secrets)
- `config.py` - Configuration code (reads from env/secrets, no hardcoded keys)
- `requirements.txt` - Dependencies list
- `.gitignore` - Git ignore rules
- `secrets.toml.example` - Template with placeholders only
- All `.md` files - Documentation

---

**After completing this checklist, you're safe to push to GitHub! 🚀**
