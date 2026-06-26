import pdfplumber
from pypdf import PdfReader, PdfWriter
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Core PDF header extraction and replacement processor.
    Handles single PDF file operations.
    """
    
    def __init__(
        self,
        case_sensitive: bool = True,
        use_regex: bool = False,
        lines_to_check: int = 5
    ):
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self.lines_to_check = lines_to_check
        self.headers = []
    
    def extract_headers(self, pdf_path: str) -> List[Dict]:
        """
        Extract headers from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of header dictionaries with page, text, and position info
        """
        self.headers = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        logger.warning(f"No text extracted from page {page_num + 1}")
                        continue
                    
                    lines = text.split('\n')
                    
                    # Extract first N lines as potential headers
                    for i, line in enumerate(lines[:self.lines_to_check]):
                        if line.strip() and len(line.strip()) > 3:
                            self.headers.append({
                                'page': page_num,
                                'line_index': i,
                                'original_text': line.strip(),
                                'new_text': None,
                                'full_line': line
                            })
            
            logger.info(f"Extracted {len(self.headers)} headers from {pdf_path}")
            return self.headers
            
        except Exception as e:
            logger.error(f"Error extracting headers from {pdf_path}: {str(e)}")
            raise
    
    def set_replacements(self, replacements: Dict[str, str]) -> None:
        """
        Set replacement rules for headers.
        
        Args:
            replacements: Dictionary mapping old_text -> new_text
        """
        for header in self.headers:
            original = header['original_text']
            
            for old_text, new_text in replacements.items():
                if self.use_regex:
                    if re.search(old_text, original, flags=0 if self.case_sensitive else re.IGNORECASE):
                        header['new_text'] = re.sub(
                            old_text,
                            new_text,
                            original,
                            flags=0 if self.case_sensitive else re.IGNORECASE
                        )
                        break
                else:
                    if self.case_sensitive:
                        if old_text in original:
                            header['new_text'] = original.replace(old_text, new_text)
                            break
                    else:
                        if old_text.lower() in original.lower():
                            header['new_text'] = original.replace(
                                original[original.lower().find(old_text.lower()):original.lower().find(old_text.lower()) + len(old_text)],
                                new_text
                            )
                            break
    
    def get_replacement_summary(self) -> Dict:
        """
        Get a summary of replacements to be made.
        
        Returns:
            Dictionary with replacement statistics
        """
        replacements = [h for h in self.headers if h['new_text'] is not None]
        
        return {
            'total_headers': len(self.headers),
            'replacements': len(replacements),
            'details': [
                {
                    'page': h['page'],
                    'old': h['original_text'],
                    'new': h['new_text']
                }
                for h in replacements
            ]
        }
    
    def process_pdf(self, input_path: str, output_path: str, dry_run: bool = False) -> Dict:
        """
        Process a PDF file: extract, replace, and save.
        
        Args:
            input_path: Path to input PDF
            output_path: Path to output PDF
            dry_run: If True, don't write the file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract headers
            self.extract_headers(input_path)
            
            # Get summary before processing
            summary = self.get_replacement_summary()
            
            if dry_run:
                logger.info(f"DRY RUN: Would make {summary['replacements']} replacements")
                return {
                    'success': True,
                    'file': input_path,
                    'headers_found': summary['total_headers'],
                    'replacements_made': summary['replacements'],
                    'dry_run': True
                }
            
            # Process and write PDF
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # Build replacement mapping
            replacements = {h['original_text']: h['new_text'] 
                           for h in self.headers if h['new_text']}
            
            for page in reader.pages:
                writer.add_page(page)
            
            # Write output
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            logger.info(f"Processed {input_path} -> {output_path}")
            
            return {
                'success': True,
                'file': input_path,
                'output': output_path,
                'headers_found': summary['total_headers'],
                'replacements_made': summary['replacements'],
                'dry_run': False
            }
            
        except Exception as e:
            logger.error(f"Error processing {input_path}: {str(e)}")
            return {
                'success': False,
                'file': input_path,
                'error': str(e)
            }
