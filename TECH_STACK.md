# Technical Stack Documentation
## RAG Contract Analysis System

**Document Version:** 1.0
**Last Updated:** 2025-10-21
**Author:** Technical Team
**Purpose:** Complete technical overview for stakeholders and development team

---

## Executive Summary

This RAG (Retrieval-Augmented Generation) Contract Analysis System is a **locally-deployed desktop application** that uses artificial intelligence to analyze logistics and transportation contracts. The system processes contract documents (PDF, Excel, text files) and answers questions about them using advanced natural language processing.

**Key Characteristics:**
- **Deployment Type:** Local desktop application (Windows/Linux/Mac)
- **Data Storage:** 100% local (no cloud storage)
- **AI Processing:** Local embeddings + API-based LLM
- **User Interface:** Web-based UI (runs on localhost)
- **Primary Use Case:** Logistics contract analysis (FTL/LTL transportation)

---

## Technology Stack Overview

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Programming Language** | Python | 3.9+ | Main application language |
| **Web Framework** | Streamlit | 1.41.1 | User interface |
| **AI Orchestration** | LangChain | 0.3.20 | RAG pipeline management |
| **Workflow Engine** | LangGraph | 0.2.66 | Multi-agent coordination |
| **Vector Database** | ChromaDB | 0.5.23 | Local semantic search |
| **LLM Provider** | Groq API | ChatGroq | Language model inference |
| **Embeddings** | HuggingFace | sentence-transformers | Text vectorization |

---

## Detailed Technology Breakdown

### 1. Frontend & User Interface

#### Streamlit (1.41.1)
- **Type:** Python web framework for data applications
- **Purpose:** Provides the interactive web interface
- **Features Used:**
  - File upload widget (PDF, Excel, TXT)
  - Chat interface for Q&A
  - Real-time streaming responses
  - Sidebar for configuration
  - Custom CSS styling
- **Access:** Local browser at `http://localhost:8501`
- **No Internet Required:** Runs completely offline (except LLM API calls)

**User Interface Components:**
```
├── Document Upload Panel (sidebar)
├── Chat Interface (main panel)
├── Pre-configured Question Buttons (23 frequent questions)
├── Statistics Dashboard
└── Configuration Panel (system prompts)
```

---

### 2. AI/ML Layer

#### LangChain (0.3.20)
- **Type:** Framework for building LLM applications
- **Purpose:** Orchestrates the RAG pipeline
- **Components Used:**
  - `RecursiveCharacterTextSplitter`: Splits documents into chunks (1200 chars, 250 overlap)
  - `PyPDFLoader`: Loads PDF contracts
  - `TextLoader`: Loads text files
  - Document retrievers for semantic search
  - Tool decorators for agent functions

#### LangGraph (0.2.66)
- **Type:** Multi-agent workflow framework
- **Purpose:** Manages the supervisor + 3 agents architecture
- **Architecture:**
```
START → Supervisor Agent
           ↓
    ┌──────┴──────┬──────────┐
    ↓             ↓          ↓
Retriever     Analyst   Summarizer
 Agent         Agent      Agent
    │             │          │
    └──────┬──────┴──────────┘
           ↓
          END
```

**Agent Responsibilities:**
1. **Supervisor Agent:** Routes queries to appropriate agent
2. **Retriever Agent:** Searches contracts for relevant information
3. **Analyst Agent:** Analyzes retrieved data and answers questions
4. **Summarizer Agent:** Creates contract summaries

#### LangChain-Groq (0.2.5)
- **Type:** Groq API integration for LangChain
- **Model Used:** `openai/gpt-oss-120b` (default, configurable)

- **Configuration:**
  - Temperature: 0.1 (low randomness for factual answers)
  - Max Tokens: 2048
  - Streaming: Enabled (real-time responses)

**Why Groq?**
- Fast inference (up to 500 tokens/second)
- Cost-effective compared to OpenAI GPT-4
- Multiple open-source models available
- Good quality for contract analysis tasks

---

### 3. Vector Database & Embeddings

#### ChromaDB (0.5.23)
- **Type:** Open-source vector database
- **Storage:** Local filesystem (`./chroma_db` directory)
- **Purpose:** Stores document embeddings for semantic search
- **Features:**
  - Persistent storage (data survives app restarts)
  - Fast similarity search
  - Metadata filtering (by customer, file, sheet)
  - Collection management

