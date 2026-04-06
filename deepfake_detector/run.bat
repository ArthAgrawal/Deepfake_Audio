@echo off
REM VoiceGuard Startup Script (Windows)

REM Load environment variables from .env
if exist .env (
    for /f "delims== tokens=1,2" %%A in (.env) do (
        if not "%%A"=="" (
            if not "%%A:~0,1%%"=="#" (
                set %%A=%%B
            )
        )
    )
) else (
    echo WARNING: .env file not found. Using defaults.
    echo Copy .env.example to .env and configure.
)

REM Set defaults if not in .env
if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=8000

echo.
echo 🚀 Starting VoiceGuard
echo    Host: %HOST%
echo    Port: %PORT%
echo    URL: http://localhost:%PORT%
echo.

REM Run with uvicorn
python -m uvicorn main:app --host %HOST% --port %PORT% --workers 1
pause
