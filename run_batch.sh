#!/bin/bash
# Script to run batch PDF processing

echo "PDF Batch Header Processor"
echo "========================="

# Install dependencies if needed
if ! python -c "import pdfplumber" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run with command line arguments
python batch_processor.py \
    --input-dir ./pdfs \
    --output-dir ./output \
    --config config.json \
    --workers 4 \
    --log-dir ./logs

echo "Done! Check ./output for processed files and ./logs for details."
