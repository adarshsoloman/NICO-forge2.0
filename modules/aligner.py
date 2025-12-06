"""
Chunk Alignment Module

Aligns English and Hindi chunks by index position.
"""


def align_chunks(eng_chunks: list[str], hin_chunks: list[str]) -> list[tuple[str, str]]:
    """
    Align English and Hindi chunks by index.
    
    If one list is shorter, pads with empty strings to match length.
    
    Args:
        eng_chunks: List of English chunk strings
        hin_chunks: List of Hindi chunk strings
    
    Returns:
        List of (eng_chunk, hin_chunk) tuples aligned by index
    """
    # Determine maximum length
    max_len = max(len(eng_chunks), len(hin_chunks))
    
    # Pad shorter list with empty strings
    eng_chunks_padded = eng_chunks + [''] * (max_len - len(eng_chunks))
    hin_chunks_padded = hin_chunks + [''] * (max_len - len(hin_chunks))
    
    # Zip into aligned pairs
    aligned_pairs = list(zip(eng_chunks_padded, hin_chunks_padded))
    
    return aligned_pairs
