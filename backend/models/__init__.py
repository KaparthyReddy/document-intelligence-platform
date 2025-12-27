"""
ML Models package for Document Intelligence Platform
Handles OCR, NER, sentiment analysis, classification, and knowledge graphs
"""

from .ocr_model import OCRModel
from .ner_model import NERModel
from .sentiment_model import SentimentModel
from .document_classifier import DocumentClassifier
from .knowledge_graph import KnowledgeGraphBuilder

# Global model instances
ocr_model = None
ner_model = None
sentiment_model = None
doc_classifier = None
kg_builder = None

async def initialize_models():
    """Initialize all ML models"""
    global ocr_model, ner_model, sentiment_model, doc_classifier, kg_builder
    
    print("🔧 Initializing OCR model...")
    ocr_model = OCRModel()
    await ocr_model.initialize()
    
    print("🔧 Initializing NER model...")
    ner_model = NERModel()
    await ner_model.initialize()
    
    print("🔧 Initializing Sentiment model...")
    sentiment_model = SentimentModel()
    await sentiment_model.initialize()
    
    print("🔧 Initializing Document Classifier...")
    doc_classifier = DocumentClassifier()
    await doc_classifier.initialize()
    
    print("🔧 Initializing Knowledge Graph builder...")
    kg_builder = KnowledgeGraphBuilder()
    
    print("✅ All models initialized successfully!")

__all__ = [
    'OCRModel',
    'NERModel', 
    'SentimentModel',
    'DocumentClassifier',
    'KnowledgeGraphBuilder',
    'ocr_model',
    'ner_model',
    'sentiment_model',
    'doc_classifier',
    'kg_builder',
    'initialize_models'
]