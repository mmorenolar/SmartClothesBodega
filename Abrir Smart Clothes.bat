@echo off
REM Abre Smart Clothes con doble clic.
cd /d "%~dp0src"
REM Pillow permite usar fotos JPG. Si falta, se instala una sola vez.
python -c "import PIL" 2>nul || (
  echo Instalando Pillow para las fotos JPG, espera un momento...
  python -m pip install --user --quiet pillow
)
python -m smartclothes
if errorlevel 1 (
  echo.
  echo No se pudo abrir Smart Clothes. Saca una captura de esta ventana.
  pause
)
