@echo off
setlocal
cd /d "%~dp0"
py -3.13 -m venv .venv
if errorlevel 1 (
  echo Python 3.13 launcher tidak tersedia, mencoba python...
  python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo Gagal membuat lingkungan Python.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Instalasi dependensi gagal.
  pause
  exit /b 1
)
echo.
echo Siap. Letakkan yt-dlp.exe dan DLL libmpv beserta dependensi di folder tools.
echo Jalankan run_windows.bat untuk membuka aplikasi.
pause
