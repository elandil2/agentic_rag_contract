#!/bin/bash
# Quick start script for Linux/Mac

echo "======================================"
echo "Contract RAG Analysis System"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -f "rag_env/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python3 -m venv rag_env"
    echo "Then run: source rag_env/bin/activate"
    echo "Then run: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source rag_env/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and add your GROQ_API_KEY"
    exit 1
fi

# Run the application
echo "[INFO] Starting Streamlit application..."
echo ""
streamlit run main.py