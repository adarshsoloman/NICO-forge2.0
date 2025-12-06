"""
Sentence Chunking Module

Groups sentences into configurable chunks (1-3 sentences).
"""

import config


def create_chunks(sentences: list[str], chunk_size: int = None) -> list[str]:
    """
    Group sentences into chunks of specified size.
    
    Args:
        sentences: List of sentence strings
        chunk_size: Number of sentences per chunk (defaults to config.CHUNK_SIZE)
    
    Returns:
        List of chunk strings (sentences joined with spaces)
    """
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    
    chunks = []
    
    # Group sentences into chunks
    for i in range(0, len(sentences), chunk_size):
        chunk_sentences = sentences[i:i + chunk_size]
        chunk_text = ' '.join(chunk_sentences)
        chunks.append(chunk_text)
    
    return chunks
