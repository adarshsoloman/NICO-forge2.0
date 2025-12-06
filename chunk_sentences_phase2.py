"""
Bilingual Dataset Sentence Chunker - Phase 2 (LLM Alignment)
=============================================================
Uses LLM to align and chunk entries with mismatched sentence counts.

Usage:
    python3 chunk_sentences_phase2.py
"""

import json
import time
from openai import OpenAI
import config

# Initialize LLM
client = OpenAI(
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL
)

SYSTEM_PROMPT = """You are an expert in English-Hindi bilingual text alignment.

Your task: Given English and Hindi text with DIFFERENT sentence counts, create aligned 3-sentence chunks.

RULES:
1. Identify which English sentences correspond to which Hindi sentences
2. Create chunks of UP TO 3 English sentences paired with their corresponding Hindi translation
3. Ensure semantic alignment - English chunk must match Hindi chunk in meaning
4. If counts are very different, some sentences might be combined or split

OUTPUT FORMAT (JSON array of chunks):
[
  {
    "english": "First 1-3 English sentences",
    "hindi": "Corresponding Hindi sentences"
  },
  {
    "english": "Next 1-3 English sentences",
    "hindi": "Corresponding Hindi sentences"
  }
]

Return ONLY the JSON array, no markdown, no explanation."""


def align_with_llm(english_text, hindi_text, entry_num, eng_count, hin_count):
    """
    Use LLM to align mismatched English-Hindi pairs.
    """
    user_prompt = f"""Align these English-Hindi texts into 3-sentence chunks:

ENGLISH ({eng_count} sentences):
{english_text}

HINDI ({hin_count} sentences):
{hindi_text}

Create aligned chunks (max 3 English sentences per chunk) as JSON array."""

    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=8000
        )
        
        llm_output = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks
        if llm_output.startswith('```'):
            llm_output = llm_output.split('```')[1]
            if llm_output.startswith('json'):
                llm_output = llm_output[4:]
            llm_output = llm_output.strip()
        
        chunks = json.loads(llm_output)
        
        return {
            'chunks': chunks,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"  ✗ LLM error: {str(e)[:100]}")
        return {
            'chunks': [],
            'success': False,
            'error': str(e)
        }


def process_phase2():
    """
    Phase 2: Use LLM to align and chunk mismatched entries.
    """
    print("=" * 70)
    print("Bilingual Dataset Sentence Chunker - Phase 2 (LLM Alignment)")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model: {config.LLM_MODEL}")
    print(f"  Processing mismatched entries...\n")
    
    # Load mismatched entries
    with open('pib_mismatched_for_llm.jsonl', 'r', encoding='utf-8') as f:
        mismatched = [json.loads(line) for line in f]
    
    print(f"Loaded {len(mismatched)} mismatched entries\n")
    
    all_chunks = []
    stats = {
        'total_mismatched': len(mismatched),
        'success': 0,
        'failed': 0,
        'chunks_created': 0
    }
    
    start_time = time.time()
    
    for entry in mismatched:
        entry_num = entry['entry_num']
        eng_count = entry['eng_sentences']
        hin_count = entry['hin_sentences']
        
        print(f"Entry {entry_num}: EN={eng_count}, HI={hin_count} - Aligning with LLM...")
        
        result = align_with_llm(
            entry['english'],
            entry['hindi'],
            entry_num,
            eng_count,
            hin_count
        )
        
        if result['success']:
            stats['success'] += 1
            chunks_count = len(result['chunks'])
            stats['chunks_created'] += chunks_count
            print(f"  ✓ Created {chunks_count} aligned chunks")
            
            # Add chunks to output
            all_chunks.extend(result['chunks'])
        else:
            stats['failed'] += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save LLM-aligned chunks
    with open('pib_chunked_llm_aligned.jsonl', 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            output = {
                'english': chunk['english'],
                'hindi': chunk['hindi']
            }
            f.write(json.dumps(output, ensure_ascii=False) + '\n')
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  Mismatched entries:         {stats['total_mismatched']}")
    print(f"  Successfully aligned:       {stats['success']}")
    print(f"  Failed:                     {stats['failed']}")
    print(f"  Total chunks created:       {stats['chunks_created']}")
    print(f"  Processing time:            {elapsed_time:.1f} seconds")
    print(f"\nOutput file:")
    print(f"  ✓ pib_chunked_llm_aligned.jsonl ({stats['chunks_created']} chunks)")
    print("\n" + "=" * 70)
    print("")


if __name__ == '__main__':
    process_phase2()
