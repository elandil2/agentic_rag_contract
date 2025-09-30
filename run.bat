@echo off
REM Quick start script for Windows

echo ======================================
echo Contract RAG Analysis System
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "rag_env\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv rag_env
    echo Then run: rag_env\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call rag_env\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and add your GROQ_API_KEY
    pause
    exit /b 1
)

REM Run the application
echo [INFO] Starting Streamlit application...
echo.
streamlit run main.py

pause