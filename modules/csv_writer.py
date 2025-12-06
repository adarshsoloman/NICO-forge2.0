"""
CSV Writer Module

Thread-safe CSV writing with proper locking mechanism.
Enhanced with metadata columns for better data organization.
"""

import csv
import os
import threading
import json
import re
from datetime import datetime, timezone
import config


# Enhanced CSV column headers with metadata and quality scoring
CSV_HEADERS = [
    'doc_id',
    'page',
    'chunk_id',
    'chapter_num',           # NEW: Extracted chapter number
    'eng_chunk',
    'hin_chunk_raw',
    'hin_chunk_verified',
    'translation_changed',   # NEW: Did LLM modify the translation?
    'char_count_eng',        # NEW: Length of English text
    'char_count_hin',        # NEW: Length of Hindi text
    'quality_score',         # NEW: Quality score (0.0-1.0)
    'quality_label',         # NEW: EXCELLENT, GOOD, FAIR, POOR
    'alignment_method',
    'regex_matches',
    'llm_flags',
    'timestamp'
]


def initialize_csv(csv_path: str, lock: threading.Lock):
    """
    Initialize CSV file with headers if it doesn't exist.
    
    Args:
        csv_path: Path to CSV file
        lock: Threading lock for safe file access
    """
    with lock:
        # Only create if file doesn't exist
        if not os.path.exists(csv_path):
            with open(csv_path, 'w', newline='', encoding=config.CSV_ENCODING) as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()


def append_row(row_data: dict, csv_path: str, lock: threading.Lock):
    """
    Append a row to the CSV file in a thread-safe manner.
    
    Args:
        row_data: Dictionary containing row data with keys matching CSV_HEADERS
        csv_path: Path to CSV file
        lock: Threading lock for safe file access
    """
    with lock:
        # Check if file exists, create with headers if not
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding=config.CSV_ENCODING) as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Add timestamp if not present
            if 'timestamp' not in row_data:
                row_data['timestamp'] = get_utc_timestamp()
            
            # Write the row
            writer.writerow(row_data)


def append_json_line(row_data: dict, json_path: str, lock: threading.Lock):
    """
    Append a row to JSON Lines file in a thread-safe manner.
    
    JSON Lines format: one JSON object per line (newline-delimited JSON).
    This format is efficient for large files and streaming.
    
    Args:
        row_data: Dictionary containing row data
        json_path: Path to JSON Lines file
        lock: Threading lock for safe file access
    """
    with lock:
        # Add timestamp if not present
        if 'timestamp' not in row_data:
            row_data['timestamp'] = get_utc_timestamp()
        
        # Append as single line JSON
        with open(json_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row_data, ensure_ascii=False) + '\n')


def initialize_json_array(json_path: str, lock: threading.Lock):
    """
    Initialize JSON array file with opening bracket.
    
    Args:
        json_path: Path to JSON file
        lock: Threading lock for safe file access
    """
    with lock:
        if not os.path.exists(json_path):
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write('[\n')


def append_json_array_item(row_data: dict, json_path: str, lock: threading.Lock, is_first: bool = False):
    """
    Append item to JSON array file.
    
    Note: This approach requires finalization. For large datasets, use JSON Lines instead.
    
    Args:
        row_data: Dictionary containing row data
        json_path: Path to JSON file
        lock: Threading lock for safe file access
        is_first: Whether this is the first item (no leading comma)
    """
    with lock:
        # Add timestamp if not present
        if 'timestamp' not in row_data:
            row_data['timestamp'] = get_utc_timestamp()
        
        with open(json_path, 'a', encoding='utf-8') as f:
            if not is_first:
                f.write(',\n')
            f.write('  ' + json.dumps(row_data, ensure_ascii=False, indent=2).replace('\n', '\n  '))


def finalize_json_array(json_path: str, lock: threading.Lock):
    """
    Close JSON array file with closing bracket.
    
    Args:
        json_path: Path to JSON file
        lock: Threading lock for safe file access
    """
    with lock:
        if os.path.exists(json_path):
            with open(json_path, 'a', encoding='utf-8') as f:
                f.write('\n]\n')


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.
    
    Returns:
        ISO-8601 formatted timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def extract_chapter_number(regex_matches_json: str) -> str:
    """
    Extract chapter number from regex matches.
    
    Looks for patterns like "Chapter 3" or "अध्याय 5" and extracts the number.
    
    Args:
        regex_matches_json: JSON string containing regex matches
    
    Returns:
        Chapter number as string, or empty string if not found
    """
    try:
        matches = json.loads(regex_matches_json)
        
        # Look for chapter patterns
        for match in matches:
            # English: "Chapter 3"
            eng_match = re.search(r'Chapter\s+(\d+)', match, re.IGNORECASE)
            if eng_match:
                return eng_match.group(1)
            
            # Hindi: "अध्याय 3"
            hin_match = re.search(r'अध्याय\s+(\d+)', match)
            if hin_match:
                return hin_match.group(1)
        
        return ""  # No chapter found
    
    except (json.JSONDecodeError, TypeError):
        return ""


def create_row(
    doc_id: str,
    page: int,
    chunk_id: int,
    eng_chunk: str,
    hin_chunk_raw: str,
    hin_chunk_verified: str,
    alignment_method: str,
    regex_matches: str,
    llm_flags: str,
    quality_score: float = 0.0,
    quality_label: str = ""
) -> dict:
    """
    Create a row dictionary with all required fields.
    
    Enhanced with automatic metadata extraction:
    - Chapter number from regex matches
    - Translation change detection
    - Character counts for both languages
    - Quality scoring
    
    Args:
        doc_id: Document identifier (PDF filename without extension)
        page: Page number (1-indexed for user display)
        chunk_id: Chunk index within page (0-indexed)
        eng_chunk: English text chunk
        hin_chunk_raw: Raw extracted Hindi chunk
        hin_chunk_verified: LLM-verified Hindi chunk
        alignment_method: Alignment method used (always "index")
        regex_matches: JSON string of regex matches
        llm_flags: Optional LLM flags
        quality_score: Quality score (0.0-1.0)
        quality_label: Quality label (EXCELLENT, GOOD, FAIR, POOR)
    
    Returns:
        Dictionary ready for CSV writing with enhanced metadata
    """
    # Extract chapter number from regex matches
    chapter_num = extract_chapter_number(regex_matches)
    
    # Check if translation was changed by LLM
    translation_changed = (hin_chunk_raw != hin_chunk_verified) and bool(hin_chunk_verified)
    
    # Calculate character counts
    char_count_eng = len(eng_chunk) if eng_chunk else 0
    char_count_hin = len(hin_chunk_verified) if hin_chunk_verified else len(hin_chunk_raw)
    
    return {
        'doc_id': doc_id,
        'page': page,
        'chunk_id': chunk_id,
        'chapter_num': chapter_num,
        'eng_chunk': eng_chunk,
        'hin_chunk_raw': hin_chunk_raw,
        'hin_chunk_verified': hin_chunk_verified,
        'translation_changed': translation_changed,
        'char_count_eng': char_count_eng,
        'char_count_hin': char_count_hin,
        'quality_score': quality_score,
        'quality_label': quality_label,
        'alignment_method': alignment_method,
        'regex_matches': regex_matches,
        'llm_flags': llm_flags,
        'timestamp': get_utc_timestamp()
    }
