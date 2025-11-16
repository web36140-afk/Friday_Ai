"""
Smart NLP Engine - Advanced Natural Language Processing
Uses local models for intelligent context understanding
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import re


class SmartNLP:
    """
    Advanced NLP processor for ultra-intelligent context understanding
    Uses lightweight methods that work without heavy ML models
    """
    
    def __init__(self):
        self.initialized = False
        self.use_advanced_nlp = False
        
    def initialize(self):
        """Initialize NLP models (optional, fallback to rule-based)"""
        if self.initialized:
            return
            
        try:
            # Try to import advanced NLP libraries
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
                self.use_advanced_nlp = True
                logger.success("✓ Advanced NLP initialized (NLTK available)")
            except LookupError:
                try:
                    logger.info("📥 Downloading NLTK data (first time only)...")
                    nltk.download('punkt', quiet=True)
                    nltk.download('averaged_perceptron_tagger', quiet=True)
                    nltk.download('maxent_ne_chunker', quiet=True)
                    nltk.download('words', quiet=True)
                    self.use_advanced_nlp = True
                    logger.success("✓ NLTK data downloaded successfully")
                except Exception as download_error:
                    logger.warning(f"⚠️ NLTK download failed: {download_error}")
                    logger.info("→ Using rule-based NLP (works fine, just less advanced)")
                    self.use_advanced_nlp = False
        except ImportError:
            logger.info("ℹ️  NLTK not installed - using built-in rule-based NLP")
            logger.info("   (Install with: pip install nltk for enhanced features)")
            self.use_advanced_nlp = False
        except Exception as e:
            logger.warning(f"⚠️ NLP initialization issue: {e}")
            logger.info("→ Falling back to rule-based NLP")
            self.use_advanced_nlp = False
        
        self.initialized = True
    
    def extract_named_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities (people, places, organizations)
        Falls back to rule-based if NLP not available
        """
        entities = []
        
        if self.use_advanced_nlp:
            try:
                import nltk
                tokens = nltk.word_tokenize(text)
                tagged = nltk.pos_tag(tokens)
                chunks = nltk.ne_chunk(tagged)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity = {
                            'text': ' '.join(c[0] for c in chunk),
                            'type': chunk.label()
                        }
                        entities.append(entity)
            except Exception as e:
                logger.debug(f"NLP extraction failed, using fallback: {e}")
                return self._rule_based_entity_extraction(text)
        else:
            return self._rule_based_entity_extraction(text)
        
        return entities
    
    def _rule_based_entity_extraction(self, text: str) -> List[Dict[str, str]]:
        """
        Rule-based entity extraction (fast, no ML required)
        """
        entities = []
        
        # Common patterns
        patterns = {
            'LOCATION': r'\b(Nepal|India|China|America|Bangalore|Delhi|Mumbai|Kathmandu|London|Paris|Tokyo|New York)\b',
            'TECHNOLOGY': r'\b(Python|JavaScript|Java|C\+\+|AI|Machine Learning|ML|React|Node|Django)\b',
            'EDUCATION': r'\b(CSE|Engineering|Computer Science|University|College|School|MIT|Stanford)\b',
            'PERSON': r'\b(John|Mary|Robert|Sarah|David|Dipesh)\b',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': entity_type
                })
        
        return entities
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text (positive, negative, neutral)
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 
                         'best', 'fantastic', 'wonderful', 'awesome', 'perfect']
        
        # Negative indicators
        negative_words = ['bad', 'terrible', 'hate', 'worst', 'awful', 'horrible',
                         'poor', 'disappointing', 'useless', 'wrong']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text
        """
        if self.use_advanced_nlp:
            try:
                import nltk
                from nltk import word_tokenize, pos_tag
                from nltk.chunk import RegexpParser
                
                # Define grammar for key phrase extraction
                grammar = "NP: {<DT>?<JJ>*<NN.*>+}"
                parser = RegexpParser(grammar)
                
                tokens = word_tokenize(text)
                tagged = pos_tag(tokens)
                tree = parser.parse(tagged)
                
                phrases = []
                for subtree in tree.subtrees():
                    if subtree.label() == 'NP':
                        phrase = ' '.join(word for word, tag in subtree.leaves())
                        if len(phrase) > 3:  # Filter short phrases
                            phrases.append(phrase)
                
                return phrases[:5]  # Top 5 phrases
            except Exception as e:
                logger.debug(f"Key phrase extraction failed: {e}")
                return self._simple_key_phrases(text)
        else:
            return self._simple_key_phrases(text)
    
    def _simple_key_phrases(self, text: str) -> List[str]:
        """
        Simple key phrase extraction without NLP
        """
        # Split by common delimiters
        phrases = re.split(r'[.!?,;]', text)
        
        # Filter and clean
        key_phrases = []
        for phrase in phrases:
            phrase = phrase.strip()
            if 10 < len(phrase) < 100:  # Reasonable length
                key_phrases.append(phrase)
        
        return key_phrases[:5]
    
    def detect_question_type(self, text: str) -> str:
        """
        Detect the type of question being asked
        """
        text_lower = text.lower().strip()
        
        question_types = {
            'what': ['what', 'which'],
            'how': ['how'],
            'why': ['why'],
            'when': ['when'],
            'where': ['where'],
            'who': ['who', 'whom'],
            'yes_no': ['is', 'are', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should']
        }
        
        first_word = text_lower.split()[0] if text_lower.split() else ''
        
        for qtype, keywords in question_types.items():
            if first_word in keywords:
                return qtype
        
        return 'statement' if not text.endswith('?') else 'general_question'
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts (0-1)
        Simple Jaccard similarity without ML
        """
        # Convert to word sets
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def is_context_dependent(self, text: str) -> bool:
        """
        Check if text is heavily context-dependent
        """
        text_lower = text.lower()
        
        # Context-dependent indicators
        context_indicators = [
            r'\b(it|that|this|these|those|them)\b',
            r'\b(he|she|they|him|her)\b',
            r'^(yes|no|yeah|nope|sure|okay|ok)\b',
            r'^(more|tell me more|continue)\b',
            r'\b(there|here)\b',
            r'\b(then|now|before|after)\b'
        ]
        
        for pattern in context_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Short questions are often context-dependent
        if len(text.strip()) < 20 and '?' in text:
            return True
        
        return False


# Global instance
smart_nlp = SmartNLP()

