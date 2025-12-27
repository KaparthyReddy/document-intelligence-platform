from typing import Dict, List
import logging
from datetime import datetime

from database.mongodb import mongodb
from database.redis_cache import redis_client

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Orchestrate all document analysis operations"""
    
    def __init__(self):
        pass
    
    async def analyze_document(self, document_id: str, text: str, force: bool = False) -> Dict:
        """
        Perform comprehensive analysis on document
        
        Args:
            document_id: Document ID
            text: Extracted text content
            force: Force re-analysis even if cached
        
        Returns:
            Complete analysis results
        """
        # Import models here after they've been initialized
        from models import ner_model, sentiment_model, doc_classifier, kg_builder
        try:
            # Check cache first
            if not force:
                cached = await redis_client.get_cached_analysis(document_id, 'complete')
                if cached:
                    logger.info(f"Returning cached analysis for document {document_id}")
                    return cached
            
            logger.info(f"Starting comprehensive analysis for document {document_id}")
            
            # Run all analyses in parallel (if async)
            results = {
                'document_id': document_id,
                'analyzed_at': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
            
            # 1. Named Entity Recognition
            logger.info("Running NER...")
            ner_results = await ner_model.extract_entities(text)
            results['entities'] = ner_results
            
            # 2. Sentiment Analysis
            logger.info("Running sentiment analysis...")
            sentiment_results = await sentiment_model.analyze_text_chunks(text)
            results['sentiment'] = sentiment_results
            
            # 3. Document Classification
            logger.info("Running document classification...")
            classification_results = await doc_classifier.classify_document(text)
            results['classification'] = classification_results
            
            # 4. Extract relationships
            logger.info("Extracting entity relationships...")
            relationships = await ner_model.extract_relationships(text)
            results['relationships'] = relationships
            
            # 5. Build knowledge graph
            logger.info("Building knowledge graph...")
            kg_data = await kg_builder.build_graph(
                ner_results.get('entities', []),
                relationships
            )
            results['knowledge_graph'] = kg_data
            
            # 6. Extract dates and timeline
            logger.info("Extracting timeline...")
            dates = await ner_model.extract_dates(text)
            results['dates'] = dates
            results['timeline'] = await self._build_timeline(dates, ner_results.get('entities', []))
            
            # 7. Extract key phrases
            logger.info("Extracting key phrases...")
            key_phrases = await ner_model.extract_key_phrases(text)
            results['key_phrases'] = key_phrases
            
            # 8. Document structure analysis
            logger.info("Analyzing document structure...")
            structure = await doc_classifier.get_document_structure(text)
            results['structure'] = structure
            
            # 9. Extract category-specific metadata
            if classification_results.get('category'):
                metadata = await doc_classifier.extract_document_metadata(
                    text,
                    classification_results['category']
                )
                results['extracted_metadata'] = metadata
            
            # 10. Text statistics
            results['statistics'] = await self._calculate_text_statistics(text)
            
            # Save results to database
            await self._save_analysis_results(document_id, results)
            
            # Cache results
            await redis_client.cache_analysis(document_id, 'complete', results)
            
            logger.info(f"✅ Analysis completed for document {document_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis engine error: {e}")
            return {
                'document_id': document_id,
                'status': 'failed',
                'error': str(e),
                'analyzed_at': datetime.utcnow().isoformat()
            }
    
    async def _build_timeline(self, dates: List[Dict], entities: List[Dict]) -> List[Dict]:
        """
        Build timeline from dates and events
        """
        timeline = []
        
        for date_item in dates:
            # Find entities near this date in the text
            date_start = date_item['start']
            date_end = date_item['end']
            
            # Find entities within 100 characters of the date
            nearby_entities = [
                e for e in entities
                if abs(e['start'] - date_start) < 100
            ]
            
            timeline.append({
                'date': date_item['text'],
                'position': date_start,
                'related_entities': [e['text'] for e in nearby_entities[:5]],
                'context': 'event'  # Could be enhanced with more context
            })
        
        # Sort by position in document
        timeline.sort(key=lambda x: x['position'])
        
        return timeline
    
    async def _calculate_text_statistics(self, text: str) -> Dict:
        """
        Calculate various text statistics
        """
        words = text.split()
        sentences = text.split('.')
        
        return {
            'total_characters': len(text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words)),
            'vocabulary_richness': len(set(words)) / len(words) if words else 0
        }
    
    async def _save_analysis_results(self, document_id: str, results: Dict):
        """
        Save analysis results to database
        """
        try:
            # Save entities
            if results.get('entities', {}).get('entities'):
                entities_to_save = [
                    {
                        'document_id': document_id,
                        'entity_text': entity['text'],
                        'entity_type': entity['label'],
                        'start_pos': entity['start'],
                        'end_pos': entity['end'],
                        'description': entity.get('description', ''),
                        'created_at': datetime.utcnow()
                    }
                    for entity in results['entities']['entities']
                ]
                await mongodb.insert_entities(entities_to_save)
            
            # Save main analysis
            analysis_doc = {
                'document_id': document_id,
                'analysis_type': 'complete',
                'sentiment': results.get('sentiment', {}),
                'classification': results.get('classification', {}),
                'statistics': results.get('statistics', {}),
                'structure': results.get('structure', {}),
                'analyzed_at': datetime.utcnow()
            }
            await mongodb.insert_analysis(analysis_doc)
            
            # Update document with analysis status
            await mongodb.update_document(document_id, {
                'analysis_status': 'completed',
                'analyzed_at': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
    
    async def get_insights(self, document_id: str) -> Dict:
        """
        Generate high-level insights from analysis
        """
        try:
            # Get analysis from cache or database
            analysis = await redis_client.get_cached_analysis(document_id, 'complete')
            
            if not analysis:
                # Fetch from database
                db_analysis = await mongodb.get_analysis(document_id)
                if not db_analysis:
                    return {'error': 'No analysis found'}
                
                analysis = db_analysis[0] if isinstance(db_analysis, list) else db_analysis
            
            insights = {
                'document_id': document_id,
                'summary': await self._generate_summary(analysis),
                'key_findings': await self._extract_key_findings(analysis),
                'recommendations': await self._generate_recommendations(analysis),
                'confidence_score': await self._calculate_confidence(analysis)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
            return {'error': str(e)}
    
    async def _generate_summary(self, analysis: Dict) -> str:
        """
        Generate natural language summary
        """
        summary_parts = []
        
        # Document type
        if analysis.get('classification', {}).get('category'):
            category = analysis['classification']['category']
            confidence = analysis['classification'].get('confidence', 0)
            summary_parts.append(
                f"This appears to be a {category} document (confidence: {confidence:.2%})."
            )
        
        # Sentiment
        if analysis.get('sentiment', {}).get('overall_sentiment'):
            sentiment = analysis['sentiment']['overall_sentiment']
            summary_parts.append(f"The overall sentiment is {sentiment}.")
        
        # Entities
        if analysis.get('entities', {}).get('total_entities'):
            total = analysis['entities']['total_entities']
            types = len(analysis['entities'].get('entity_types', []))
            summary_parts.append(
                f"The document contains {total} entities across {types} different types."
            )
        
        # Key statistics
        if analysis.get('statistics', {}).get('total_words'):
            words = analysis['statistics']['total_words']
            summary_parts.append(f"The document has approximately {words} words.")
        
        return ' '.join(summary_parts)
    
    async def _extract_key_findings(self, analysis: Dict) -> List[str]:
        """
        Extract key findings from analysis
        """
        findings = []
        
        # Most common entity types
        if analysis.get('entities', {}).get('entity_counts'):
            counts = analysis['entities']['entity_counts']
            top_type = max(counts.items(), key=lambda x: x[1]) if counts else None
            if top_type:
                findings.append(f"Most frequent entity type: {top_type[0]} ({top_type[1]} occurrences)")
        
        # Sentiment insights
        if analysis.get('sentiment', {}).get('positive_chunks', 0) > 0:
            pos = analysis['sentiment']['positive_chunks']
            total = analysis['sentiment'].get('total_chunks', 1)
            findings.append(f"{(pos/total)*100:.1f}% of the content has positive sentiment")
        
        # Structure insights
        if analysis.get('structure', {}).get('has_tables'):
            findings.append("Document contains structured tables")
        
        if analysis.get('structure', {}).get('has_lists'):
            findings.append("Document contains lists or enumerated items")
        
        # Timeline insights
        if analysis.get('dates') and len(analysis['dates']) > 0:
            findings.append(f"Document references {len(analysis['dates'])} specific dates")
        
        return findings
    
    async def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """
        Generate actionable recommendations
        """
        recommendations = []
        
        # Based on document type
        category = analysis.get('classification', {}).get('category')
        if category == 'invoice':
            recommendations.append("Review payment terms and due dates")
            recommendations.append("Verify amounts and line items")
        elif category == 'contract':
            recommendations.append("Review all terms and conditions carefully")
            recommendations.append("Check effective dates and renewal clauses")
        
        # Based on sentiment
        sentiment = analysis.get('sentiment', {}).get('overall_sentiment')
        if sentiment == 'negative':
            recommendations.append("Pay attention to concerns or issues raised in the document")
        
        # Based on entities
        if analysis.get('entities', {}).get('entity_types'):
            if 'PERSON' in analysis['entities']['entity_types']:
                recommendations.append("Review mentions of key individuals")
            if 'ORG' in analysis['entities']['entity_types']:
                recommendations.append("Verify organizational relationships")
        
        return recommendations
    
    async def _calculate_confidence(self, analysis: Dict) -> float:
        """
        Calculate overall confidence score of the analysis
        """
        scores = []
        
        # Classification confidence
        if analysis.get('classification', {}).get('confidence'):
            scores.append(analysis['classification']['confidence'])
        
        # Sentiment confidence
        if analysis.get('sentiment', {}).get('average_score'):
            scores.append(analysis['sentiment']['average_score'])
        
        # OCR confidence (if available)
        if analysis.get('ocr_confidence'):
            scores.append(analysis['ocr_confidence'])
        
        return sum(scores) / len(scores) if scores else 0.5
    
    async def compare_documents(self, doc_id1: str, doc_id2: str) -> Dict:
        """
        Compare two documents
        """
        try:
            # Get both analyses
            analysis1 = await redis_client.get_cached_analysis(doc_id1, 'complete')
            analysis2 = await redis_client.get_cached_analysis(doc_id2, 'complete')
            
            if not analysis1 or not analysis2:
                return {'error': 'One or both documents not analyzed'}
            
            comparison = {
                'document_1': doc_id1,
                'document_2': doc_id2,
                'similarities': [],
                'differences': [],
                'shared_entities': [],
                'unique_entities_1': [],
                'unique_entities_2': []
            }
            
            # Compare categories
            cat1 = analysis1.get('classification', {}).get('category')
            cat2 = analysis2.get('classification', {}).get('category')
            
            if cat1 == cat2:
                comparison['similarities'].append(f"Both are {cat1} documents")
            else:
                comparison['differences'].append(f"Different types: {cat1} vs {cat2}")
            
            # Compare sentiment
            sent1 = analysis1.get('sentiment', {}).get('overall_sentiment')
            sent2 = analysis2.get('sentiment', {}).get('overall_sentiment')
            
            if sent1 == sent2:
                comparison['similarities'].append(f"Both have {sent1} sentiment")
            else:
                comparison['differences'].append(f"Different sentiment: {sent1} vs {sent2}")
            
            # Compare entities
            entities1 = set(e['text'] for e in analysis1.get('entities', {}).get('entities', []))
            entities2 = set(e['text'] for e in analysis2.get('entities', {}).get('entities', []))
            
            comparison['shared_entities'] = list(entities1 & entities2)
            comparison['unique_entities_1'] = list(entities1 - entities2)
            comparison['unique_entities_2'] = list(entities2 - entities1)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Document comparison error: {e}")
            return {'error': str(e)}