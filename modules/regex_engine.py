"""
Regex Extraction Engine

Extracts structured data using user-defined regex patterns.
"""

import re
import json
import config


def extract_patterns(text: str, patterns: list[str] = None) -> str:
    """
    Extract matches from text using regex patterns.
    
    Args:
        text: Text to search for patterns
        patterns: List of regex pattern strings (defaults to config.REGEX_PATTERNS)
    
    Returns:
        JSON-encoded array of matches as string
        Example: '["2024", "Chapter 5", "अध्याय 3"]'
    """
    if patterns is None:
        patterns = config.REGEX_PATTERNS
    
    all_matches = []
    
    # Run each pattern against the text
    for pattern in patterns:
        try:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        except re.error as e:
            # Skip invalid patterns
            continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in all_matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
    
    # Convert to JSON string
    return json.dumps(unique_matches, ensure_ascii=False)
