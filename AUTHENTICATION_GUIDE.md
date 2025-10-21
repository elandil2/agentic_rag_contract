# Authentication & Multi-User Implementation Guide
## RAG Contract Analysis System

**Document Version:** 1.0
**Last Updated:** 2025-10-21
**Audience:** Developers, IT Team
**Purpose:** Add authentication and multi-user support for cloud deployment

---

## Overview

This guide shows how to add **username/password authentication** and **multi-user support** to the RAG Contract Analysis System for deployment to cloud platforms (Streamlit Cloud or self-hosted).

**⚠️ DO NOT implement this until you get approval from management/legal team.**

---

## Why Authentication?

### Without Authentication (Current State)
- Anyone with the URL can access the app
- No user isolation (everyone sees same chat history)
- No access control
- Not suitable for cloud deployment

### With Authentication
- ✅ Users must login with username/password
- ✅ Each user has separate chat history
- ✅ Access control (only authorized users)
- ✅ Audit trail (track who accessed what)
- ✅ Safe for cloud deployment

---

## Authentication Options

### Option 1: Simple Username/Password (Recommended for Start)
- **Pros:** Easy to implement (30 minutes), no external dependencies
- **Cons:** Passwords stored in code (okay for small teams)
- **Best for:** 5-10 users, quick deployment

### Option 2: Streamlit Authentication Component
- **Pros:** More secure, better UX
- **Cons:** Requires `streamlit-authenticator` library
- **Best for:** 10-50 users, professional deployment

### Option 3: SSO Integration (Advanced)
- **Pros:** Enterprise-grade, integrates with company Active Directory
- **Cons:** Complex setup, requires enterprise Streamlit Cloud
- **Best for:** 50+ users, large organizations

**This guide covers Option 1 and Option 2.**

---

## Option 1: Simple Authentication (Quick Setup)

### Step 1: Install Dependencies

Add to `requirements.txt`:
```txt
streamlit-authenticator==0.3.3
```

Then install:
```bash
pip install streamlit-authenticator==0.3.3
```

### Step 2: Create User Credentials File

Create `config_auth.yaml`:
```yaml
credentials:
  usernames:
    jsmith:
      name: John Smith
      password: $2b$12$KIXhs7qJ9YwJKRlhFfGfCO8LlRlYxN8dQw6WJX8HvZGZJHqWjQXWm  # hashed: password123
    mjones:
      name: Mary Jones
      password: $2b$12$vZGDlHvzQwJKRlhFfGfCO8LlRlYxN8dQw6WJX8HvZGZJHqWjQXWm  # hashed: secure456
    tmanager:
      name: Transport Manager
      password: $2b$12$xYZAbcDefGhIjKlMnOpQrStUvWxYz123456789AbCdEfGhIjKlM  # hashed: logistics789

cookie:
  expiry_days: 30
  key: some_signature_key_12345  # Change this to a random string
  name: contract_analysis_cookie

preauthorized:
  emails:
  - john.smith@company.com
  - mary.jones@company.com
```

**⚠️ IMPORTANT:** Passwords above are hashed. To generate hashed passwords, use this Python script:

Create `generate_password.py`:
```python
import bcrypt

def hash_password(password: str) -> str:
    """Generate bcrypt hash for password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Generate hashes for your passwords
passwords = {
    "password123": hash_password("password123"),
    "secure456": hash_password("secure456"),
    "logistics789": hash_password("logistics789")
}

for password, hashed in passwords.items():
    print(f"{password}: {hashed}")
```

Run:
```bash
python generate_password.py
```

Copy the generated hashes into `config_auth.yaml`.

### Step 3: Update main.py

Add authentication at the top of `main.py` (after imports):

```python
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load authentication config
with open('config_auth.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login widget
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

# User is authenticated - show main app
st.sidebar.write(f'Welcome *{name}*')
authenticator.logout('Logout', 'sidebar')
```

### Step 4: Add User Isolation

Update session state initialization to include username:

```python
# Initialize session state with user isolation
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = {}  # Now a dict: {username: vector_store}

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}  # Now a dict: {username: chat_history}

if 'supervisor' not in st.session_state:
    st.session_state.supervisor = {}  # Now a dict: {username: supervisor}

# Get current user's data
current_user = username
if current_user not in st.session_state.chat_history:
    st.session_state.chat_history[current_user] = []
if current_user not in st.session_state.vector_store:
    st.session_state.vector_store[current_user] = None
if current_user not in st.session_state.supervisor:
    st.session_state.supervisor[current_user] = None
```

Then update all references to use `current_user`:
```python
# OLD:
st.session_state.chat_history.append(...)

# NEW:
st.session_state.chat_history[current_user].append(...)
```

### Step 5: Test Locally

```bash
streamlit run main.py
```

Try logging in with:
- **Username:** `jsmith`
- **Password:** `password123`

---

## Option 2: Streamlit Authenticator (Professional)

### Full Implementation

Update `main.py` with this complete authentication code:

