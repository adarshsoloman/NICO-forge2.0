"""
Sentence Splitting Module

Splits text into sentences based on language-specific punctuation.
"""

import re
import config


def split_sentences(text: str, language: str = 'english') -> list[str]:
    """
    Split text into sentences based on punctuation.
    
    Args:
        text: Text to split
        language: 'english' or 'hindi' (determines delimiters)
    
    Returns:
        List of sentence strings (whitespace stripped, empties removed)
    """
    # Choose delimiter pattern based on language
    if language.lower() == 'hindi':
        pattern = config.HINDI_SENTENCE_DELIMITERS
    else:
        pattern = config.ENGLISH_SENTENCE_DELIMITERS
    
    # Split on delimiters
    sentences = re.split(pattern, text)
    
    # Strip whitespace and filter out empty strings
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences
