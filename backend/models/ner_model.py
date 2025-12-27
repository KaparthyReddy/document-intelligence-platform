import spacy
from typing import List, Dict
import logging
from collections import defaultdict

from config import settings

logger = logging.getLogger(__name__)

class NERModel:
    """Named Entity Recognition model"""
    
    def __init__(self):
        self.nlp = None
        self.model_name = settings.SPACY_MODEL
        self.confidence_threshold = settings.NER_CONFIDENCE_THRESHOLD
    
    async def initialize(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"✅ spaCy model '{self.model_name}' loaded")
            
        except OSError:
            logger.error(f"❌ spaCy model '{self.model_name}' not found. Run: python -m spacy download {self.model_name}")
            raise
    
    async def extract_entities(self, text: str) -> Dict:
        """
        Extract named entities from text
        
        Returns:
            {
                'entities': List[Dict],
                'entity_counts': Dict[str, int],
                'unique_entities': Dict[str, List[str]]
            }
        """
        try:
            doc = self.nlp(text)
            
            entities = []
            entity_counts = defaultdict(int)
            unique_entities = defaultdict(set)
            
            for ent in doc.ents:
                entity_data = {
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'description': spacy.explain(ent.label_)
                }
                
                entities.append(entity_data)
                entity_counts[ent.label_] += 1
                unique_entities[ent.label_].add(ent.text)
            
            # Convert sets to lists for JSON serialization
            unique_entities = {k: list(v) for k, v in unique_entities.items()}
            
            return {
                'entities': entities,
                'total_entities': len(entities),
                'entity_counts': dict(entity_counts),
                'unique_entities': unique_entities,
                'entity_types': list(entity_counts.keys())
            }
            
        except Exception as e:
            logger.error(f"NER extraction error: {e}")
            return {
                'entities': [],
                'total_entities': 0,
                'entity_counts': {},
                'unique_entities': {},
                'entity_types': [],
                'error': str(e)
            }
    
    async def extract_relationships(self, text: str) -> List[Dict]:
        """
        Extract relationships between entities
        """
        try:
            doc = self.nlp(text)
            relationships = []
            
            # Simple relationship extraction based on dependency parsing
            for sent in doc.sents:
                entities_in_sent = [(ent.text, ent.label_) for ent in sent.ents]
                
                if len(entities_in_sent) >= 2:
                    # Find verb connecting entities
                    for token in sent:
                        if token.pos_ == "VERB":
                            # Check if verb connects entities
                            subjects = [child for child in token.children if child.dep_ in ("nsubj", "nsubjpass")]
                            objects = [child for child in token.children if child.dep_ in ("dobj", "pobj")]
                            
                            for subj in subjects:
                                for obj in objects:
                                    relationships.append({
                                        'subject': subj.text,
                                        'relation': token.text,
                                        'object': obj.text,
                                        'sentence': sent.text
                                    })
            
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship extraction error: {e}")
            return []
    
    async def extract_dates(self, text: str) -> List[Dict]:
        """Extract date entities"""
        try:
            doc = self.nlp(text)
            dates = []
            
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    dates.append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            return dates
            
        except Exception as e:
            logger.error(f"Date extraction error: {e}")
            return []
    
    async def extract_key_phrases(self, text: str, top_n: int = 10) -> List[Dict]:
        """Extract key noun phrases"""
        try:
            doc = self.nlp(text)
            
            # Extract noun chunks
            noun_chunks = []
            for chunk in doc.noun_chunks:
                noun_chunks.append({
                    'text': chunk.text,
                    'root': chunk.root.text,
                    'pos': chunk.root.pos_
                })
            
            # Sort by length (longer phrases often more meaningful)
            noun_chunks.sort(key=lambda x: len(x['text'].split()), reverse=True)
            
            return noun_chunks[:top_n]
            
        except Exception as e:
            logger.error(f"Key phrase extraction error: {e}")
            return []