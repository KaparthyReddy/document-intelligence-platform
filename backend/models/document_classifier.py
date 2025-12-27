from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
from pathlib import Path
from typing import Dict, List
import logging
import re

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """Document type classifier"""
    
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.categories = [
            'invoice',
            'contract',
            'report',
            'letter',
            'form',
            'receipt',
            'statement',
            'other'
        ]
        
        # Keywords for rule-based classification
        self.category_keywords = {
            'invoice': ['invoice', 'bill', 'payment', 'due date', 'amount due', 'total', 'subtotal'],
            'contract': ['agreement', 'contract', 'terms', 'conditions', 'parties', 'whereas', 'hereby'],
            'report': ['report', 'summary', 'analysis', 'findings', 'conclusion', 'executive summary'],
            'letter': ['dear', 'sincerely', 'regards', 'yours truly', 'to whom it may concern'],
            'form': ['form', 'application', 'please fill', 'signature', 'date', 'checkbox'],
            'receipt': ['receipt', 'purchase', 'paid', 'transaction', 'reference number'],
            'statement': ['statement', 'balance', 'account', 'period', 'transactions'],
        }
    
    async def initialize(self):
        """Initialize classifier"""
        try:
            # Initialize TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            logger.info("✅ Document classifier initialized")
            
        except Exception as e:
            logger.error(f"❌ Classifier initialization failed: {e}")
            raise
    
    async def classify_document(self, text: str) -> Dict:
        """
        Classify document type based on content
        
        Returns:
            {
                'category': str,
                'confidence': float,
                'scores': Dict[str, float]
            }
        """
        try:
            # Use rule-based classification (keyword matching)
            scores = await self._keyword_based_classification(text)
            
            # Get top category
            if scores:
                top_category = max(scores.items(), key=lambda x: x[1])
                category = top_category[0]
                confidence = top_category[1]
            else:
                category = 'other'
                confidence = 0.0
            
            return {
                'category': category,
                'confidence': confidence,
                'scores': scores,
                'all_categories': self.categories
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'category': 'other',
                'confidence': 0.0,
                'scores': {},
                'error': str(e)
            }
    
    async def _keyword_based_classification(self, text: str) -> Dict[str, float]:
        """
        Classify using keyword matching
        """
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.category_keywords.items():
            # Count keyword occurrences
            count = sum(1 for keyword in keywords if keyword in text_lower)
            
            # Normalize by number of keywords
            score = count / len(keywords) if keywords else 0.0
            scores[category] = score
        
        # Normalize scores to sum to 1
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        return scores
    
    async def extract_document_metadata(self, text: str, category: str) -> Dict:
        """
        Extract category-specific metadata
        """
        metadata = {
            'category': category,
            'extracted_fields': {}
        }
        
        if category == 'invoice':
            metadata['extracted_fields'] = await self._extract_invoice_fields(text)
        elif category == 'contract':
            metadata['extracted_fields'] = await self._extract_contract_fields(text)
        elif category == 'receipt':
            metadata['extracted_fields'] = await self._extract_receipt_fields(text)
        
        return metadata
    
    async def _extract_invoice_fields(self, text: str) -> Dict:
        """Extract invoice-specific fields"""
        fields = {}
        
        # Extract invoice number
        invoice_pattern = r'invoice\s*#?\s*:?\s*(\w+)'
        invoice_match = re.search(invoice_pattern, text, re.IGNORECASE)
        if invoice_match:
            fields['invoice_number'] = invoice_match.group(1)
        
        # Extract amounts (simple pattern)
        amount_pattern = r'\$\s*(\d+[,\d]*\.?\d*)'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            fields['amounts'] = amounts
            fields['total_amount'] = amounts[-1] if amounts else None  # Last amount often total
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)
        if dates:
            fields['dates'] = dates
        
        return fields
    
    async def _extract_contract_fields(self, text: str) -> Dict:
        """Extract contract-specific fields"""
        fields = {}
        
        # Extract parties (simplified)
        parties_pattern = r'between\s+([A-Z][a-z\s]+)\s+and\s+([A-Z][a-z\s]+)'
        parties_match = re.search(parties_pattern, text)
        if parties_match:
            fields['parties'] = [parties_match.group(1), parties_match.group(2)]
        
        # Extract effective date
        effective_pattern = r'effective\s+(?:date\s*:?\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        effective_match = re.search(effective_pattern, text, re.IGNORECASE)
        if effective_match:
            fields['effective_date'] = effective_match.group(1)
        
        return fields
    
    async def _extract_receipt_fields(self, text: str) -> Dict:
        """Extract receipt-specific fields"""
        fields = {}
        
        # Extract transaction ID
        transaction_pattern = r'(?:transaction|reference|receipt)\s*#?\s*:?\s*(\w+)'
        transaction_match = re.search(transaction_pattern, text, re.IGNORECASE)
        if transaction_match:
            fields['transaction_id'] = transaction_match.group(1)
        
        # Extract amounts
        amount_pattern = r'\$\s*(\d+[,\d]*\.?\d*)'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            fields['amount'] = amounts[-1]  # Last amount usually the total
        
        return fields
    
    async def get_document_structure(self, text: str) -> Dict:
        """
        Analyze document structure
        """
        lines = text.split('\n')
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([l for l in lines if l.strip()]),
            'average_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
            'has_headers': await self._detect_headers(text),
            'has_tables': await self._detect_tables(text),
            'has_lists': await self._detect_lists(text)
        }
    
    async def _detect_headers(self, text: str) -> bool:
        """Detect if document has headers"""
        # Simple heuristic: lines in ALL CAPS or with consistent formatting
        lines = text.split('\n')
        header_count = sum(1 for line in lines if line.isupper() and len(line) > 5)
        return header_count > 2
    
    async def _detect_tables(self, text: str) -> bool:
        """Detect if document has tables"""
        # Look for patterns like | or consistent spacing
        return '|' in text or '\t' in text
    
    async def _detect_lists(self, text: str) -> bool:
        """Detect if document has lists"""
        # Look for bullet points or numbering
        list_patterns = [r'^\s*[\-\*\•]', r'^\s*\d+\.', r'^\s*\([a-z]\)']
        lines = text.split('\n')
        
        for pattern in list_patterns:
            if sum(1 for line in lines if re.match(pattern, line)) > 2:
                return True
        
        return False