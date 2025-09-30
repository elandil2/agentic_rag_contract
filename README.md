# Contract RAG Analysis System

A production-ready Retrieval-Augmented Generation (RAG) system for contract analysis using LangChain, LangGraph, and Groq API.

## 🚀 Features

- **Multi-Agent Architecture**: Supervisor coordinates retriever, analyst, and summarizer agents
- **Semantic Search**: HuggingFace embeddings for accurate document retrieval
- **Streaming Support**: Real-time response streaming with Groq API
- **Interactive UI**: Streamlit-based interface for document upload and analysis
- **Persistent Storage**: ChromaDB vector store with persistent storage
- **Quick Analysis**: Pre-built buttons for risk analysis, key terms, dates, and payment terms
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 📋 Requirements

- Python 3.9+
- Groq API Key ([Get one here](https://console.groq.com/))
- 4GB+ RAM recommended for embeddings

## 🔧 Installation

### 1. Clone or Download the Repository

```bash
cd rag_langgraph
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

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## 🎯 Usage

### Running the Application

```bash
streamlit run main.py
```

The application will open in your browser at `http://localhost:8501`

### Basic Workflow

1. **Upload Documents**: Click "Upload Contract Documents" in the sidebar
   - Supported formats: PDF, TXT
   - Upload 1-10 documents

2. **Process Documents**: Click "Process Documents" button
   - System will chunk documents and create embeddings
   - Vector store will be created for semantic search

3. **Ask Questions**: Use the chat interface to ask questions about your contracts
   - Examples:
     - "What are the payment terms?"
     - "List all obligations of the parties"
     - "Identify any risks or liabilities"

4. **Quick Analysis**: Use pre-built analysis buttons
   - 🔍 Find Key Terms
   - ⚠️ Identify Risks
   - 📅 Extract Dates
   - 💰 Payment Terms
   - 📋 Summarize All Contracts

## 🏗️ Architecture

### Multi-Agent System

The system uses a supervisor pattern with three specialized agents:

1. **Retriever Agent**: Searches and retrieves relevant contract sections
2. **Analyst Agent**: Analyzes retrieved information and provides insights
3. **Summarizer Agent**: Creates concise summaries of contracts

### LangGraph Workflow

```
START → Supervisor → [Retriever/Analyst/Summarizer] → END
```

The supervisor routes queries to the appropriate agent based on the query type.

### Components

- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: ChromaDB with persistent storage
- **LLM**: Groq API (llama3-groq-70b-8192-tool-use-preview)
- **Chunking**: RecursiveCharacterTextSplitter (1000 chars, 200 overlap)

## ⚙️ Configuration

### Model Selection

Edit `.env` to change models:

```env
# Available models
GROQ_MODEL=llama3-groq-70b-8192-tool-use-preview
# or
GROQ_MODEL=llama3-70b-8192
# or
GROQ_MODEL=mixtral-8x7b-32768
# or
GROQ_MODEL=gemma2-9b-it
```

### Chunk Settings

Adjust in `.env`:

```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### System Prompts

Customize agent behavior in `config.py`:

- `RETRIEVER_PROMPT`: Controls retrieval agent behavior
- `ANALYST_PROMPT`: Controls analysis agent behavior
- `SUMMARIZER_PROMPT`: Controls summarization agent behavior
- `SUPERVISOR_PROMPT`: Controls routing logic

## 🧪 Testing

Run the test suite:

```bash
pytest test_rag.py -v
```

Run specific test classes:

```bash
pytest test_rag.py::TestConfiguration -v
pytest test_rag.py::TestContractRAGSystem -v
pytest test_rag.py::TestTools -v
```

## 📊 Performance

### Typical Metrics

- **Document Processing**: ~2-5 seconds for 10 PDF pages
- **Query Response**: ~2-4 seconds with streaming
- **Embedding Generation**: ~1-2 seconds for 1000 tokens
- **Memory Usage**: ~500MB-1GB depending on document count

### Optimization Tips

1. **GPU Acceleration**: Set `EMBEDDING_DEVICE=cuda` in `.env` if GPU available
2. **Chunk Size**: Reduce `CHUNK_SIZE` for faster processing, increase for better context
3. **Top K Results**: Adjust `TOP_K_RESULTS` to balance relevance vs. speed
4. **Model Selection**: Use `mixtral-8x7b-32768` for faster responses, `llama3-70b-8192` for better quality

## 🔍 Key Improvements Over Original

### 1. Fixed Deprecation Warnings
- ✅ Replaced `create_react_agent` with `ToolNode` and proper StateGraph
- ✅ Updated to latest LangGraph API with START/END nodes
- ✅ Fixed ChromaDB persistence with correct parameters

### 2. Proper Embeddings
- ✅ Replaced hash-based embeddings with HuggingFace semantic embeddings
- ✅ Added normalization for better similarity search

### 3. Better Model Configuration
- ✅ Fixed invalid Groq model name
- ✅ Added support for all available Groq models
- ✅ Made configuration environment-based

### 4. Streaming Support
- ✅ Enabled streaming in ChatGroq
- ✅ Added streaming UI updates in Streamlit
- ✅ Proper error handling for streaming failures

### 5. Enhanced Architecture
- ✅ Proper TypedDict for state management
- ✅ Conditional routing with supervisor pattern
- ✅ Tool-based agent architecture
- ✅ Memory checkpointing with MemorySaver

### 6. Improved Error Handling
- ✅ Comprehensive logging throughout
- ✅ Try-catch blocks with specific error messages
- ✅ Graceful fallbacks for failures

### 7. Testing
- ✅ Comprehensive test suite with pytest
- ✅ Unit tests for all major components
- ✅ Integration tests for end-to-end workflow
- ✅ Mock-based testing for external dependencies

## 🐛 Troubleshooting

### Issue: "GROQ_API_KEY not found"
**Solution**: Make sure `.env` file exists and contains your API key

### Issue: "Module not found"
**Solution**: Activate virtual environment and reinstall dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Issue: Slow embeddings
**Solution**:
1. Reduce `CHUNK_SIZE` in `.env`
2. Use GPU if available: `EMBEDDING_DEVICE=cuda`
3. Consider using a smaller embedding model

### Issue: Out of memory
**Solution**:
1. Reduce number of documents processed at once
2. Reduce `CHUNK_SIZE`
3. Reduce `TOP_K_RESULTS`

### Issue: ChromaDB errors
**Solution**: Delete `./chroma_db` directory and reprocess documents
```bash
rm -rf ./chroma_db
```

## 📝 Example Queries

### Contract Analysis
- "What are the key obligations of each party?"
- "Identify all payment terms and conditions"
- "When does this contract expire?"
- "What are the termination clauses?"

### Risk Assessment
- "What are the potential risks in this contract?"
- "Are there any unusual or concerning clauses?"
- "What liabilities does each party have?"

### Summarization
- "Provide a summary of all uploaded contracts"
- "What are the main points of this agreement?"

## 🔒 Security Notes

- Never commit `.env` file to version control
- Keep your Groq API key secure
- Use environment variables for all sensitive configuration
- Regularly rotate API keys

## 📚 Documentation

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and commercial use.

## 🙏 Acknowledgments

- LangChain team for the framework
- Groq for the API
- HuggingFace for embeddings models
- Streamlit for the UI framework

---

**Note**: This system is designed for contract analysis. Always have legal professionals review important contracts. This tool is for assistance only, not legal advice.