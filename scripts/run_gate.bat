@echo off
if exist "%~dp0..\.venv\Scripts\python.exe" (
  "%~dp0..\.venv\Scripts\python.exe" "%~dp0remote_permission_gate.py"
) else (
  python "%~dp0remote_permission_gate.py"
)
