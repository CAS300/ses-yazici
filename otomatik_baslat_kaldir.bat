@echo off
setlocal
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Ses Yazıcı.lnk"

if exist "%SHORTCUT%" del /f /q "%SHORTCUT%"
if exist "%SHORTCUT%" (
    echo Otomatik baslatma kisayolu kaldirilamadi.
    exit /b 1
)

echo Otomatik baslatma kaldirildi.
endlocal
