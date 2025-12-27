from pathlib import Path
from typing import Dict, Optional
import logging
from datetime import datetime
import hashlib

from .pdf_handler import PDFHandler
from .excel_handler import ExcelHandler
from models import ocr_model

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processing orchestrator"""
    
    def __init__(self):
        self.pdf_handler = PDFHandler()
        self.excel_handler = ExcelHandler()
    
    async def process_document(self, file_path: str, filename: str) -> Dict:
        """
        Process any document type
        
        Returns comprehensive document data
        """
        try:
            file_path_obj = Path(file_path)
            file_ext = file_path_obj.suffix.lower()
            
            # Initialize result
            result = {
                'filename': filename,
                'file_path': str(file_path),
                'file_type': file_ext,
                'file_size': file_path_obj.stat().st_size,
                'processed_at': datetime.utcnow().isoformat(),
                'text_content': '',
                'metadata': {},
                'requires_ocr': False
            }
            
            # Process based on file type
            if file_ext == '.pdf':
                pdf_data = await self.pdf_handler.extract_text(file_path)
                result['text_content'] = pdf_data.get('text', '')
                result['metadata'] = pdf_data.get('metadata', {})
                result['total_pages'] = pdf_data.get('total_pages', 0)
                result['pages'] = pdf_data.get('pages', [])
                
                # Check if OCR needed
                if not result['text_content'] or len(result['text_content'].strip()) < 50:
                    result['requires_ocr'] = True
                    logger.info(f"PDF appears to be scanned, OCR required: {filename}")
            
            elif file_ext in ['.xlsx', '.xls', '.csv']:
                excel_data = await self.excel_handler.extract_data(file_path)
                result['text_content'] = excel_data.get('text', '')
                result['metadata'] = excel_data.get('summary', {})
                result['sheets'] = excel_data.get('sheets', [])
            
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                # Image file - use OCR
                result['requires_ocr'] = True
                result['metadata'] = {'type': 'image'}
            
            else:
                result['error'] = f"Unsupported file type: {file_ext}"
            
            # Generate document hash for deduplication
            result['document_hash'] = await self._generate_hash(file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {
                'filename': filename,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    async def apply_ocr(self, file_path: str) -> Dict:
        """
        Apply OCR to document
        """
        try:
            if not ocr_model:
                return {
                    'text': '',
                    'error': 'OCR model not initialized'
                }
            
            ocr_result = await ocr_model.extract_text_from_image(file_path)
            
            return {
                'text': ocr_result.get('text', ''),
                'confidence': ocr_result.get('confidence', 0.0),
                'blocks': ocr_result.get('blocks', []),
                'method': 'OCR'
            }
            
        except Exception as e:
            logger.error(f"OCR application error: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _generate_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file for deduplication"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Hash generation error: {e}")
            return ""
    
    async def extract_metadata(self, file_path: str) -> Dict:
        """
        Extract comprehensive metadata from document
        """
        file_path_obj = Path(file_path)
        
        metadata = {
            'filename': file_path_obj.name,
            'file_size': file_path_obj.stat().st_size,
            'file_type': file_path_obj.suffix,
            'created_at': datetime.fromtimestamp(file_path_obj.stat().st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(file_path_obj.stat().st_mtime).isoformat()
        }
        
        return metadata
    
    async def validate_document(self, file_path: str, max_size: int = 50 * 1024 * 1024) -> Dict:
        """
        Validate document before processing
        
        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        file_path_obj = Path(file_path)
        
        # Check file exists
        if not file_path_obj.exists():
            errors.append("File does not exist")
        
        # Check file size
        if file_path_obj.stat().st_size > max_size:
            errors.append(f"File size exceeds maximum ({max_size} bytes)")
        
        # Check file extension
        supported_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.xlsx', '.xls', '.csv']
        if file_path_obj.suffix.lower() not in supported_extensions:
            errors.append(f"Unsupported file type: {file_path_obj.suffix}")
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
        except Exception as e:
            errors.append(f"File is not readable: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }