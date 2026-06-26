@echo off
REM Script to run batch PDF processing on Windows

echo PDF Batch Header Processor
echo ==========================

REM Install dependencies if needed
python -c "import pdfplumber" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run with command line arguments
python batch_processor.py ^
    --input-dir ./pdfs ^
    --output-dir ./output ^
    --config config.json ^
    --workers 4 ^
    --log-dir ./logs

echo Done! Check .\output for processed files and .\logs for details.
pause
