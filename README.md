# PDF Header Processor - Batch Edition

A powerful tool for extracting and replacing headers in multiple PDF files with batch processing, progress tracking, and comprehensive logging.

## Features

- ✅ **Batch Processing**: Process multiple PDFs in parallel or sequentially
- ✅ **Header Extraction**: Automatically detect and extract headers from PDFs
- ✅ **Text Replacement**: Replace headers with custom text
- ✅ **Progress Tracking**: Real-time progress updates and statistics
- ✅ **Logging**: Detailed logs for each processed file
- ✅ **Dry Run Mode**: Preview changes before applying them
- ✅ **Configuration-Based**: JSON config for replacements
- ✅ **Error Handling**: Robust error handling and recovery

## Installation

```bash
git clone https://github.com/docsparker/pdf-header-processor.git
cd pdf-header-processor
pip install -r requirements.txt
```

## Quick Start

### 1. Create a Config File

```json
{
  "replacements": {
    "Old Chapter Title": "New Chapter Title",
    "Old Section": "New Section",
    "Draft": "Final Version"
  },
  "output_dir": "./output",
  "num_workers": 4,
  "dry_run": false
}
```

### 2. Run Batch Processing

```bash
python batch_processor.py --config config.json --input-dir ./pdfs --output-dir ./output
```

### 3. Check Results

Processed PDFs will be in `./output` with detailed logs in `./logs`

## Usage

### Command Line

```bash
# Process all PDFs in a directory
python batch_processor.py --input-dir ./pdfs --config config.json

# Dry run (preview changes)
python batch_processor.py --input-dir ./pdfs --config config.json --dry-run

# Specify output directory
python batch_processor.py --input-dir ./pdfs --output-dir ./results --config config.json

# Set number of parallel workers
python batch_processor.py --input-dir ./pdfs --config config.json --workers 8
```

### Python API

```python
from batch_processor import PDFBatchProcessor

processor = PDFBatchProcessor(
    input_dir='./pdfs',
    output_dir='./output',
    config_file='config.json',
    num_workers=4
)

results = processor.process_all(dry_run=False)
print(f"Processed: {results['files_processed']} files")
print(f"Failed: {results['files_failed']} files")
```

## Configuration

See `config.example.json` for all available options.

### Config Options

```json
{
  "replacements": {},           # Dictionary of old_text -> new_text
  "output_dir": "./output",     # Output directory path
  "num_workers": 4,             # Number of parallel workers
  "dry_run": false,             # Preview changes without writing
  "lines_to_check": 5,          # Number of lines to check for headers
  "case_sensitive": true,       # Case-sensitive matching
  "use_regex": false,           # Enable regex pattern matching
  "backup_originals": true,     # Keep backup of originals
  "log_level": "INFO"           # Logging level
}
```

## File Structure

```
pdf-header-processor/
├── batch_processor.py          # Main batch processor
├── pdf_processor.py            # Core PDF processor
├── config.json                 # Configuration file
├── config.example.json         # Example configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── pdfs/                       # Input PDFs
├── output/                     # Processed PDFs
└── logs/                       # Processing logs
```

## Logging

Detailed logs are saved to `logs/batch_process_YYYY-MM-DD_HH-MM-SS.log`

Example log entry:
```
[2026-06-26 10:30:45] INFO: Processing document.pdf
[2026-06-26 10:30:46] INFO: Extracted 3 headers
[2026-06-26 10:30:47] ✓ document.pdf: 3 replacements
```

## Performance

- **Sequential**: ~2-5 seconds per PDF (depends on size)
- **Parallel (4 workers)**: ~1-2 seconds per PDF average
- **Parallel (8 workers)**: ~0.5-1 second per PDF average

## Examples

See `examples/` directory for sample configurations:

- `config_simple.json` - Basic text replacement
- `config_advanced.json` - Regex patterns with advanced options

## License

MIT
