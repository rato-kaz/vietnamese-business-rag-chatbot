@echo off
echo Starting Vietnamese Business Registration RAG Chatbot...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo .env file not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env file with your API keys before running again.
    pause
    exit /b 1
)

REM Run the setup and run script
python setup_and_run.py

pause