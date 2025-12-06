"""
Quality Filter Module

Filters and validates English-Hindi chunk pairs based on various
quality metrics to ensure high-quality training data.
"""

import re
from typing import Dict, Tuple


def calculate_length_ratio(eng_chunk: str, hin_chunk: str) -> float:
    """
    Calculate the character length ratio between Hindi and English.
    
    Typical ratio for Hindi/English is 1.2-2.2
    
    Args:
        eng_chunk: English text
        hin_chunk: Hindi text
    
    Returns:
        Ratio (hindi_length / english_length)
    """
    if not eng_chunk or len(eng_chunk) == 0:
        return 0.0
    
    return len(hin_chunk) / len(eng_chunk)


def validate_hindi_script(text: str, min_percentage: float = 0.3) -> bool:
    """
    Validate that text contains sufficient Hindi Devanagari characters.
    
    Args:
        text: Text to validate
        min_percentage: Minimum percentage of Hindi characters required
    
    Returns:
        True if valid, False otherwise
    """
    if not text:
        return False
    
    # Count Hindi characters (Devanagari script range)
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    
    if total_chars == 0:
        return False
    
    ratio = hindi_chars / total_chars
    return ratio >= min_percentage


def is_valid_chunk_pair(eng_chunk: str, hin_chunk: str) -> Tuple[bool, str]:
    """
    Validate an English-Hindi chunk pair.
    
    Args:
        eng_chunk: English text
        hin_chunk: Hindi text
    
    Returns:
        Tuple of (is_valid, reason)
    """
    # Rule 1: Minimum length check
    if len(eng_chunk) < 20:
        return False, "English chunk too short (<20 chars)"
    
    if len(hin_chunk) < 20:
        return False, "Hindi chunk too short (<20 chars)"
    
    # Rule 2: Maximum length check (avoid concatenated chunks)
    if len(eng_chunk) > 1000:
        return False, "English chunk too long (>1000 chars)"
    
    if len(hin_chunk) > 1500:
        return False, "Hindi chunk too long (>1500 chars)"
    
    # Rule 3: Length ratio check
    ratio = calculate_length_ratio(eng_chunk, hin_chunk)
    if ratio < 0.5 or ratio > 3.5:
        return False, f"Length ratio out of range ({ratio:.2f})"
    
    # Rule 4: Hindi script validation
    if not validate_hindi_script(hin_chunk):
        return False, "Insufficient Hindi characters"
    
    # Rule 5: Check for metadata pollution
    metadata_keywords = [
        'Reprint 20', '© Wikipedia', 'For more details',
        'Exercise', 'Question', 'Answer'
    ]
    
    for keyword in metadata_keywords:
        if keyword in eng_chunk[:50]:  # Check first 50 chars
            return False, f"Metadata detected: {keyword}"
    
    # Rule 6: Empty or whitespace-only chunks
    if not eng_chunk.strip() or not hin_chunk.strip():
        return False, "Empty or whitespace-only chunk"
    
    return True, "PASS"


def calculate_quality_score(eng_chunk: str, hin_chunk: str) -> float:
    """
    Calculate a quality score for a chunk pair (0.0 to 1.0).
    
    Factors:
    - Length ratio (optimal: 1.2-2.2)
    - Character diversity
    - Hindi script percentage
    
    Args:
        eng_chunk: English text
        hin_chunk: Hindi text
    
    Returns:
        Quality score between 0.0 and 1.0
    """
    score = 1.0
    
    # Factor 1: Length ratio (20% weight)
    ratio = calculate_length_ratio(eng_chunk, hin_chunk)
    if 1.2 <= ratio <= 2.2:
        ratio_score = 1.0
    elif 0.8 <= ratio < 1.2 or 2.2 < ratio <= 2.8:
        ratio_score = 0.7
    else:
        ratio_score = 0.3
    score *= (0.8 + 0.2 * ratio_score)
    
    # Factor 2: Hindi script percentage (30% weight)
    hindi_chars = sum(1 for c in hin_chunk if '\u0900' <= c <= '\u097F')
    total_chars = len(hin_chunk.replace(' ', '').replace('\n', ''))
    if total_chars > 0:
        hindi_ratio = hindi_chars / total_chars
        if hindi_ratio >= 0.5:
            hindi_score = 1.0
        elif hindi_ratio >= 0.3:
            hindi_score = 0.7
        else:
            hindi_score = 0.3
    else:
        hindi_score = 0.0
    score *= (0.7 + 0.3 * hindi_score)
    
    # Factor 3: Length appropriateness (20% weight)
    ideal_length = 150
    eng_len = len(eng_chunk)
    if 80 <= eng_len <= 400:
        length_score = 1.0
    elif 40 <= eng_len < 80 or 400 < eng_len <= 600:
        length_score = 0.7
    else:
        length_score = 0.4
    score *= (0.8 + 0.2 * length_score)
    
    # Factor 4: Character diversity (10% weight)
    unique_chars_eng = len(set(eng_chunk.lower()))
    unique_chars_hin = len(set(hin_chunk))
    
    if unique_chars_eng >= 20 and unique_chars_hin >= 20:
        diversity_score = 1.0
    elif unique_chars_eng >= 10 and unique_chars_hin >= 10:
        diversity_score = 0.7
    else:
        diversity_score = 0.4
    score *= (0.9 + 0.1 * diversity_score)
    
    return round(score, 3)


def get_quality_label(score: float) -> str:
    """
    Get quality label based on score.
    
    Args:
        score: Quality score (0.0-1.0)
    
    Returns:
        Quality label: EXCELLENT, GOOD, FAIR, or POOR
    """
    if score >= 0.85:
        return "EXCELLENT"
    elif score >= 0.70:
        return "GOOD"
    elif score >= 0.50:
        return "FAIR"
    else:
        return "POOR"
