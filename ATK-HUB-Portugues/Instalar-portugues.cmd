@echo off
title ATK HUB - Portugues (Brasil)
if exist "%~dp0ATK-HUB-Portugues.exe" goto compilado
echo Instalador local de idioma. O ATK HUB sera fechado automaticamente, se estiver aberto.
echo Depois, ele so sera reaberto se ja estava aberto antes.
py -3 "%~dp0aplicar.py" --apply
echo.
pause
exit /b
:compilado
set "ATK_PTBR_INSTALLER=%~dp0ATK-HUB-Portugues.exe"
powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference = 'Stop'; $process = Start-Process -FilePath $env:ATK_PTBR_INSTALLER -ArgumentList '--apply' -Verb RunAs -Wait -PassThru; exit $process.ExitCode"
exit /b %errorlevel%
