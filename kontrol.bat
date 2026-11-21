@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo.
  echo  Python bulunamadi.
  echo  https://www.python.org/downloads/ adresinden Python 3.9 veya ustunu kur.
  echo  Kurulumun ilk ekraninda "Add Python to PATH" kutusunu ISARETLE.
  echo.
  pause
  exit /b 1
)
%PY% -m usta kontrol
pause
