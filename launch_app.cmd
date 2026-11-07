@echo off
cd /d "%~dp0"
if exist "%USERPROFILE%\miniconda3\envs\ai\python.exe" (
  "%USERPROFILE%\miniconda3\envs\ai\python.exe" -B -m morpholab gui
) else (
  python -B -m morpholab gui
)
if errorlevel 1 pause
