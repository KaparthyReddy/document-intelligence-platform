from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, List
import logging
import numpy as np

logger = logging.getLogger(__name__)

class SentimentModel:
    """Sentiment analysis model using transformers"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.sentiment_pipeline = None
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    async def initialize(self):
        """Initialize sentiment analysis model"""
        try:
            # Use pipeline for easier inference
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=0 if self.device == "mps" else -1
            )
            
            logger.info(f"✅ Sentiment model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Sentiment model initialization failed: {e}")
            raise
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        
        Returns:
            {
                'label': str ('POSITIVE' or 'NEGATIVE'),
                'score': float,
                'sentiment': str ('positive', 'negative', 'neutral')
            }
        """
        try:
            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.sentiment_pipeline(text)[0]
            
            # Normalize result
            label = result['label']
            score = result['score']
            
            # Determine sentiment category
            if label == "POSITIVE" and score > 0.6:
                sentiment = "positive"
            elif label == "NEGATIVE" and score > 0.6:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                'label': label,
                'score': score,
                'sentiment': sentiment,
                'confidence': score
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'label': 'NEUTRAL',
                'score': 0.5,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def analyze_text_chunks(self, text: str, chunk_size: int = 500) -> Dict:
        """
        Analyze sentiment of long text by chunks
        
        Returns aggregated sentiment
        """
        try:
            # Split text into chunks
            words = text.split()
            chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            sentiments = []
            scores = []
            
            for chunk in chunks:
                if chunk.strip():
                    result = await self.analyze_sentiment(chunk)
                    sentiments.append(result['sentiment'])
                    scores.append(result['score'])
            
            # Aggregate results
            if not sentiments:
                return await self.analyze_sentiment(text)
            
            # Count sentiment occurrences
            positive_count = sentiments.count('positive')
            negative_count = sentiments.count('negative')
            neutral_count = sentiments.count('neutral')
            
            # Determine overall sentiment
            if positive_count > negative_count and positive_count > neutral_count:
                overall = 'positive'
            elif negative_count > positive_count and negative_count > neutral_count:
                overall = 'negative'
            else:
                overall = 'neutral'
            
            avg_score = np.mean(scores)
            
            return {
                'overall_sentiment': overall,
                'average_score': float(avg_score),
                'positive_chunks': positive_count,
                'negative_chunks': negative_count,
                'neutral_chunks': neutral_count,
                'total_chunks': len(sentiments),
                'chunk_sentiments': sentiments
            }
            
        except Exception as e:
            logger.error(f"Chunk sentiment analysis error: {e}")
            return await self.analyze_sentiment(text)
    
    async def get_emotion_distribution(self, text: str) -> Dict:
        """
        Get distribution of emotions in text
        (Simplified - using sentiment as proxy)
        """
        result = await self.analyze_text_chunks(text)
        
        total = result.get('total_chunks', 1)
        
        return {
            'positive_ratio': result.get('positive_chunks', 0) / total,
            'negative_ratio': result.get('negative_chunks', 0) / total,
            'neutral_ratio': result.get('neutral_chunks', 0) / total,
            'overall': result.get('overall_sentiment', 'neutral')
        }