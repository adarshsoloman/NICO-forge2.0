"""
LLM Alignment Module for Rewat-Forge

This module uses LLM-based semantic alignment to map English and Hindi corpus chunks.
Unlike the index-based aligner, this approach uses an LLM to intelligently match
English segments with their precise Hindi translations from the raw corpus.
"""

import json
from typing import List, Tuple, Optional
from openai import OpenAI


# System prompt for bilingual corpus alignment
ALIGNMENT_SYSTEM_PROMPT = """You are an alignment assistant for bilingual corpus mapping. Your job is to take raw English text and its corresponding raw Hindi text, and produce a clean CSV dataset of aligned translation pairs.

Rules you must follow:

1. Input will always come as
<english> ... </english> and <hindi> ... </hindi>.


2. You must semantically map English chunks to their precise Hindi translations using only the raw corpus.
No paraphrasing, no rewriting, no synthetic text.
Every line you output must be exactly present in the input corpus.


3. Chunking:
Break the English corpus into segments of 1 to 3 sentences. Never exceed 3 sentences.
For each chunk, find the exact corresponding Hindi translation from the Hindi corpus.


4. Output format:
You must respond with only the CSV mappings, wrapped inside a <csv></csv> block.
Format inside the CSV must be:
"English","Hindi"
Both sides must be verbatim text from the corpus.


5. No commentary, no explanations, no extra lines outside <csv></csv>.
Only produce rows for clean, confirmed mappings.


6. Quality control:
Do not guess missing translations.
Do not merge unrelated lines.
Do not fix grammar or modify spacing.
Use only exact text present in the input.



Your task is to produce a final CSV dataset of aligned bilingual pairs that are purely extracted from the provided English and Hindi corpora."""


def align_with_llm(
    english_text: str,
    hindi_text: str,
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1
) -> List[Tuple[str, str]]:
    """
    Use LLM to semantically align English and Hindi text chunks.
    
    Args:
        english_text: Raw English text from a page
        hindi_text: Raw Hindi text from the same page
        llm_client: OpenAI client instance
        model: LLM model identifier
        temperature: Temperature for LLM (lower = more deterministic)
    
    Returns:
        List of (english_chunk, hindi_chunk) tuples
    
    Raises:
        Exception: If LLM call fails or response is malformed
    """
    # Construct the user message with the corpus
    user_message = f"""<english>
{english_text}
</english>

<hindi>
{hindi_text}
</hindi>"""
    
    try:
        # Call the LLM API
        response = llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ALIGNMENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=4096
        )
        
        # Extract the response content
        content = response.choices[0].message.content.strip()
        
        # Parse the CSV from the <csv></csv> block
        aligned_pairs = _parse_csv_response(content)
        
        return aligned_pairs
        
    except Exception as e:
        raise Exception(f"LLM alignment failed: {str(e)}")


def _parse_csv_response(response: str) -> List[Tuple[str, str]]:
    """
    Parse the LLM's CSV response from <csv></csv> block.
    
    Args:
        response: Raw LLM response containing <csv></csv> block
    
    Returns:
        List of (english, hindi) tuples
    
    Raises:
        ValueError: If CSV block not found or malformed
    """
    import csv
    from io import StringIO
    
    # Extract content between <csv> and </csv>
    if "<csv>" not in response or "</csv>" not in response:
        raise ValueError("Response does not contain <csv></csv> block")
    
    start_idx = response.find("<csv>") + 5
    end_idx = response.find("</csv>")
    csv_content = response[start_idx:end_idx].strip()
    
    # Parse CSV content
    pairs = []
    csv_reader = csv.reader(StringIO(csv_content))
    
    # Skip header row if present
    first_row = next(csv_reader, None)
    if first_row and first_row[0].lower() != "english":
        # First row is data, not header
        if len(first_row) >= 2:
            pairs.append((first_row[0], first_row[1]))
    
    # Read remaining rows
    for row in csv_reader:
        if len(row) >= 2:
            eng_chunk = row[0].strip()
            hin_chunk = row[1].strip()
            
            # Only add non-empty pairs
            if eng_chunk and hin_chunk:
                pairs.append((eng_chunk, hin_chunk))
    
    return pairs


def batch_align_pages(
    page_pairs: List[Tuple[str, str]],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1
) -> List[List[Tuple[str, str]]]:
    """
    Align multiple page pairs in batch.
    
    Args:
        page_pairs: List of (english_text, hindi_text) for each page
        llm_client: OpenAI client instance
        model: LLM model identifier
        temperature: Temperature for LLM
    
    Returns:
        List of alignment results, one per page
        Each result is a list of (english_chunk, hindi_chunk) tuples
    """
    results = []
    
    for eng_text, hin_text in page_pairs:
        try:
            aligned_pairs = align_with_llm(
                eng_text, 
                hin_text, 
                llm_client, 
                model, 
                temperature
            )
            results.append(aligned_pairs)
        except Exception as e:
            # Log error and return empty alignment for this page
            print(f"⚠️  Alignment failed for page: {str(e)}")
            results.append([])
    
    return results
