# Installation Guide

Complete installation and setup guide for the Contract RAG Analysis System.

## Prerequisites

- **Python**: 3.9 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space for models and vector store
- **Groq API Key**: Get one at [https://console.groq.com/](https://console.groq.com/)

## Quick Start (5 minutes)

### 1. Verify Python Installation

```bash
python --version
# Should show Python 3.9 or higher
```

### 2. Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv rag_env
rag_env\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv rag_env
source rag_env/bin/activate
```

You should see `(rag_env)` in your terminal prompt.

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages (may take 5-10 minutes).

### 4. Configure Environment

**Windows:**
```bash
copy .env.example .env
notepad .env
```

**Linux/Mac:**
```bash
cp .env.example .env
nano .env
```

Update the `.env` file with your Groq API key:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 5. Run the Application

```bash
streamlit run main.py
```

The application will open automatically in your browser at `http://localhost:8501`

## Detailed Installation

### Step 1: System Requirements Check

#### Check Python Version
```bash
python --version
```
Must be 3.9 or higher. If not, download from [python.org](https://www.python.org/downloads/)

#### Check Available RAM
```bash
# Windows
systeminfo | findstr "Available Physical Memory"

# Linux/Mac
free -h
```
Should have at least 4GB available.

#### Check Disk Space
```bash
# Windows
dir

# Linux/Mac
df -h .
```
Need at least 2GB free.

### Step 2: Get Groq API Key

1. Go to [https://console.groq.com/](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)

### Step 3: Virtual Environment Setup

Virtual environments isolate project dependencies.

**Create virtual environment:**
```bash
# Windows
python -m venv rag_env

# Linux/Mac
python3 -m venv rag_env
```

**Activate virtual environment:**
```bash
# Windows Command Prompt
rag_env\Scripts\activate

# Windows PowerShell
rag_env\Scripts\Activate.ps1

# Linux/Mac
source rag_env/bin/activate
```

**Verify activation:**
Your prompt should now show `(rag_env)` at the beginning.

### Step 4: Install Dependencies

**Upgrade pip first:**
```bash
pip install --upgrade pip
```

**Install all requirements:**
```bash
pip install -r requirements.txt
```

**Verify installation:**
```bash
pip list | grep langchain
# Should show multiple langchain packages

pip list | grep groq
# Should show langchain-groq

pip list | grep streamlit
# Should show streamlit
```

### Step 5: Configuration

**Create .env file:**
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Edit .env file:**
```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional - Uncomment to customize
# GROQ_MODEL=llama3-groq-70b-8192-tool-use-preview
# GROQ_TEMPERATURE=0.1
# CHUNK_SIZE=1000
# CHUNK_OVERLAP=200
# EMBEDDING_DEVICE=cpu
```

**Verify configuration:**
```bash
python -c "from config import validate_config; validate_config()"
```

If successful, you'll see: "Configuration loaded successfully"

### Step 6: First Run

**Start the application:**
```bash
streamlit run main.py
```

**What to expect:**
1. Terminal will show "You can now view your Streamlit app in your browser"
2. Browser will open automatically to `http://localhost:8501`
3. First run will download the embeddings model (~100MB)
4. After initial download, subsequent runs are fast

**If browser doesn't open automatically:**
Open your browser and go to: `http://localhost:8501`

## Verification

### Run Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest test_rag.py -v

# Run specific test
pytest test_rag.py::TestConfiguration -v
```

All tests should pass (or skip if mocked components are unavailable).

### Test Basic Functionality

1. **Upload a test document:**
   - Create a simple text file: `test_contract.txt`
   - Add some content: "This is a test contract with payment terms of Net 30 days."
   - Upload via the UI

2. **Process the document:**
   - Click "Process Documents"
   - Should see success message

3. **Ask a question:**
   - Type: "What are the payment terms?"
   - Should get a relevant response

## Troubleshooting

### Issue: "Python not found"

**Solution:**
- **Windows**: Add Python to PATH during installation
- **Linux/Mac**: Install Python 3.9+ via package manager

### Issue: "pip not found"

**Solution:**
```bash
python -m ensurepip --upgrade
```

### Issue: Virtual environment activation fails

**Solution on Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Package installation fails

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install packages one by one to identify problem
pip install streamlit
pip install langchain
pip install langchain-groq
# etc.
```

### Issue: "GROQ_API_KEY not found"

**Solution:**
1. Check `.env` file exists
2. Check API key is on the line: `GROQ_API_KEY=your_key`
3. No quotes needed around the key
4. Restart the application

### Issue: "Module 'config' has no attribute 'validate_config'"

**Solution:**
Make sure you have the latest `config.py`. Re-download if necessary.

### Issue: Embeddings download fails

**Solution:**
```bash
# Download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Issue: Port 8501 already in use

**Solution:**
```bash
# Use different port
streamlit run main.py --server.port 8502
```

### Issue: Out of memory

**Solution:**
1. Reduce `CHUNK_SIZE` in `.env`:
   ```env
   CHUNK_SIZE=500
   ```
2. Reduce `TOP_K_RESULTS`:
   ```env
   TOP_K_RESULTS=3
   ```
3. Close other applications

### Issue: Slow performance

**Solutions:**

**For faster embeddings (if you have GPU):**
```env
EMBEDDING_DEVICE=cuda
```

**Use faster model:**
```env
GROQ_MODEL=mixtral-8x7b-32768
```

**Reduce chunk overlap:**
```env
CHUNK_OVERLAP=100
```

## Advanced Setup

### GPU Acceleration (Optional)

If you have an NVIDIA GPU:

**Install CUDA version of PyTorch:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Update .env:**
```env
EMBEDDING_DEVICE=cuda
```

**Verify GPU usage:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

### Docker Installation (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and run:**
```bash
docker build -t rag-system .
docker run -p 8501:8501 --env-file .env rag-system
```

### Production Deployment

For production use:

1. **Use environment secrets manager** (not `.env` file)
2. **Add authentication** (Streamlit supports auth)
3. **Set up monitoring** (logs, metrics)
4. **Configure reverse proxy** (nginx)
5. **Add rate limiting**
6. **Use persistent storage** for vector DB

## Next Steps

After successful installation:

1. **Read the README**: `README.md` for usage guide
2. **Review CHANGELOG**: `CHANGELOG.md` for all improvements
3. **Customize prompts**: Edit `config.py` for your use case
4. **Run tests**: `pytest test_rag.py -v`
5. **Upload contracts**: Try with your actual contract documents

## Getting Help

If you encounter issues:

1. **Check logs**: Look for error messages in terminal
2. **Review documentation**: README.md and this guide
3. **Run tests**: `pytest test_rag.py -v` to identify issues
4. **Check API status**: [https://status.groq.com/](https://status.groq.com/)
5. **Verify Python version**: Must be 3.9+

## Uninstallation

To remove the system:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf rag_env  # Linux/Mac
rmdir /s rag_env  # Windows

# Remove vector store
rm -rf chroma_db

# Remove Python cache
rm -rf __pycache__
```

---

**Congratulations!** You should now have a fully functional RAG Contract Analysis System.

For usage instructions, see [README.md](README.md)