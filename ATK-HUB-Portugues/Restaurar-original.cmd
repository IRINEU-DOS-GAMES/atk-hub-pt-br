@echo off
title ATK HUB - Restaurar idioma original
if exist "%~dp0ATK-HUB-Portugues.exe" goto compilado
py -3 "%~dp0aplicar.py" --restore
echo.
pause
exit /b
:compilado
set "ATK_PTBR_INSTALLER=%~dp0ATK-HUB-Portugues.exe"
powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference = 'Stop'; $process = Start-Process -FilePath $env:ATK_PTBR_INSTALLER -ArgumentList '--restore' -Verb RunAs -Wait -PassThru; exit $process.ExitCode"
exit /b %errorlevel%
