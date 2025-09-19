@echo off
cd /d "%~dp0\.."
for /r %%i in (*.pyc) do del "%%i"
for /f "delims=" %%i in ('dir /s /b /a:d __pycache__ 2^>nul') do rmdir /s /q "%%i"