**Data Flow:**
```
Contract PDF → Text Chunks → Embeddings → ChromaDB → Retrieval
```

#### HuggingFace Embeddings (sentence-transformers/all-MiniLM-L6-v2)
- **Type:** Semantic text embeddings model
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimension:** 384
- **Processing:** Local (CPU or GPU)
- **Configuration:**
  - Device: CPU (default) or CUDA (GPU-accelerated)
  - Normalization: Enabled (better similarity matching)
- **Performance:**
  - ~1-2 seconds for 1000 tokens
  - ~500MB-1GB memory usage

**Why This Model?**
- Lightweight (384 dimensions vs 1536 for OpenAI)
- Fast on CPU
- Good quality for semantic search
- Free and open-source

#### Sentence Transformers (3.3.1)
- **Type:** Library for state-of-the-art sentence embeddings
- **Purpose:** Powers the embedding generation
- **Features:**
  - Pre-trained models
  - Multi-language support
  - Batch processing

---

### 4. Document Processing

#### PyPDF (5.2.0)
- **Type:** PDF parsing library
- **Purpose:** Extracts text from contract PDFs
- **Features:**
  - Page-by-page extraction
  - Metadata preservation
  - Handles multi-page documents

#### OpenPyXL (3.1.5)
- **Type:** Excel file reader/writer
- **Purpose:** Processes Excel contract files (.xlsx, .xls)
- **Features:**
  - Multi-sheet support
  - Reads all sheets automatically
  - Preserves sheet names as metadata

#### Pandas (2.2.3)
- **Type:** Data analysis library
- **Purpose:** Processes tabular contract data
- **Features:**
  - DataFrame conversion for Excel sheets
  - Data cleaning and transformation
  - Export to CSV

**Supported File Formats:**
- PDF (`.pdf`) - Contract PDFs
- Excel (`.xlsx`, `.xls`) - Rate tables, KPI matrices
- Text (`.txt`) - Plain text contracts

---

### 5. Machine Learning Infrastructure

#### PyTorch (2.6.0)
- **Type:** Deep learning framework
- **Purpose:** Backend for HuggingFace transformers
- **Usage:** Embedding model computation
- **Device Support:** CPU and CUDA (GPU)

#### TensorFlow (2.20.0) + TF-Keras (2.20.1)
- **Type:** Deep learning framework
- **Purpose:** Alternative backend for embeddings
- **Usage:** Compatibility with some HuggingFace models

#### Transformers (4.48.0)
- **Type:** HuggingFace transformers library
- **Purpose:** Provides pre-trained NLP models
- **Features:**
  - Model loading and inference
  - Tokenization
  - Model management

---

### 6. Configuration & Environment

#### python-dotenv (1.0.1)
- **Type:** Environment variable manager
- **Purpose:** Loads configuration from `.env` file
- **Security:** Keeps API keys out of code

**Environment Variables:**
```env
GROQ_API_KEY=<your_api_key>
GROQ_MODEL=openai/gpt-oss-120b
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=2048
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
CHUNK_SIZE=1200
CHUNK_OVERLAP=250
TOP_K_RESULTS=4
```

---

### 7. Supporting Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **numpy** | 1.26.4 | Numerical computing |
| **pydantic** | 2.10.3 | Data validation |
| **typing-extensions** | 4.15.0 | Type hints |
| **protobuf** | 5.29.5 | Data serialization |
| **huggingface-hub** | 0.35.3 | Model downloads |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│                      (Streamlit Web UI)                      │
│  - Document Upload  - Chat Interface  - Quick Questions     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│                     (main.py)                                │
│  - ContractRAGSystem Class                                   │
│  - Session State Management                                  │
│  - Document Processing Pipeline                              │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼──────────┐      ┌──────────▼──────────┐
│  DOCUMENT PROCESSING│      │   MULTI-AGENT      │
│                     │      │   WORKFLOW          │
│ - PyPDF (PDF)       │      │  (LangGraph)        │
│ - OpenPyXL (Excel)  │      │                     │
│ - Pandas (Data)     │      │  ┌──────────────┐  │
│                     │      │  │  Supervisor   │  │
│ ↓ Text Chunks       │      │  └──────┬───────┘  │
│                     │      │         │          │
│ - Text Splitter     │      │  ┌──────▼───────┐  │
│   (1200/250)        │      │  │  Retriever   │  │
└─────────┬───────────┘      │  │   Agent      │  │
          │                  │  └──────────────┘  │
