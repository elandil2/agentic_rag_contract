# RAG System Implementation Architecture

## Overview
This document provides the complete implementation architecture for the Contract AI Assistant RAG system. It includes detailed code structure, class definitions, function signatures, and implementation guidelines.

## Project Structure

```
contract_ai_assistant/
├── app.py                          # Main Streamlit application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag_agent.py           # Main RAG agent implementation
│   │   ├── document_processor.py   # Document processing utilities
│   │   ├── vector_store.py         # ChromaDB vector store management
│   │   ├── embedding_generator.py  # HuggingFace embeddings
│   │   └── llm_integration.py      # Groq API integration
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── components.py           # Reusable UI components
│   │   ├── file_uploader.py        # File upload interface
│   │   ├── query_interface.py      # Query input and results display
│   │   └── authentication.py       # User authentication
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_processing.py      # Text chunking and preprocessing
│   │   ├── file_handlers.py        # PDF/DOCX file processing
│   │   └── validation.py           # Input validation utilities
│   └── config/
│       ├── __init__.py
│       └── settings.py             # Application settings
├── tests/
│   ├── __init__.py
│   ├── test_rag_agent.py
│   ├── test_document_processor.py
│   └── test_vector_store.py
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── USER_MANUAL.md
└── data/
    └── temp/                       # Temporary file storage
```

## Core Components Implementation

### 1. Configuration Management (`config.py`)

```python
import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """Configuration management for the RAG system"""

    def __init__(self):
        load_dotenv()

        # API Keys
        self.GROQ_API_KEY = os.getenv('GROQ_API_KEY')
        self.HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

        # Model Configuration
        self.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        self.LLM_MODEL = "mixtral-8x7b-32768"
        self.TEMPERATURE = 0.1
        self.MAX_TOKENS = 1000

        # Vector Store Configuration
        self.CHROMA_PATH = "./data/chroma_db"
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 200
        self.TOP_K_SIMILARITY = 5

        # UI Configuration
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        self.SUPPORTED_FILE_TYPES = ['.pdf', '.docx', '.txt']
        self.SESSION_TIMEOUT = 3600  # 1 hour

    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_keys = ['GROQ_API_KEY']
        return all(getattr(self, key) for key in required_keys)
```

### 2. Document Processor (`src/core/document_processor.py`)

```python
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .text_processing import TextProcessor

class DocumentProcessor:
    """Handles document ingestion and processing"""

    def __init__(self, config):
        self.config = config
        self.text_processor = TextProcessor()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file and return structured data"""
        file_path = Path(file_path)

        if file_path.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path.suffix.lower() == '.docx':
            text = self._extract_docx_text(file_path)
        elif file_path.suffix.lower() == '.txt':
            text = self._extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Clean and preprocess text
        cleaned_text = self.text_processor.clean_text(text)

        # Split into chunks
        chunks = self.text_splitter.split_text(cleaned_text)

        return {
            'filename': file_path.name,
            'file_path': str(file_path),
            'text': cleaned_text,
            'chunks': chunks,
            'metadata': {
                'file_size': file_path.stat().st_size,
                'file_type': file_path.suffix,
                'chunk_count': len(chunks),
                'word_count': len(cleaned_text.split())
            }
        }

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def _extract_txt_text(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
```

### 3. Vector Store Manager (`src/core/vector_store.py`)

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import uuid
from pathlib import Path

