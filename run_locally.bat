@echo off
echo ========================================================
echo       NetSage AI - Packet Tracer Troubleshooting
echo ========================================================
echo.

echo [1/3] Running Deterministic Rule Checker...
python scripts\rule_checker.py
echo.

echo [2/3] Validating Dashboard & 30 Case Dataset...
python scripts\build_dashboard.py
echo.

echo [3/3] Launching NetSage AI Web Interface on http://localhost:8000 ...
start "" "http://localhost:8000"

echo Starting local server on port 8000... (Press Ctrl+C to stop)
python -m http.server 8000
