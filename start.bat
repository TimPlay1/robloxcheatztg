@echo off
title RobloxCheatz Discord + Telegram Bot
echo ========================================
echo   RobloxCheatz Verification Bot
echo   LOCAL DEVELOPMENT MODE
echo ========================================
echo.

cd /d "%~dp0"

REM Load environment variables from .env.local file
if exist ".env.local" (
    echo Loading environment from .env.local...
    for /f "usebackq tokens=1,* delims==" %%a in (".env.local") do (
        set "%%a=%%b"
    )
) else (
    echo ERROR: .env.local file not found!
    echo Please create .env.local with your environment variables.
    echo.
    echo Example .env.local:
    echo DISCORD_TOKEN=your_token
    echo GUILD_ID=your_guild_id
    echo TELEGRAM_TOKEN=your_telegram_token
    echo ...
    pause
    exit /b 1
)

echo Environment variables loaded!
echo.
echo Starting Discord + Telegram bot...
echo.

python bot.py

echo.
echo Bot stopped. Press any key to exit...
pause >nul
