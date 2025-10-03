@echo off
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Starting Embedding Manager...
python embedding_manager.py

echo.
echo Press any key to exit...
pause >nul