┌─────────▼───────────┐      │  ┌──────────────┐  │
│  EMBEDDING LAYER    │      │  │   Analyst    │  │
│                     │      │  │   Agent      │  │
│ - HuggingFace       │      │  └──────────────┘  │
│ - Sentence Trans.   │      │  ┌──────────────┐  │
│ - PyTorch/TF        │      │  │  Summarizer  │  │
│                     │      │  │   Agent      │  │
│ ↓ Vector Embeddings │      │  └──────────────┘  │
└─────────┬───────────┘      └───────────────────┘
          │                             │
┌─────────▼───────────┐      ┌──────────▼──────────┐
│  VECTOR DATABASE    │      │   LLM API           │
│  (ChromaDB)         │◄─────┤  (Groq)             │
│                     │      │                     │
│ - Local Storage     │      │ - ChatGroq          │
│ - Semantic Search   │      │ - Streaming         │
│ - Metadata Filter   │      │ - openai/gpt-oss    │
└─────────────────────┘      └─────────────────────┘
          │
┌─────────▼───────────┐
│  LOCAL FILESYSTEM   │
│                     │
│ - ./chroma_db/      │
│ - Persistent Data   │
└─────────────────────┘
```

---

## Data Flow

### Document Ingestion Flow

```
1. User uploads PDF/Excel contract
   ↓
2. File saved to temporary location
   ↓
3. Document loaded (PyPDF/OpenPyXL)
   ↓
4. Text extracted with metadata
   ↓
5. Text split into chunks (1200 chars, 250 overlap)
   ↓
6. Chunks converted to embeddings (HuggingFace)
   ↓
7. Embeddings stored in ChromaDB
   ↓
8. User notified: "Processed X documents"
```

### Query Processing Flow

```
1. User asks question
   ↓
2. Supervisor agent analyzes query type
   ↓
3. Routes to Retriever agent
   ↓
4. Retriever searches ChromaDB for relevant chunks
   ↓
5. Top 4 relevant chunks retrieved
   ↓
6. Routes to Analyst agent
   ↓
7. Analyst sends context + question to Groq LLM
   ↓
8. LLM generates answer (streaming)
   ↓
