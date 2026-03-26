@echo off
title Data Janitor CLI
echo.
echo  =============================================
echo   DATA JANITOR CLI - Setting up environment...
echo  =============================================
echo.
pip install -r requirements.txt --quiet 2>nul
echo.
python main.py
pause
