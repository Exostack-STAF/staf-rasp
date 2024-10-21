@echo off
setlocal
set SCRIPT_DIR=%~dp0
bash -c "cd %SCRIPT_DIR% && ./STMF-RASP.sh"
