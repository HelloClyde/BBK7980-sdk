@echo off
pushd "%~dp0"
python -X utf8 tools\build.py examples\hello
if errorlevel 1 goto end
python -X utf8 tools\build.py examples\diagnostics
if errorlevel 1 goto end
python -X utf8 tools\build.py examples\minesweeper
if errorlevel 1 goto end
python -X utf8 tools\build.py examples\storage
if errorlevel 1 goto end
python -X utf8 tools\build.py examples\music
:end
popd
pause
