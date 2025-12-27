import easyocr
import pytesseract
from PIL import Image
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from config import settings

logger = logging.getLogger(__name__)

class OCRModel:
    """OCR model for extracting text from images"""
    
    def __init__(self):
        self.reader = None
        self.engine = settings.OCR_ENGINE
        self.languages = settings.OCR_LANGUAGES
    
    async def initialize(self):
        """Initialize OCR engine"""
        try:
            if self.engine == "easyocr":
                # Initialize EasyOCR (better for general use)
                self.reader = easyocr.Reader(self.languages, gpu=False)
                logger.info("✅ EasyOCR initialized")
            else:
                # Tesseract is already available via pytesseract
                logger.info("✅ Tesseract OCR ready")
                
        except Exception as e:
            logger.error(f"❌ OCR initialization failed: {e}")
            raise
    
    async def extract_text_from_image(self, image_path: str) -> Dict:
        """
        Extract text from image
        
        Returns:
            {
                'text': str,
                'confidence': float,
                'blocks': List[Dict]
            }
        """
        try:
            if self.engine == "easyocr":
                return await self._extract_with_easyocr(image_path)
            else:
                return await self._extract_with_tesseract(image_path)
                
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'blocks': [],
                'error': str(e)
            }
    
    async def _extract_with_easyocr(self, image_path: str) -> Dict:
        """Extract text using EasyOCR"""
        results = self.reader.readtext(image_path)
        
        # Parse results
        all_text = []
        blocks = []
        total_confidence = 0.0
        
        for (bbox, text, confidence) in results:
            all_text.append(text)
            blocks.append({
                'text': text,
                'confidence': confidence,
                'bbox': bbox
            })
            total_confidence += confidence
        
        avg_confidence = total_confidence / len(results) if results else 0.0
        
        return {
            'text': ' '.join(all_text),
            'confidence': avg_confidence,
            'blocks': blocks,
            'num_blocks': len(blocks)
        }
    
    async def _extract_with_tesseract(self, image_path: str) -> Dict:
        """Extract text using Tesseract"""
        image = Image.open(image_path)
        
        # Get detailed data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Extract text and blocks
        blocks = []
        all_text = []
        confidences = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Filter out low confidence
                text = data['text'][i].strip()
                if text:
                    all_text.append(text)
                    confidences.append(float(data['conf'][i]))
                    
                    blocks.append({
                        'text': text,
                        'confidence': float(data['conf'][i]) / 100.0,
                        'bbox': [
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ]
                    })
        
        avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
        
        return {
            'text': ' '.join(all_text),
            'confidence': avg_confidence,
            'blocks': blocks,
            'num_blocks': len(blocks)
        }
    
    async def preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image for better OCR results
        
        Returns path to preprocessed image
        """
        try:
            image = Image.open(image_path)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Save preprocessed image
            preprocessed_path = str(Path(image_path).with_suffix('.preprocessed.png'))
            image.save(preprocessed_path)
            
            return preprocessed_path
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return image_path  # Return original if preprocessing fails