```python
"""
Main RAG Contract Analysis Application with Authentication
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from typing import List, Dict, Any, Annotated, TypedDict, Sequence, Literal
import os
import tempfile
from datetime import datetime
import json
import logging
import re
import pandas as pd
from langchain.docstore.document import Document

# ... (keep all other imports from original main.py)

# Setup logging
logger = logging.getLogger(__name__)

# ==================== AUTHENTICATION ====================

# Load authentication config
with open('config_auth.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# ==================== LOGIN PAGE ====================

# Set page config FIRST (before any st. calls)
st.set_page_config(
    page_title="Contract Analysis RAG System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Login widget
name, authentication_status, username = authenticator.login('Login', 'main')

# Handle authentication status
if authentication_status == False:
    st.error('❌ Username/password is incorrect')
    st.info('💡 Contact your administrator if you forgot your password')
    st.stop()

elif authentication_status == None:
    st.title("🔐 Contract Analysis System - Login")
    st.markdown("---")
    st.info('👆 Please enter your username and password above')

    with st.expander("ℹ️ System Information"):
        st.markdown("""
        **Contract Analysis RAG System**

        This system uses AI to analyze logistics and transportation contracts:
        - Upload contracts (PDF, Excel, TXT)
        - Ask questions in natural language
        - Get instant answers with source references
        - Calculate trip costs and check KPI compliance

        **For access, contact:** IT Support / Your Manager
        """)
    st.stop()

# ==================== USER IS AUTHENTICATED ====================

# Show welcome message
st.sidebar.success(f'✅ Logged in as **{name}**')
authenticator.logout('🚪 Logout', 'sidebar', key='logout_button')

# Store current username
current_user = username

# ==================== INITIALIZE USER-SPECIFIC SESSION STATE ====================

# Initialize multi-user session state
if 'users' not in st.session_state:
    st.session_state.users = {}

# Create user-specific storage
if current_user not in st.session_state.users:
    st.session_state.users[current_user] = {
        'vector_store': None,
        'chat_history': [],
        'supervisor': None,
        'rag_system': None
    }

# Shortcuts for current user's data
user_data = st.session_state.users[current_user]

# ==================== MAIN APPLICATION CODE ====================

# ... (rest of your main.py code, but replace all st.session_state references
#      with user_data where appropriate)

# Example replacements:
# OLD: st.session_state.chat_history
# NEW: user_data['chat_history']

# OLD: st.session_state.rag_system
# NEW: user_data['rag_system']

# OLD: st.session_state.supervisor
# NEW: user_data['supervisor']

# OLD: st.session_state.vector_store
# NEW: user_data['vector_store']
```

---

## Deployment to Streamlit Cloud (After Approval)

### Step 1: Prepare Repository

1. Commit all changes to Git:
```bash
git add .
git commit -m "Add authentication for multi-user deployment"
git push origin main
```

2. Create `.streamlit/secrets.toml` for sensitive config:
```toml
# .streamlit/secrets.toml
[credentials.usernames.jsmith]
name = "John Smith"
password = "$2b$12$KIXhs7qJ9YwJKRlhFfGfCO8LlRlYxN8dQw6WJX8HvZGZJHqWjQXWm"

[credentials.usernames.mjones]
name = "Mary Jones"
password = "$2b$12$vZGDlHvzQwJKRlhFfGfCO8LlRlYxN8dQw6WJX8HvZGZJHqWjQXWm"

[cookie]
expiry_days = 30
key = "your_random_signature_key_change_this_12345"
name = "contract_analysis_cookie"

# Groq API Key
GROQ_API_KEY = "your_groq_api_key_here"
```

**⚠️ Add `.streamlit/secrets.toml` to `.gitignore` to prevent committing secrets!**

Update `.gitignore`:
```
.streamlit/secrets.toml
config_auth.yaml
.env
```

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and branch
5. Set main file: `main.py`
6. Click "Deploy"

### Step 3: Add Secrets in Streamlit Cloud

1. In Streamlit Cloud dashboard, click your app
2. Click "⚙️ Settings"
3. Click "Secrets"
4. Paste contents of `.streamlit/secrets.toml`
5. Click "Save"

### Step 4: Test Deployment

1. Wait for deployment (2-5 minutes)
2. Access your app: `https://yourapp.streamlit.app`
3. Try logging in with test credentials
4. Verify authentication works
5. Test multi-user (open in incognito window with different user)

---

## Deployment to Self-Hosted Cloud (AWS/Azure/DigitalOcean)

### Step 1: Provision Server

#### Option A: DigitalOcean (Easiest)

1. Go to https://www.digitalocean.com/
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic ($12/month - 2GB RAM)
   - **Region:** Choose closest to your users
   - **Authentication:** SSH Key (add your public key)
3. Click "Create Droplet"

#### Option B: AWS EC2

1. Go to AWS Console → EC2
2. Launch Instance:
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t3.small
   - **Security Group:** Allow HTTP (80), HTTPS (443), SSH (22)
