# AI Contract Analysis System

A production-ready RAG (Retrieval-Augmented Generation) system for analyzing logistics and transportation contracts using LangChain, LangGraph, and Groq API.

## ☁️ Quick Deploy to Streamlit Cloud

**Deploy in 15-30 minutes!** See **[STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** for step-by-step guide.

**Cost:** $0 (Free with Streamlit Cloud + Groq free tier)

**Live Demo:** Deploy your own instance in minutes!

---

## 🚀 Features

- **🤖 Multi-Agent Architecture**: Supervisor coordinates retriever, analyst, and summarizer agents
- **🔍 Semantic Search**: HuggingFace embeddings for accurate document retrieval
- **⚡ Real-time Streaming**: Instant response streaming with Groq API
- **📊 Interactive UI**: Modern Streamlit interface with professional design
- **💾 Vector Database**: ChromaDB for fast semantic search
- **📋 23 Pre-configured Questions**: Common logistics contract questions built-in
- **📄 Multi-format Support**: PDF, Excel (.xlsx, .xls), and TXT files
- **🧮 Logistics Tools**: Trip cost calculator and KPI compliance checker
- **🎯 Domain Optimized**: Specialized for FTL/LTL transportation contracts
- **🔓 Open Source**: No vendor lock-in, switch LLM providers anytime

---

## 📋 Requirements

- Python 3.9+
- Groq API Key ([Get free key](https://console.groq.com/))
- 4GB+ RAM (for embeddings)

---

## 🔧 Local Installation

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/agentic_rag_contract.git
cd agentic_rag_contract
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv rag_env
rag_env\Scripts\activate

# Linux/Mac
python3 -m venv rag_env
source rag_env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

Get your free API key at: https://console.groq.com/

### 5. Run the Application

```bash
streamlit run main.py
```

Application opens at `http://localhost:8501`

---

## 🎯 How to Use

### 1. Upload Contracts

- Click **"Upload Contract Documents"** in sidebar
- Supported formats: **PDF, Excel (.xlsx, .xls), TXT**
- Upload multiple files at once

### 2. Process Documents

- Click **"Process Documents"** button
- System extracts text and creates vector embeddings
- Takes 2-5 seconds per 10 pages

### 3. Ask Questions

**Two ways to interact:**

#### A. Type Your Own Questions
Use the chat interface:
- "What is the on-time delivery requirement?"
- "What are the payment terms?"
- "Calculate trip cost for 500km at €1.2/km"
- "What happens if we miss KPI targets?"

#### B. Use Pre-configured Questions (23 Built-in)
Click any of the 23 frequent logistics questions in the right panel:
- Customer details (name, sector, products)
- Service types (FTL/LTL, intermodal, rail)
- Equipment requirements
- Pricing and fuel surcharge
- KPIs and penalties
- Payment terms

---

## 🏗️ Architecture

### Multi-Agent System

```
User Query
    ↓
Supervisor Agent (routes query)
    ↓
┌───────────────┬──────────────┬────────────────┐
│               │              │                │
Retriever       Analyst        Summarizer       END
(search)        (analyze)      (summarize)
```

**Agents:**
1. **Supervisor**: Routes queries to appropriate agent
2. **Retriever**: Searches contracts for relevant information
3. **Analyst**: Analyzes retrieved data and answers questions
4. **Summarizer**: Creates contract summaries

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | Groq API | Fast inference with open-source models |
| **Framework** | LangChain + LangGraph | AI orchestration and workflow |
| **UI** | Streamlit | Interactive web interface |
| **Embeddings** | HuggingFace sentence-transformers | Text vectorization |
| **Vector DB** | ChromaDB | Semantic search and storage |
| **Documents** | PyPDF + OpenPyXL | PDF and Excel processing |

### Components Details

- **LLM Provider**: Groq API (openai/gpt-oss-120b)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: ChromaDB with local persistence
- **Chunking**: RecursiveCharacterTextSplitter (1200 chars, 250 overlap)
- **Retrieval**: Top-4 similarity search

---

## ⚙️ Configuration

### Available Groq Models

Edit `.env` or Streamlit secrets to change models:

```env
# Default (best quality)
GROQ_MODEL=openai/gpt-oss-120b

# Alternatives:
# GROQ_MODEL=openai/gpt-oss-28b         # Faster
# GROQ_MODEL=llama-3.1-8b-instant       # Fastest
# GROQ_MODEL=llama-3.3-70b-versatile    # Balanced
```

### Document Processing Settings

```env
CHUNK_SIZE=1200              # Characters per chunk
CHUNK_OVERLAP=250            # Overlap between chunks
TOP_K_RESULTS=4              # Number of chunks to retrieve
```

### System Prompts

Customize agent behavior in `config.py`:
- `RETRIEVER_PROMPT` - Search behavior
- `ANALYST_PROMPT` - Analysis style
- `SUMMARIZER_PROMPT` - Summary format
- `SUPERVISOR_PROMPT` - Routing logic

All prompts are optimized for **logistics and transportation contracts**.

---

## 🧮 Specialized Features

### 1. Trip Cost Calculator

Built-in tool to calculate FTL transportation costs:

**Example Query:**
> "Calculate trip cost for 500km at €1.2/km with 25% fuel surcharge and 3 hours waiting time"

**Calculates:**
- Base rate (€/km or €/shipment)
- Fuel surcharge (%)
- Waiting time charges
- Multi-stop fees
- **Total cost breakdown**

### 2. KPI Compliance Checker

Validates KPI performance against contract requirements:

**Supported KPIs:**
- On-Time Delivery (OTD) %
- Claims rate %
- Booking acceptance %
- POD upload compliance %

**Example Query:**
> "Check if 96.5% OTD meets requirements"

**Returns:**
- Status (✅ Excellent / ⚠️ Warning / ❌ Non-compliant)
- Gap analysis vs targets
- Penalty warnings if applicable

---

## 📊 Performance

### Typical Metrics

- **Document Processing**: 2-5 seconds per 10 PDF pages
- **Query Response**: 2-4 seconds (with streaming)
- **Embedding Generation**: 1-2 seconds per 1000 tokens
- **Memory Usage**: 500MB-1GB (depends on document count)

### Optimization Tips

1. **GPU Acceleration**: Set `EMBEDDING_DEVICE=cuda` (10x faster)
2. **Reduce Chunk Size**: Set `CHUNK_SIZE=800` for faster processing
3. **Faster Model**: Use `llama-3.1-8b-instant` for speed
4. **Fewer Results**: Set `TOP_K_RESULTS=3` for faster retrieval

---

## 🐛 Troubleshooting

### "GROQ_API_KEY not found"

**Solution:**
1. Create `.env` file (copy from `.env.example`)
2. Add: `GROQ_API_KEY=gsk_your_key_here`
3. Restart the app

### "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Slow performance

**Solution:**
1. Reduce `CHUNK_SIZE` to 800
2. Use GPU: `EMBEDDING_DEVICE=cuda`
3. Switch to faster model: `llama-3.1-8b-instant`

### ChromaDB errors

**Solution:**
```bash
# Delete vector database and reprocess
rm -rf ./chroma_db
# Then re-upload contracts in the app
```

### Out of memory

**Solution:**
1. Upload fewer documents at once
2. Reduce `CHUNK_SIZE` to 800
3. Reduce `TOP_K_RESULTS` to 3

---

## 📝 Example Queries

### Logistics Contracts

- "What is the fuel surcharge percentage?"
- "What are the KPI requirements?"
- "Summarize penalty clauses"
- "What equipment types are required?"
- "When is the deadline for the tender?"
- "What is the pre-advise requirement?"

### Cost Calculations

- "Calculate trip cost for 300km at €1.5/km with fuel surcharge"
- "What is the total cost including 2 hours waiting time?"

### KPI Compliance

- "Check if 97% OTD meets requirements"
- "What happens if claims exceed 0.3%?"

---

## 🔒 Security

### Data Privacy

- **Local Development**: All data stays on your PC
- **Streamlit Cloud**: Data stored on Streamlit's servers
- **Groq API**: Only query text sent (not full documents)
- **No Training**: Groq uses inference only - your data is NOT used for AI training

### Best Practices

- ✅ Never commit `.env` file to GitHub
- ✅ Keep Groq API key secure
- ✅ Use Streamlit secrets for cloud deployment
- ✅ Rotate API keys regularly
- ✅ Review `.gitignore` before pushing code

---

## 📚 Documentation

### Deployment Guides

- **[STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** - Deploy to Streamlit Cloud (15 min)
- **[DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)** - Compare deployment options
- **[AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)** - Add user authentication

### Technical Documentation

- **[TECH_STACK.md](TECH_STACK.md)** - Complete technical stack
- **[DEPLOYMENT_AND_SECURITY.md](DEPLOYMENT_AND_SECURITY.md)** - Security comparison
- **[CUSTOMIZATION_SUMMARY.md](CUSTOMIZATION_SUMMARY.md)** - Logistics customizations

### Presentation

- **[PRESENTATION.html](PRESENTATION.html)** - Visual presentation for stakeholders

---

## 💰 Cost Comparison

| Solution | Cost/Year | Features |
|----------|-----------|----------|
| **This System (Streamlit Cloud)** | **$0-240** | Multi-user, remote access, NO training on data |
| **This System (Self-Hosted)** | **$144-360** | Full control, your cloud, NO training on data |
| **Microsoft 365 Copilot** | **$6,000-10,000** | Enterprise features, BUT trains on your data |

**Savings: 94-100% cheaper than Microsoft 365 Copilot**

**Key Advantage:** Groq uses inference only - your contract data is NEVER used for AI training (unlike Microsoft/OpenAI)

---

## 🔗 External Resources

- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Groq API Docs](https://console.groq.com/docs)
- [Streamlit Docs](https://docs.streamlit.io/)
- [HuggingFace Models](https://huggingface.co/models)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 🙏 Acknowledgments

- **LangChain** team for the framework
- **Groq** for fast inference API
- **HuggingFace** for embedding models
- **Streamlit** for the UI framework

---

## ⚠️ Disclaimer

This system is designed for contract analysis assistance only. Always have legal professionals review important contracts. This tool does not provide legal advice.

---

**🚀 Ready to deploy?** See [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md) to get started in 15 minutes!
