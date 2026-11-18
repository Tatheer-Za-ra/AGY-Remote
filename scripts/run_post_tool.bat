@echo off
if exist "%~dp0..\.venv\Scripts\python.exe" (
  "%~dp0..\.venv\Scripts\python.exe" "%~dp0remote_post_tool.py"
) else (
  python "%~dp0remote_post_tool.py"
)
