@echo off
REM Abre Smart Clothes con doble clic.
cd /d "%~dp0src"
python -m smartclothes
if errorlevel 1 (
  echo.
  echo No se pudo abrir Smart Clothes. Saca una captura de esta ventana.
  pause
)
