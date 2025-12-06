"""
Rewat-Forge Pipeline Configuration

Central configuration file for all pipeline settings.
Modify these values to customize pipeline behavior.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================

# Number of sentences to group into each chunk (1-3 recommended)
CHUNK_SIZE = 3

# Number of parallel worker threads for page processing
# Recommended: Start with 4, then tune based on your CPU
WORKER_THREADS = 4


# ============================================================================
# LLM VERIFICATION CONFIGURATION
# ============================================================================

# Enable or disable LLM verification of Hindi translations
# Set to False for faster processing without LLM calls
USE_LLM_VERIFICATION = True

# Enable LLM-based semantic alignment (alternative to index-based alignment)
# When True: Uses Rewat's LLM alignment prompt to semantically match EN-HI pairs
# When False: Uses traditional index-based alignment (faster but less accurate)
USE_LLM_ALIGNMENT = False

# LLM API Configuration (OpenAI-compatible)
# Examples:
#   - OpenRouter: "https://openrouter.ai/api/v1"
#   - OpenAI: "https://api.openai.com/v1"
#   - Bytez: "https://api.bytez.com"
#   - Local: "http://localhost:1234/v1"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")  # Load from .env

# Your API key for the LLM provider (loaded from .env file for security)
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")  # IMPORTANT: Set in .env file

# Model identifier
# Examples:
#   - Bytez: "gpt-4o-mini", "claude-3-5-sonnet-20241022", "llama-3.1-70b-versatile"
#   - Bytez Translation: "google/madlad400-7b-mt" (specialized for multilingual translation)
#   - OpenRouter: "meta-llama/llama-3.1-8b-instruct:free"
#   - OpenAI: "gpt-4o-mini"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Load from .env

# Temperature for LLM responses (0.0 = deterministic, 1.0 = creative)
# Lower values recommended for translation verification
LLM_TEMPERATURE = 0.3

# Maximum retries for LLM API calls (handles rate limits)
LLM_MAX_RETRIES = 3

# Delay between retries in seconds
LLM_RETRY_DELAY = 2


# ============================================================================
# REGEX EXTRACTION PATTERNS
# ============================================================================

# List of regex patterns to extract from Hindi text
# Matches will be saved as JSON arrays in the CSV
REGEX_PATTERNS = [
    r'\b\d{4}\b',              # Years (e.g., 2024, 1947)
    r'Chapter \d+',            # English chapter references
    r'अध्याय \d+',             # Hindi chapter references (adhyaya)
    r'\bPage \d+\b',           # Page references
    r'\bपृष्ठ \d+\b',          # Hindi page references (prishth)
    r'Exercise \d+',           # Exercise numbers
    # Add your custom patterns below:
]


# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

# Path to output CSV file
OUTPUT_CSV = "final_output.csv"

# Path to output JSON file
OUTPUT_JSON = "final_output.json"

# Enable JSON output (in addition to CSV)
OUTPUT_JSON_ENABLED = True

# JSON format: "lines" (one JSON object per line) or "array" (single JSON array)
# "lines" is better for large files, "array" is more standard
JSON_FORMAT = "lines"  # Options: "lines" or "array"

# Enable error logging to file
LOG_ERRORS = True

# Error log file path
ERROR_LOG = "errors.log"


# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Apply regex patterns to verified Hindi (True) or raw Hindi (False)
REGEX_ON_VERIFIED = True  # Only if USE_LLM_VERIFICATION is True

# Sentence splitting patterns
ENGLISH_SENTENCE_DELIMITERS = r'[.!?]+'
HINDI_SENTENCE_DELIMITERS = r'[.!?।]+'  # Includes Devanagari danda (।)

# CSV encoding
CSV_ENCODING = 'utf-8-sig'  # utf-8-sig adds BOM for Excel compatibility
