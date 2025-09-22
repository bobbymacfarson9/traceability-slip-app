@echo off
echo ========================================
echo   Egg Room Packing Predictor
echo ========================================
echo.
echo Choose an option:
echo 1. Get actuals for today's weekday
echo 2. Forecast next week (Mon-Fri)
echo 3. Forecast specific day for specific week
echo 4. Show help
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Getting actuals for the latest week file...
    python egg_packing_predictor.py actuals --day Mon
    echo.
    echo Press any key to continue...
    pause >nul
    exit /b
)

if "%choice%"=="2" (
    echo.
    echo Forecasting next week (Mon-Fri)...
    python egg_packing_predictor.py forecast-next-week --window 8 --alpha 0.7
    echo.
    echo Press any key to continue...
    pause >nul
    exit /b
)

if "%choice%"=="3" (
    echo.
    set /p day="Enter day (Mon/Tues/Wed/Thurs/Fri): "
    set /p week="Enter week number: "
    set /p year="Enter year: "
    echo.
    echo Forecasting %day% for week %week% of %year%...
    python egg_packing_predictor.py forecast-day --day %day% --week %week% --year %year% --window 8 --alpha 0.7
    echo.
    echo Press any key to continue...
    pause >nul
    exit /b
)

if "%choice%"=="4" (
    echo.
    python egg_packing_predictor.py --help
    echo.
    echo Press any key to continue...
    pause >nul
    exit /b
)

echo Invalid choice. Please run the script again.
pause
