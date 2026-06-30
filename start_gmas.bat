@echo off
setlocal

echo ============================================================
echo  GMAS v1.1.0 -- Grants Management Assistant
echo ============================================================
echo.

:: Activate conda environment
call conda activate gmas 2>nul
if errorlevel 1 (
    echo ERROR: Could not activate conda environment "gmas".
    echo Run: conda env create -f environment.yml
    pause
    exit /b 1
)

:: Ensure src package is importable
set PYTHONPATH=%CD%

:: Seed the database (idempotent -- safe to run every time)
echo [1/2] Seeding database...
python -m src.db.seed_data
if errorlevel 1 (
    echo ERROR: Database seed failed. Check logs\gmas.log for details.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting Streamlit app...
echo       Open your browser to: http://localhost:8501
echo       Press Ctrl+C to stop.
echo.

streamlit run src/app/main.py --server.headless false

endlocal
