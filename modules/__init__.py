"""
Rewat-Forge Modules Package

Contains all modular components for the bilingual PDF-to-CSV pipeline.
"""

from .extractor import extract_page_text, get_page_count
from .splitter import split_sentences
from .chunker import create_chunks
from .aligner import align_chunks
from .llm_verifier import llm_map
from .llm_alignment import align_with_llm, batch_align_pages, ALIGNMENT_SYSTEM_PROMPT
from .regex_engine import extract_patterns
from .csv_writer import (
    append_row, 
    initialize_csv, 
    create_row,
    append_json_line,
    initialize_json_array,
    append_json_array_item,
    finalize_json_array
)
from .text_cleaner import clean_chunk, is_chunk_valid
from .quality_filter import (
    is_valid_chunk_pair,
    calculate_quality_score,
    get_quality_label
)

__all__ = [
    'extract_page_text',
    'get_page_count',
    'split_sentences',
    'create_chunks',
    'align_chunks',
    'llm_map',
    'align_with_llm',
    'batch_align_pages',
    'ALIGNMENT_SYSTEM_PROMPT',
    'extract_patterns',
    'append_row',
    'initialize_csv',
    'create_row',
    'append_json_line',
    'initialize_json_array',
    'append_json_array_item',
    'finalize_json_array',
    'clean_chunk',
    'is_chunk_valid',
    'is_valid_chunk_pair',
    'calculate_quality_score',
    'get_quality_label',
]