class ChromaVectorStore:
    """Manages ChromaDB vector store operations"""

    def __init__(self, config):
        self.config = config
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PATH or "./data/chroma_db"
        )
        self.collection = None
        self._setup_collection()

    def _setup_collection(self):
        """Create or get existing collection"""
        collection_name = "contract_documents"

        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Contract document chunks with embeddings"}
            )

    def add_documents(self, processed_docs: List[Dict[str, Any]]) -> bool:
        """Add processed documents to ChromaDB"""
        try:
            ids = []
            documents = []
            metadatas = []

            for doc in processed_docs:
                for i, chunk in enumerate(doc['chunks']):
                    doc_id = f"{doc['filename']}_{i}_{uuid.uuid4().hex[:8]}"

                    ids.append(doc_id)
                    documents.append(chunk)
                    metadatas.append({
                        'filename': doc['filename'],
                        'chunk_id': i,
                        'total_chunks': len(doc['chunks']),
                        'file_size': doc['metadata']['file_size'],
                        'word_count': doc['metadata']['word_count']
                    })

            # ChromaDB automatically handles embeddings
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            return True
        except Exception as e:
            print(f"ChromaDB error: {e}")
            return False

    def search_similar(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents in ChromaDB"""
        if top_k is None:
            top_k = self.config.TOP_K_SIMILARITY

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )

            search_results = []
            for i, doc in enumerate(results['documents'][0]):
                search_results.append({
                    'document': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })

            return search_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def search_with_filter(self, query: str, filename: str = None, top_k: int = None) -> List[Dict[str, Any]]:
        """Search with metadata filtering"""
        if top_k is None:
            top_k = self.config.TOP_K_SIMILARITY

        where_clause = {"filename": filename} if filename else None

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )

            search_results = []
            for i, doc in enumerate(results['documents'][0]):
                search_results.append({
                    'document': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]
                })

            return search_results

        except Exception as e:
            print(f"Filtered search error: {e}")
            return []

    def get_document_count(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()

    def clear_collection(self):
        """Clear all documents from collection"""
        try:
            collection_name = "contract_documents"
            self.client.delete_collection(collection_name)
            self._setup_collection()
        except Exception as e:
            print(f"Clear error: {e}")

    def list_collections(self) -> List[str]:
        """List all collections"""
        return [col.name for col in self.client.list_collections()]
```

### 4. Embedding Generator (`src/core/embedding_generator.py`)

```python
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Handles text embedding generation using HuggingFace"""

    def __init__(self, config):
        self.config = config
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to a smaller model if needed
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            # Normalize embeddings for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / norms
            return normalized_embeddings.tolist()
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self.model.get_sentence_embedding_dimension()
```

### 5. LLM Integration (`src/core/llm_integration.py`)

```python
from typing import Dict, Any, Optional
import groq
from groq import Groq

class LLMIntegration:
    """Handles integration with Groq API for LLM responses"""

    def __init__(self, config):
        self.config = config
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def generate_response(self,
                         query: str,
                         context: str,
                         system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Groq API"""

        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant specializing in contract analysis.
            Use the provided context to answer questions accurately and comprehensively.
            If the context doesn't contain enough information, say so clearly."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS,
                top_p=1,
                stream=False
            )

            return {
                'success': True,
                'response': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': response.model
            }

        except groq.APIError as e:
            return {
                'success': False,
                'error': f"API Error: {str(e)}",
                'response': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'response': None
            }

    def generate_summary(self, text: str, max_length: int = 500) -> Dict[str, Any]:
        """Generate a summary of the provided text"""

        system_prompt = f"""You are a contract summarization expert.
        Provide a clear, concise summary of the contract content in {max_length} characters or less.
        Focus on key terms, obligations, and important clauses."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please summarize this contract:\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=max_length // 4,  # Approximate token to character ratio
                top_p=1,
                stream=False
            )

            return {
                'success': True,
                'summary': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'summary': None
            }
```

### 6. RAG Agent (`src/core/rag_agent.py`)

```python
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from .vector_store import ChromaVectorStore
from .llm_integration import LLMIntegration

class RAGAgent:
    """Main RAG agent that orchestrates the retrieval and generation process"""

    def __init__(self, config, vector_store: ChromaVectorStore, llm: LLMIntegration):
        self.config = config
        self.vector_store = vector_store
        self.llm = llm
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent_executor = None
        self._setup_agent()

    def _setup_agent(self):
        """Setup the LangChain agent with tools"""

        # Define tools
        tools = [
            Tool(
                name="DocumentSearch",
                description="Search through uploaded documents for relevant information",
                func=self._search_documents
            ),
            Tool(
                name="GenerateAnswer",
                description="Generate an answer based on retrieved context",
                func=self._generate_answer
            ),
            Tool(
                name="SummarizeContent",
                description="Generate a summary of contract content",
                func=self._summarize_content
            )
        ]

        # Create the agent prompt
        template = """You are a Contract Analysis AI Assistant. You have access to tools to search through contract documents and generate responses.

Available tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        # Create the agent
        agent = create_react_agent(
            llm=self.llm.client,  # This would need to be wrapped for LangChain
            tools=tools,
            prompt=prompt
        )

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return a response"""

        try:
            # First, search for relevant documents
            search_results = self.vector_store.search_similar(query)

            if not search_results:
                return {
                    'success': False,
                    'response': "No relevant documents found. Please upload contract documents first.",
                    'sources': []
                }

            # Combine relevant chunks into context
            context = "\n\n".join([result['document'] for result in search_results])

            # Generate response using LLM
            llm_response = self.llm.generate_response(query, context)

            if llm_response['success']:
                return {
                    'success': True,
                    'response': llm_response['response'],
                    'sources': [
                        {
                            'filename': result['metadata']['filename'],
                            'similarity_score': result['similarity_score'],
                            'chunk_id': result['metadata']['chunk_id']
                        }
                        for result in search_results
                    ],
                    'usage': llm_response.get('usage', {})
                }
            else:
                return {
                    'success': False,
                    'response': f"Error generating response: {llm_response['error']}",
                    'sources': []
                }

        except Exception as e:
            return {
                'success': False,
                'response': f"An error occurred: {str(e)}",
                'sources': []
            }

    def _search_documents(self, query: str) -> str:
        """Tool function for document search"""
        results = self.vector_store.search_similar(query, top_k=3)
        if results:
            context = "\n\n".join([f"Document: {r['metadata']['filename']}\n{r['document']}" for r in results])
            return f"Found {len(results)} relevant sections:\n{context}"
        return "No relevant documents found."

    def _generate_answer(self, context_and_query: str) -> str:
        """Tool function for answer generation"""
        # This would parse the context and query, then call LLM
        return "Answer generated based on context."

    def _summarize_content(self, content: str) -> str:
        """Tool function for content summarization"""
        summary_result = self.llm.generate_summary(content)
        if summary_result['success']:
            return summary_result['summary']
        return "Error generating summary."
```

### 7. Main Application (`app.py`)

```python
import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import tempfile
import os

from config import Config
from src.core.document_processor import DocumentProcessor
from src.core.vector_store import ChromaVectorStore
from src.core.embedding_generator import EmbeddingGenerator
from src.core.llm_integration import LLMIntegration
from src.core.rag_agent import RAGAgent
from src.ui.file_uploader import FileUploader
from src.ui.query_interface import QueryInterface

# Page configuration
st.set_page_config(
    page_title="Contract AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .query-section {
        background: #e8f4f8;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .results-section {
        background: #f0f8e8;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""

    # Initialize configuration
    config = Config()
    if not config.validate_config():
        st.error("Configuration error: Please check your environment variables.")
        return

    # Initialize session state
    if 'rag_agent' not in st.session_state:
        initialize_components(config)

    # Main UI
    st.markdown('<h1 class="main-header">🤖 Contract AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2em; color: #7f8c8d;">Ask questions about your contracts and get accurate answers instantly</p>', unsafe_allow_html=True)

    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Document Upload")
        file_uploader = FileUploader(config)
        uploaded_files = file_uploader.render()

        if uploaded_files:
            with st.spinner("Processing documents..."):
                success = process_uploaded_files(uploaded_files, st.session_state.rag_agent)
                if success:
                    st.success("✅ Documents processed successfully!")
                else:
                    st.error("❌ Error processing documents.")

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="query-section">', unsafe_allow_html=True)
        st.header("❓ Ask Your Question")

        query_interface = QueryInterface()
        query = query_interface.render()

        if query and st.button("🔍 Search", type="primary"):
            with st.spinner("Searching documents..."):
                result = st.session_state.rag_agent.process_query(query)

                if result['success']:
                    st.session_state.last_result = result
                    st.rerun()
                else:
                    st.error(f"❌ {result['response']}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.header("📋 Results")

        if 'last_result' in st.session_state and st.session_state.last_result['success']:
            result = st.session_state.last_result

            # Display answer
            st.subheader("💡 Answer")
            st.write(result['response'])

            # Display sources
            if result['sources']:
                st.subheader("📚 Sources")
                for i, source in enumerate(result['sources'], 1):
                    with st.expander(f"Source {i}: {source['filename']}"):
                        st.write(f"**Similarity Score:** {source['similarity_score']:.3f}")
                        st.write(f"**Chunk ID:** {source['chunk_id']}")

            # Display usage statistics
            if result.get('usage'):
                st.subheader("📊 Usage Statistics")
                usage = result['usage']
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Prompt Tokens", usage.get('prompt_tokens', 0))
                with col_b:
                    st.metric("Completion Tokens", usage.get('completion_tokens', 0))
                with col_c:
                    st.metric("Total Tokens", usage.get('total_tokens', 0))

        st.markdown('</div>', unsafe_allow_html=True)

def initialize_components(config):
    """Initialize all RAG components"""
    try:
        # Initialize core components
        embedding_generator = EmbeddingGenerator(config)
        vector_store = ChromaVectorStore(config)
        llm_integration = LLMIntegration(config)

        # Initialize RAG agent
        rag_agent = RAGAgent(config, vector_store, llm_integration)

        # Store in session state
        st.session_state.rag_agent = rag_agent
        st.session_state.embedding_generator = embedding_generator
        st.session_state.vector_store = vector_store
        st.session_state.llm_integration = llm_integration

    except Exception as e:
        st.error(f"Error initializing components: {e}")

def process_uploaded_files(uploaded_files, rag_agent):
    """Process uploaded files and add to vector store"""
    try:
        document_processor = DocumentProcessor(rag_agent.config)

        processed_docs = []
        for uploaded_file in uploaded_files:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                # Process the file
                processed_doc = document_processor.process_file(tmp_file_path)
                processed_docs.append(processed_doc)
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)

        # Add processed documents to vector store
        if processed_docs:
            success = rag_agent.vector_store.add_documents(processed_docs)
            return success

        return False

    except Exception as e:
        st.error(f"Error processing files: {e}")
        return False

if __name__ == "__main__":
    main()
```

## Dependencies (`requirements.txt`)

```
streamlit>=1.28.0
streamlit-authenticator>=0.2.3
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.10
sentence-transformers>=2.2.2
chromadb>=0.4.0
groq>=0.4.1
python-dotenv>=1.0.0
PyPDF2>=3.0.1
python-docx>=1.1.0
numpy>=1.24.0
pandas>=2.0.0
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
```

## Environment Variables (`.env`)

```
# API Keys
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Application Settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=mixtral-8x7b-32768
CHROMA_PATH=./data/chroma_db
MAX_FILE_SIZE=52428800
SESSION_TIMEOUT=3600
```

## Deployment Configuration

### For Streamlit Cloud:
1. Create `packages.txt` for system dependencies
2. Set environment variables in Streamlit Cloud dashboard
3. Deploy the main `app.py` file

### For Local Development:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
streamlit run app.py
```

## Security Implementation

### Authentication (`src/ui/authentication.py`)

```python
import streamlit_authenticator as stauth
from typing import Dict, Any

class AuthenticationManager:
    """Manages user authentication"""

    def __init__(self, config):
        self.config = config
        self.authenticator = None
        self._setup_auth()

    def _setup_auth(self):
        """Setup authentication configuration"""
        # In production, load from secure storage
        users = {
            "admin": {
                "name": "Administrator",
                "password": stauth.Hasher(['admin123']).generate()[0],
                "email": "admin@example.com",
                "role": "admin"
            }
        }

        self.authenticator = stauth.Authenticate(
            credentials={'usernames': users},
            cookie_name='contract_ai_auth',
            key='contract_ai_key',
            cookie_expiry_days=30
        )

    def login(self):
        """Handle user login"""
        return self.authenticator.login('Login', 'main')

    def logout(self):
        """Handle user logout"""
        self.authenticator.logout('Logout', 'sidebar')
```

## Testing Structure

### Unit Tests (`tests/test_rag_agent.py`)

```python
import pytest
from unittest.mock import Mock, patch
from src.core.rag_agent import RAGAgent

class TestRAGAgent:
    """Test cases for RAG Agent"""

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.TOP_K_SIMILARITY = 5
        return config

    @pytest.fixture
    def mock_vector_store(self):
        vector_store = Mock()
        vector_store.search_similar.return_value = [
            {
                'document': 'Sample contract text',
                'metadata': {'filename': 'test.pdf', 'chunk_id': 0},
                'similarity_score': 0.85
            }
        ]
        return vector_store

    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.generate_response.return_value = {
            'success': True,
            'response': 'Sample answer',
            'usage': {'total_tokens': 100}
        }
        return llm

    def test_process_query_success(self, mock_config, mock_vector_store, mock_llm):
        """Test successful query processing"""
        agent = RAGAgent(mock_config, mock_vector_store, mock_llm)
        result = agent.process_query("What is the payment term?")

        assert result['success'] == True
        assert 'response' in result
        assert 'sources' in result
        mock_vector_store.search_similar.assert_called_once()
        mock_llm.generate_response.assert_called_once()

    def test_process_query_no_documents(self, mock_config, mock_vector_store, mock_llm):
        """Test query processing when no documents found"""
        mock_vector_store.search_similar.return_value = []
        agent = RAGAgent(mock_config, mock_vector_store, mock_llm)
        result = agent.process_query("What is the payment term?")

        assert result['success'] == False
        assert "No relevant documents found" in result['response']
```

## Performance Optimization

### Caching Strategy
- Implement Redis for query result caching
- Cache embeddings for frequently accessed documents
- Use LRU cache for vector search results

### Async Processing
- Use asyncio for document processing
- Background processing for large document uploads
- Streaming responses for long queries

### Monitoring and Logging
- Implement structured logging with loguru
- Add performance metrics collection
- Create health check endpoints

This implementation architecture provides a solid foundation for building the Contract AI Assistant RAG system with proper separation of concerns, comprehensive error handling, and scalability considerations.