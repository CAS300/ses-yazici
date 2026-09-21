@echo off
title Ses Yazici
cd /d "%~dp0"
"C:\Users\esahi\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo =======================================================
    echo Uygulama bir hata ile karsilasti. Detaylar yukarida veya error.log dosyasindadir.
    echo =======================================================
    pause
)
