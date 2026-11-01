@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment tidak ditemukan. Jalankan setup_windows.bat terlebih dahulu.
  pause
  exit /b 1
)
if not exist "tools\mpv-2.dll" if not exist "tools\libmpv-2.dll" (
  echo [WARNING] mpv DLL belum ada di tools. EXE membutuhkan libmpv di tools atau PATH.
)
if not exist "web\index.html" (
  echo Folder web atau file web\index.html tidak ditemukan.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name YouTubeLite --add-data "web;web" --add-data "logo.webp;." main.py
if errorlevel 1 (
  echo Build gagal.
  pause
  exit /b 1
)
if not exist "dist\YouTubeLite\_internal\web\index.html" (
  echo Build gagal: aset web tidak ditemukan di folder internal.
  pause
  exit /b 1
)
if not exist "dist\YouTubeLite\tools" mkdir "dist\YouTubeLite\tools"
if exist "tools\*" xcopy "tools\*" "dist\YouTubeLite\tools\" /E /I /Y >nul
if exist "tools\mpv-2.dll" copy /Y "tools\mpv-2.dll" "dist\YouTubeLite\" >nul
if exist "tools\libmpv-2.dll" copy /Y "tools\libmpv-2.dll" "dist\YouTubeLite\" >nul
if exist "tools\yt-dlp.exe" copy /Y "tools\yt-dlp.exe" "dist\YouTubeLite\" >nul
if exist "tools\ffmpeg.exe" copy /Y "tools\ffmpeg.exe" "dist\YouTubeLite\" >nul
echo.
echo Hasil: dist\YouTubeLite\YouTubeLite.exe
pause