3. Download key pair (.pem file)

### Step 2: Connect to Server

```bash
# DigitalOcean
ssh root@your_server_ip

# AWS (use your key)
ssh -i your_key.pem ubuntu@your_server_ip
```

### Step 3: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Nginx (web server)
sudo apt install nginx -y

# Install Certbot (for HTTPS)
sudo apt install certbot python3-certbot-nginx -y
```

### Step 4: Deploy Application

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/rag_langgraph.git
cd rag_langgraph

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R $USER:$USER venv

# Activate and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
sudo nano .env
```

Paste:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Save (Ctrl+X, Y, Enter)

### Step 5: Create Systemd Service

```bash
sudo nano /etc/systemd/system/contract-rag.service
```

Paste:
```ini
[Unit]
Description=Contract RAG Analysis System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rag_langgraph
Environment="PATH=/opt/rag_langgraph/venv/bin"
ExecStart=/opt/rag_langgraph/venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable contract-rag
sudo systemctl start contract-rag
sudo systemctl status contract-rag
```

### Step 6: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/contract-rag
```

Paste:
```nginx
server {
    listen 80;
    server_name contracts.yourcompany.com;  # Change to your domain

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/contract-rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 7: Set Up HTTPS (SSL)

```bash
sudo certbot --nginx -d contracts.yourcompany.com
```

Follow prompts:
- Enter email
- Agree to terms
- Choose redirect HTTP to HTTPS (option 2)

### Step 8: Test

1. Go to: `https://contracts.yourcompany.com`
2. Should see login page
3. Log in with credentials
4. Test uploading contracts and asking questions

---

## User Management

### Adding New Users

Edit `config_auth.yaml`:

```bash
# On server
cd /opt/rag_langgraph
source venv/bin/activate
python generate_password.py  # Generate hash for new password

# Edit config
nano config_auth.yaml
```

Add new user:
```yaml
credentials:
  usernames:
    newuser:
      name: New User Name
      password: $2b$12$...  # Paste hashed password here
```

Restart service:
```bash
sudo systemctl restart contract-rag
```

### Removing Users

Edit `config_auth.yaml`, remove user entry, restart service.

### Changing Passwords

1. Generate new hash:
```bash
python generate_password.py
```

2. Update password in `config_auth.yaml`
3. Restart service

---

## Security Best Practices

### 1. Use Strong Passwords
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Use password manager

### 2. Regular Updates
```bash
# Update system monthly
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip install --upgrade -r requirements.txt
```

### 3. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. Backup Configuration
```bash
# Backup authentication config
cp config_auth.yaml config_auth.yaml.backup

# Backup ChromaDB data
tar -czf chroma_db_backup.tar.gz ./chroma_db/
```

### 5. Monitor Logs
```bash
# Application logs
sudo journalctl -u contract-rag -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Issue: "Authentication failed"

**Solution:**
1. Verify `config_auth.yaml` exists
2. Check password hash is correct
3. Ensure YAML syntax is valid

### Issue: "Cannot connect to server"

**Solution:**
1. Check service status: `sudo systemctl status contract-rag`
2. Check nginx status: `sudo systemctl status nginx`
3. Verify firewall: `sudo ufw status`

### Issue: "SSL certificate error"

**Solution:**
1. Renew certificate: `sudo certbot renew`
2. Check DNS points to server IP
3. Restart nginx: `sudo systemctl restart nginx`

---

## Cost Estimate

### Streamlit Cloud
- **Free:** $0/month (public apps, limited resources)
- **Teams:** $20/month (private apps)
- **Enterprise:** Contact sales

### Self-Hosted Cloud

#### DigitalOcean
- **Server:** $12/month (2GB RAM)
- **Domain:** $10/year
- **SSL:** Free (Let's Encrypt)
- **Total:** ~$154/year

#### AWS EC2
- **t3.small:** $15-20/month (~$240/year)
- **Data transfer:** ~$10/month
- **Total:** ~$360/year

#### Azure
- **B2s VM:** $30/month (~$360/year)

**Recommendation:** DigitalOcean for best value ($154/year)

---

## Next Steps

1. **Get approval** from management/legal/IT security
2. **Choose deployment option:**
   - Streamlit Cloud (easier) OR
   - Self-hosted cloud (more control)
3. **Generate passwords** for users
4. **Test locally** with authentication
5. **Deploy** following this guide
6. **Train users** on login and usage
7. **Monitor** usage and security

---

## Support Resources

- **Streamlit Authenticator:** https://github.com/mkhorasani/Streamlit-Authenticator
- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **DigitalOcean Tutorials:** https://www.digitalocean.com/community/tutorials
- **AWS EC2 Docs:** https://docs.aws.amazon.com/ec2/
- **Nginx Docs:** https://nginx.org/en/docs/

---

**Document End**

**⚠️ REMINDER:** Do NOT implement authentication or deploy to cloud until you receive approval from your employer, especially for extremely sensitive contracts.
