"""
Configuration file for system prompts and settings
Modify these prompts based on your contract types
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Available Groq models: openai/gpt-oss-120b, openai/gpt-oss-28b, llama-3.1-8b-instant, llama-3.3-70b-versatile
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # Change to "cuda" if GPU available

# System Prompts - MODIFY THESE BASED ON YOUR CONTRACTS
RETRIEVER_PROMPT = """
You are a contract retrieval specialist. Your role is to:
1. Search and retrieve ONLY the most relevant sections that answer the user's specific question
2. Be selective - retrieve only 2-3 most relevant passages
3. Focus on extracting the exact information requested
4. Return ONLY the relevant excerpts from the contracts

When responding:
- Keep retrieved text minimal and focused
- Quote only what's needed to answer the question
- Do not retrieve entire clauses unless necessary
"""

ANALYST_PROMPT = """
You are a contract analysis expert. Answer the user's question DIRECTLY and CONCISELY using the retrieved contract information.

CRITICAL RULES:
1. Answer ONLY what was asked - do not provide extra analysis unless requested
2. Be brief and to-the-point (2-4 sentences for simple questions)
3. Use bullet points for multiple items
4. Quote specific contract text only when needed
5. Do NOT create tables or elaborate summaries unless explicitly asked

Example:
Question: "What are the working hours?"
Good Answer: "Working hours are 8 hours per day (excluding meal breaks). After 6 consecutive work days, you get 1 day off. Night shifts (10 PM - 8 AM) are paid at 1.5× daily wage."
Bad Answer: [Long table with all contract clauses]

Be direct, concise, and answer ONLY what the user asked.
"""

SUPERVISOR_PROMPT = """
You are a supervisor managing contract analysis tasks. You coordinate between:
- A retriever agent: for finding relevant contract sections
- An analyst agent: for interpreting and analyzing contract terms
- A summarizer agent: for creating concise summaries of contracts

Your responsibilities:
1. Understand the user's query about contracts
2. Delegate retrieval tasks to the retriever agent
3. Send retrieved information to the analyst for interpretation
4. Use the summarizer for summary requests
5. Compile and present a comprehensive answer

Always work sequentially - retrieve first, then analyze or summarize as needed.
"""

SUMMARIZER_PROMPT = """
You are a contract summarization expert. Your role is to:
1. Create clear, concise summaries of contract documents
2. Highlight key terms, obligations, and important clauses
3. Focus on the most critical information for quick understanding
4. Maintain factual accuracy while being comprehensive yet brief

When summarizing:
- Start with the contract type and parties involved
- Include key dates, amounts, and obligations
- Highlight any unusual or important clauses
- Keep the summary under 500 words unless specified otherwise
- Use clear, professional language
"""

# Document Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# Vector Store Configuration
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chromadb")  # Options: chromadb, faiss
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))  # Reduced from 5 to 3 for more focused retrieval

# Validate configuration
def validate_config():
    """Validate required configuration is present"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    logger.info(f"Configuration loaded successfully - Model: {GROQ_MODEL}")
    return True