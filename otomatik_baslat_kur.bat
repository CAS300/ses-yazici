@echo off
setlocal
set "APP_DIR=%~dp0"
set "LAUNCHER=%APP_DIR%baslat_arkaplan.vbs"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Ses Yazıcı.lnk"

if not exist "%LAUNCHER%" (
    echo baslat_arkaplan.vbs bulunamadi.
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $shortcut = $ws.CreateShortcut($env:SHORTCUT); $shortcut.TargetPath = (Join-Path $env:SystemRoot 'System32\wscript.exe'); $shortcut.Arguments = '"' + $env:LAUNCHER + '"'; $shortcut.WorkingDirectory = $env:APP_DIR.TrimEnd('\'); $shortcut.Save()"
if errorlevel 1 exit /b 1

echo Otomatik baslatma kuruldu: "%SHORTCUT%"
endlocal
