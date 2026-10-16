@echo off
cd /d "%~dp0"
py -3 backend\start_portal.py
if errorlevel 1 pause