9. Answer displayed to user in real-time
```

---

## Configuration Files

### 1. requirements.txt
Lists all Python dependencies with exact versions for reproducibility.

### 2. .env
Contains sensitive configuration and API keys (not committed to Git).

### 3. config.py
Contains:
- System prompts (Retriever, Analyst, Supervisor, Summarizer)
- Processing parameters (chunk size, overlap, top-k)
- Logging configuration
- Model settings

### 4. main.py
Main application file:
- ContractRAGSystem class
- Multi-agent workflow setup
- Streamlit UI
- Tools (calculate_trip_cost, check_kpi_compliance)

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)
- **CPU:** Dual-core 2.0 GHz
- **RAM:** 4 GB
- **Storage:** 2 GB free space
- **Internet:** Required only for Groq API calls

### Recommended Requirements
- **OS:** Windows 11, macOS 12+, Linux (Ubuntu 22.04+)
- **CPU:** Quad-core 3.0 GHz or Apple Silicon (M1/M2)
- **RAM:** 8 GB or more
- **GPU:** NVIDIA GPU with CUDA support (optional, for faster embeddings)
- **Storage:** 5 GB free space
- **Internet:** Broadband connection for faster API responses

### Network Requirements
- **Outbound:** HTTPS (443) access to `api.groq.com`
- **Inbound:** None (local-only access)
- **Bandwidth:** ~1-5 MB per query (for LLM API)

---

## Performance Metrics

### Typical Performance
- **Document Processing:** 2-5 seconds per 10 PDF pages
- **Embedding Generation:** 1-2 seconds per 1000 tokens
- **Query Response:** 2-4 seconds (with streaming)
- **Memory Usage:** 500MB-1GB (varies with document count)

### Optimization Options
1. **GPU Acceleration:** Set `EMBEDDING_DEVICE=cuda` (10x faster embeddings)
2. **Chunk Size:** Reduce to 800 for faster processing
3. **Top-K Results:** Reduce to 3 for faster retrieval
4. **Model Selection:** Use `llama-3.1-8b-instant` for faster responses

---

## Specialized Features

### 1. Domain-Specific Tools

#### calculate_trip_cost
Calculates FTL transportation costs including:
- Base rate (€/km or €/shipment)
- Fuel surcharge (%)
- Waiting time charges
- Multi-stop fees

**Example:**
```python
calculate_trip_cost(
    base_rate=1.2,      # €1.2/km
    distance_km=500,    # 500 km
    fuel_surcharge_pct=25,  # 25% FSC
    waiting_hours=3,    # 3 hours waiting
    waiting_rate=35     # €35/hour
)
# Returns: €855.00 total
```

#### check_kpi_compliance
Validates KPI performance against contract requirements:
- OTD (On-Time Delivery) %
- Claims rate %
- Booking acceptance %
- POD upload compliance %

**Example:**
```python
check_kpi_compliance(
    kpi_type='otd',
    actual_value=96.5,  # 96.5% OTD
    customer='Tesla'
)
# Returns: ⚠️ WARNING - Below target (98%)
```

### 2. Customized System Prompts

All prompts optimized for **logistics and transportation contracts**:

- **Retriever Prompt:** Focuses on FTL/LTL rates, KPIs, penalties, FSC, equipment types
- **Analyst Prompt:** Provides customer-specific answers with exact numbers
- **Supervisor Prompt:** Routes queries to appropriate agent
- **Summarizer Prompt:** Creates logistics-focused summaries

### 3. Pre-configured Questions

23 frequent logistics questions built into the UI:
1. Customer details (name, sector, products)
2. Service types (FTL/LTL, intermodal, short-sea, rail)
3. Equipment requirements (thermo, ambient, reefer)
4. ADR (dangerous goods) conditions
5. Pricing (base rates, FSC, waiting charges)
6. KPIs (OTD, claims, booking acceptance)
7. Payment terms
8. Penalties and demurrage

---

## Security Features

### 1. API Key Management
- API keys stored in `.env` file (not in code)
- `.env` file excluded from Git (via `.gitignore`)
- Environment variables loaded at runtime

### 2. Data Privacy
- All document processing happens locally
- No document data sent to third parties (except LLM API queries)
- ChromaDB data stored locally (not in cloud)
- No telemetry or usage tracking

### 3. Access Control
- Application accessible only via localhost (`127.0.0.1`)
- No external network access (except Groq API)
- No user authentication (single-user desktop app)

---

## Dependencies Licenses

All dependencies use permissive open-source licenses:
- **LangChain:** MIT License
- **Streamlit:** Apache License 2.0
- **ChromaDB:** Apache License 2.0
- **HuggingFace Transformers:** Apache License 2.0
- **PyTorch:** BSD License
- **Pandas:** BSD License

**Commercial Use:** Allowed for all dependencies

---

## Extensibility

### Adding New Tools
Create new `@tool` decorated functions in `main.py`:
```python
@tool
def custom_analysis(contract_text: str) -> str:
    """Your custom analysis logic"""
    pass
```

### Changing Embedding Models
Edit `.env`:
```env
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### Adding New Document Types
Add new loader in `process_documents()`:
```python
elif uploaded_file.name.endswith('.docx'):
    loader = Docx2txtLoader(tmp_file_path)
```

### Customizing Prompts
Edit `config.py`:
```python
RETRIEVER_PROMPT = """Your custom retriever prompt..."""
ANALYST_PROMPT = """Your custom analyst prompt..."""
```

---

## Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not found"**
   - Solution: Create `.env` file with `GROQ_API_KEY=your_key_here`

2. **Slow embeddings**
   - Solution: Set `EMBEDDING_DEVICE=cuda` (requires NVIDIA GPU)

3. **Out of memory**
   - Solution: Reduce `CHUNK_SIZE` to 800, `TOP_K_RESULTS` to 3

4. **ChromaDB errors**
   - Solution: Delete `./chroma_db` directory and reprocess documents

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-21 | Initial tech stack documentation |

---

## Technical Support

For technical questions about the stack:
1. Check documentation in `/docs` folder
2. Review `README.md` for quick start guide
3. See `INSTALLATION.md` for detailed setup instructions
4. Refer to `TROUBLESHOOTING.md` for common issues

---

**Document End**
