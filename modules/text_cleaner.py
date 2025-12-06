"""
Text Cleaning Module

Handles OCR artifacts, spacing issues, and Unicode normalization
for improved text quality in bilingual datasets.
"""

import re
import unicodedata


def clean_english_text(text: str) -> str:
    """
    Clean English text extracted from PDFs.
    
    Fixes:
    - Broken spacing (e.g., "Po we r" -> "Power")
    - Extra whitespace
    - Page numbers and headers
    
    Args:
        text: Raw extracted English text
    
    Returns:
        Cleaned English text
    """
    if not text:
        return ""
    
    # Remove leading page numbers (e.g., "4\n")
    text = re.sub(r'^\d+\s*\n', '', text, flags=re.MULTILINE)
    
    # Fix broken spacing in words (common OCR issue)
    # Match: letter-space-letter when space shouldn't be there
    # Be careful not to merge actual separate words
    text = re.sub(r'([a-z])\s([a-z])\s([a-z])', r'\1\2\3', text)
    
    # Fix hyphenated words with spaces (e.g., "sha r ing" -> "sharing")
    text = re.sub(r'(\w)\s+-\s+(\w)', r'\1-\2', text)
    
    # Normalize multiple spaces to single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Normalize multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'©\s*Wikipedia', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Reprint\s+\d{4}-\d{2}', '', text)
    text = re.sub(r'For more details.*?(?:\n|$)', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_hindi_text(text: str) -> str:
    """
    Clean Hindi text extracted from PDFs.
    
    Fixes:
    - Duplicate vowel marks (e.g., "सााझेदाारी" -> "साझेदारी")
    - Extra whitespace
    - Page numbers
    - Unicode normalization
    
    Args:
        text: Raw extracted Hindi text
    
    Returns:
        Cleaned Hindi text
    """
    if not text:
        return ""
    
    # Remove leading page numbers
    text = re.sub(r'^\d+\s*\n', '', text, flags=re.MULTILINE)
    
    # Fix duplicate vowel marks (common in poor OCR)
    # Hindi vowel marks: ा ि ी ु ू ृ े ै ो ौ ं ः
    vowel_marks = r'[ा-ौं-ः]'
    text = re.sub(f'({vowel_marks})\\1+', r'\1', text)
    
    # Fix duplicate consonants (less common but possible)
    # Pattern: क + ् + क → क्क (proper)
    # But duplicates like ककक should become single क
    text = re.sub(r'([क-ह])\1{2,}', r'\1', text)
    
    # Normalize Unicode (NFC normalization)
    text = unicodedata.normalize('NFC', text)
    
    # Normalize multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Normalize multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common artifacts
    text = re.sub(r'Reprint\s+\d{4}-\d{2}', '', text)
    text = re.sub(r'विकीपीडिया', '', text)  # Wikipedia in Hindi
    
    # Strip whitespace
    text = text.strip()
    
    return text


def clean_chunk(chunk: str, language: str = 'english') -> str:
    """
    Clean a text chunk based on language.
    
    Args:
        chunk: Text chunk to clean
        language: 'english' or 'hindi'
    
    Returns:
        Cleaned chunk
    """
    if language.lower() == 'hindi':
        return clean_hindi_text(chunk)
    else:
        return clean_english_text(chunk)


def is_chunk_valid(chunk: str, language: str = 'english') -> bool:
    """
    Check if a chunk has meaningful content.
    
    Args:
        chunk: Text chunk to validate
        language: 'english' or 'hindi'
    
    Returns:
        True if chunk is valid, False otherwise
    """
    if not chunk or len(chunk.strip()) < 10:
        return False
    
    # Check for metadata-only chunks
    metadata_patterns = [
        r'^Chapter\s+\d+$',
        r'^Page\s+\d+$',
        r'^Exercise\s+\d+$',
        r'^\d+$',  # Just a number
        r'^©',  # Copyright symbol
    ]
    
    for pattern in metadata_patterns:
        if re.match(pattern, chunk.strip(), re.IGNORECASE):
            return False
    
    # For Hindi, check if it actually contains Hindi characters
    if language.lower() == 'hindi':
        hindi_chars = sum(1 for c in chunk if '\u0900' <= c <= '\u097F')
        if hindi_chars < 5:  # At least 5 Hindi characters
            return False
    
    return True
