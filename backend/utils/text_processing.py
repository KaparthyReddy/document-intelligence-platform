import re
from typing import List, Dict, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str, remove_extra_spaces: bool = True) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text
        remove_extra_spaces: Remove multiple consecutive spaces
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove control characters except newline and tab
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Normalize whitespace
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def remove_urls(text: str) -> str:
    """
    Remove URLs from text
    """
    url_pattern = r'https?://\S+|www\.\S+'
    return re.sub(url_pattern, '', text)


def remove_emails(text: str) -> str:
    """
    Remove email addresses from text
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(email_pattern, '', text)


def remove_phone_numbers(text: str) -> str:
    """
    Remove phone numbers from text
    """
    # Simple phone number patterns
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
        r'\b\d{10}\b'  # 1234567890
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    
    return text


def extract_keywords(text: str, top_n: int = 10, min_word_length: int = 3) -> List[Dict]:
    """
    Extract keywords from text using frequency analysis
    
    Args:
        text: Input text
        top_n: Number of top keywords to return
        min_word_length: Minimum length of words to consider
    
    Returns:
        List of {word, count, score} dicts
    """
    try:
        # Clean text
        text = clean_text(text.lower())
        
        # Remove common stop words
        stop_words = get_stop_words()
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text)
        
        # Filter words
        filtered_words = [
            word for word in words
            if len(word) >= min_word_length and word not in stop_words
        ]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        # Get top N
        top_words = word_counts.most_common(top_n)
        
        # Calculate scores (normalized frequency)
        max_count = top_words[0][1] if top_words else 1
        
        keywords = [
            {
                'word': word,
                'count': count,
                'score': count / max_count
            }
            for word, count in top_words
        ]
        
        return keywords
        
    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        return []


def get_stop_words() -> Set[str]:
    """
    Get common English stop words
    """
    return {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
        'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below',
        'between', 'both', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 'down',
        'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have',
        'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his',
        'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me',
        'might', 'more', 'most', 'must', 'my', 'myself', 'no', 'nor', 'not', 'now',
        'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves',
        'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than',
        'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
        'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until',
        'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while',
        'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your', 'yours',
        'yourself', 'yourselves'
    }


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Create a simple extractive summary
    
    Args:
        text: Input text
        max_sentences: Maximum number of sentences in summary
    
    Returns:
        Summary text
    """
    try:
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple heuristic: take first, middle, and last sentences
        # (More sophisticated: use TF-IDF, TextRank, etc.)
        
        if max_sentences == 1:
            return sentences[0] + '.'
        elif max_sentences == 2:
            return sentences[0] + '. ' + sentences[-1] + '.'
        else:
            indices = [0, len(sentences) // 2, -1]
            summary_sentences = [sentences[i] for i in indices[:max_sentences]]
            return ' '.join(summary_sentences) + '.'
        
    except Exception as e:
        logger.error(f"Text summarization error: {e}")
        return text[:500] + '...' if len(text) > 500 else text


def count_sentences(text: str) -> int:
    """
    Count number of sentences in text
    """
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def count_words(text: str) -> int:
    """
    Count number of words in text
    """
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def count_paragraphs(text: str) -> int:
    """
    Count number of paragraphs in text
    """
    paragraphs = text.split('\n\n')
    return len([p for p in paragraphs if p.strip()])


def extract_sentences_with_keyword(text: str, keyword: str, context_size: int = 1) -> List[str]:
    """
    Extract sentences containing a specific keyword with context
    
    Args:
        text: Input text
        keyword: Keyword to search for
        context_size: Number of sentences before/after to include
    
    Returns:
        List of sentence groups containing the keyword
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    results = []
    keyword_lower = keyword.lower()
    
    for i, sentence in enumerate(sentences):
        if keyword_lower in sentence.lower():
            # Get context
            start = max(0, i - context_size)
            end = min(len(sentences), i + context_size + 1)
            
            context = ' '.join(sentences[start:end])
            results.append(context)
    
    return results


def truncate_text(text: str, max_length: int = 500, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    """
    if len(text) <= max_length:
        return text
    
    # Try to break at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace to single spaces
    """
    return ' '.join(text.split())


def remove_punctuation(text: str, keep_periods: bool = False) -> str:
    """
    Remove punctuation from text
    """
    if keep_periods:
        pattern = r'[^\w\s.]'
    else:
        pattern = r'[^\w\s]'
    
    return re.sub(pattern, '', text)


def extract_quoted_text(text: str) -> List[str]:
    """
    Extract text within quotes
    """
    # Match text in double or single quotes
    pattern = r'["\']([^"\']+)["\']'
    quotes = re.findall(pattern, text)
    return quotes


def calculate_readability_score(text: str) -> Dict:
    """
    Calculate simple readability metrics
    
    Returns Flesch Reading Ease approximation
    """
    words = count_words(text)
    sentences = count_sentences(text)
    
    if sentences == 0 or words == 0:
        return {
            'score': 0,
            'level': 'unknown'
        }
    
    # Approximate syllables (rough estimate)
    syllables = sum(estimate_syllables(word) for word in re.findall(r'\b\w+\b', text))
    
    # Flesch Reading Ease (simplified)
    if sentences > 0 and words > 0:
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    else:
        score = 0
    
    # Interpret score
    if score >= 90:
        level = 'Very Easy'
    elif score >= 80:
        level = 'Easy'
    elif score >= 70:
        level = 'Fairly Easy'
    elif score >= 60:
        level = 'Standard'
    elif score >= 50:
        level = 'Fairly Difficult'
    elif score >= 30:
        level = 'Difficult'
    else:
        level = 'Very Difficult'
    
    return {
        'score': round(score, 2),
        'level': level,
        'words': words,
        'sentences': sentences,
        'avg_words_per_sentence': round(words / sentences, 2) if sentences > 0 else 0
    }


def estimate_syllables(word: str) -> int:
    """
    Rough syllable estimation for a word
    """
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel
    
    # Adjust for silent 'e'
    if word.endswith('e'):
        count -= 1
    
    # Ensure at least one syllable
    if count == 0:
        count = 1
    
    return count
