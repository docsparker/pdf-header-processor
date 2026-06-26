import os
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm
import argparse
from pdf_processor import PDFProcessor


class PDFBatchProcessor:
    """
    Batch processor for handling multiple PDF files with header extraction and replacement.
    Supports parallel processing and comprehensive logging.
    """
    
    def __init__(
        self,
        input_dir: str,
        output_dir: str = None,
        config_file: str = None,
        num_workers: int = 4,
        log_dir: str = './logs'
    ):
        """
        Initialize the batch processor.
        
        Args:
            input_dir: Directory containing PDF files to process
            output_dir: Directory to save processed PDFs (defaults to input_dir/output)
            config_file: JSON config file with replacements and settings
            num_workers: Number of parallel workers
            log_dir: Directory for log files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if output_dir else self.input_dir / 'output'
        self.num_workers = num_workers
        self.log_dir = Path(log_dir)
        self.config = {}
        
        # Create directories
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Load config
        if config_file:
            self.load_config(config_file)
        
        self.logger = logging.getLogger(__name__)
    
    def _setup_logging(self) -> None:
        """
        Setup logging configuration.
        """
        log_file = self.log_dir / f"batch_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self, config_file: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to config JSON file
        """
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            logging.info(f"Loaded config from {config_file}")
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
            raise
    
    def get_pdf_files(self, recursive: bool = False) -> List[Path]:
        """
        Get all PDF files from input directory.
        
        Args:
            recursive: If True, search subdirectories
            
        Returns:
            List of PDF file paths
        """
        pattern = '**/*.pdf' if recursive else '*.pdf'
        pdf_files = list(self.input_dir.glob(pattern))
        logging.info(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        return sorted(pdf_files)
    
    def _process_single_pdf(self, pdf_file: Path, dry_run: bool = False) -> Dict:
        """
        Process a single PDF file.
        
        Args:
            pdf_file: Path to PDF file
            dry_run: If True, don't write output
            
        Returns:
            Processing result dictionary
        """
        try:
            processor = PDFProcessor(
                case_sensitive=self.config.get('case_sensitive', True),
                use_regex=self.config.get('use_regex', False),
                lines_to_check=self.config.get('lines_to_check', 5)
            )
            
            # Extract headers
            processor.extract_headers(str(pdf_file))
            
            # Apply replacements
            if self.config.get('replacements'):
                processor.set_replacements(self.config['replacements'])
            
            # Determine output path
            relative_path = pdf_file.relative_to(self.input_dir)
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process PDF
            result = processor.process_pdf(str(pdf_file), str(output_path), dry_run=dry_run)
            
            return result
            
        except Exception as e:
            logging.error(f"Error processing {pdf_file.name}: {str(e)}")
            return {
                'success': False,
                'file': str(pdf_file),
                'error': str(e)
            }
    
    def process_all(self, dry_run: bool = False, recursive: bool = False) -> Dict:
        """
        Process all PDF files in the input directory.
        
        Args:
            dry_run: If True, preview changes without writing
            recursive: If True, search subdirectories
            
        Returns:
            Dictionary with processing summary
        """
        pdf_files = self.get_pdf_files(recursive=recursive)
        
        if not pdf_files:
            logging.warning("No PDF files found to process")
            return {'success': True, 'files_processed': 0, 'results': []}
        
        results = []
        total_replacements = 0
        failed_files = []
        
        logging.info(f"Starting batch processing of {len(pdf_files)} files with {self.num_workers} workers")
        logging.info(f"Dry run: {dry_run}")
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {
                executor.submit(self._process_single_pdf, pdf_file, dry_run): pdf_file
                for pdf_file in pdf_files
            }
            
            with tqdm(total=len(futures), desc="Processing PDFs") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        total_replacements += result.get('replacements_made', 0)
                        logging.info(f"✓ {Path(result['file']).name}: {result.get('replacements_made', 0)} replacements")
                    else:
                        failed_files.append(result['file'])
                        logging.error(f"✗ {Path(result['file']).name}: {result.get('error', 'Unknown error')}")
                    
                    pbar.update(1)
        
        summary = {
            'success': True,
            'files_processed': len([r for r in results if r['success']]),
            'files_failed': len(failed_files),
            'total_replacements': total_replacements,
            'dry_run': dry_run,
            'results': results,
            'failed_files': failed_files
        }
        
        self._print_summary(summary)
        return summary
    
    def _print_summary(self, summary: Dict) -> None:
        """
        Print a summary of processing results.
        
        Args:
            summary: Summary dictionary from process_all()
        """
        logging.info("\n" + "=" * 60)
        logging.info("BATCH PROCESSING SUMMARY")
        logging.info("=" * 60)
        logging.info(f"Files Processed: {summary['files_processed']}")
        logging.info(f"Files Failed: {summary['files_failed']}")
        logging.info(f"Total Replacements: {summary['total_replacements']}")
        logging.info(f"Dry Run: {summary['dry_run']}")
        
        if summary['failed_files']:
            logging.warning("\nFailed Files:")
            for file in summary['failed_files']:
                logging.warning(f"  - {file}")
        
        logging.info("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Batch process PDF files for header extraction and replacement'
    )
    parser.add_argument('--input-dir', required=True, help='Input directory with PDF files')
    parser.add_argument('--output-dir', help='Output directory (default: input-dir/output)')
    parser.add_argument('--config', required=True, help='Config JSON file with replacements')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--recursive', action='store_true', help='Search subdirectories')
    parser.add_argument('--log-dir', default='./logs', help='Log directory')
    
    args = parser.parse_args()
    
    processor = PDFBatchProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config_file=args.config,
        num_workers=args.workers,
        log_dir=args.log_dir
    )
    
    results = processor.process_all(dry_run=args.dry_run, recursive=args.recursive)
    
    # Exit with appropriate code
    exit(0 if results['files_failed'] == 0 else 1)


if __name__ == '__main__':
    main()
