import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class PDFHandler:
    """Handle PDF document processing"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    async def extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF
        
        Returns:
            {
                'text': str,
                'pages': List[Dict],
                'metadata': Dict
            }
        """
        try:
            # Try pdfplumber first (better for complex layouts)
            result = await self._extract_with_pdfplumber(pdf_path)
            
            if not result['text']:
                # Fallback to PyPDF2
                result = await self._extract_with_pypdf2(pdf_path)
            
            return result
            
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            return {
                'text': '',
                'pages': [],
                'metadata': {},
                'error': str(e)
            }
    
    async def _extract_with_pdfplumber(self, pdf_path: str) -> Dict:
        """Extract text using pdfplumber"""
        all_text = []
        pages_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            metadata = pdf.metadata or {}
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ''
                
                # Extract tables if present
                tables = page.extract_tables()
                
                pages_data.append({
                    'page_number': page_num,
                    'text': page_text,
                    'has_tables': len(tables) > 0,
                    'num_tables': len(tables),
                    'width': page.width,
                    'height': page.height
                })
                
                all_text.append(page_text)
        
        return {
            'text': '\n\n'.join(all_text),
            'pages': pages_data,
            'total_pages': len(pages_data),
            'metadata': metadata,
            'method': 'pdfplumber'
        }
    
    async def _extract_with_pypdf2(self, pdf_path: str) -> Dict:
        """Extract text using PyPDF2"""
        all_text = []
        pages_data = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = pdf_reader.metadata or {}
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text() or ''
                
                pages_data.append({
                    'page_number': page_num,
                    'text': page_text,
                    'has_tables': False,
                    'num_tables': 0
                })
                
                all_text.append(page_text)
        
        return {
            'text': '\n\n'.join(all_text),
            'pages': pages_data,
            'total_pages': len(pages_data),
            'metadata': {k: str(v) for k, v in metadata.items()},
            'method': 'PyPDF2'
        }
    
    async def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """
        Extract tables from PDF
        
        Returns list of tables (each table is a list of rows)
        """
        try:
            all_tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    all_tables.extend(tables)
            
            return all_tables
            
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
            return []
    
    async def get_pdf_info(self, pdf_path: str) -> Dict:
        """Get PDF document information"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    'num_pages': len(pdf_reader.pages),
                    'metadata': {},
                    'is_encrypted': pdf_reader.is_encrypted,
                    'file_size': Path(pdf_path).stat().st_size
                }
                
                if pdf_reader.metadata:
                    info['metadata'] = {
                        k: str(v) for k, v in pdf_reader.metadata.items()
                    }
                
                return info
                
        except Exception as e:
            logger.error(f"PDF info extraction error: {e}")
            return {
                'error': str(e)
            }
    
    async def extract_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Extract images from PDF (simplified)
        
        Returns list of saved image paths
        """
        # Note: Full image extraction requires additional libraries like pdf2image
        # This is a placeholder for future implementation
        logger.warning("Image extraction from PDF not fully implemented")
        return []
    
    async def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Detect if PDF is scanned (image-based) vs text-based
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first few pages
                for page in pdf.pages[:3]:
                    text = page.extract_text() or ''
                    # If we get substantial text, it's not purely scanned
                    if len(text.strip()) > 100:
                        return False
                
                # If minimal text found, likely scanned
                return True
                
        except Exception as e:
            logger.error(f"Scanned PDF detection error: {e}")
            return False