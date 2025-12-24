@echo off
title RobloxCheatz Discord Bot
echo ========================================
echo   RobloxCheatz Verification Bot
echo ========================================
echo.

cd /d "%~dp0"

echo Starting bot...
echo.

python bot.py

echo.
echo Bot stopped. Press any key to exit...
pause >nul
