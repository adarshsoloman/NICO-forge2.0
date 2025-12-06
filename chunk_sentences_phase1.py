"""
Bilingual Dataset Sentence Chunker - Phase 1
=============================================
Splits long English-Hindi pairs into 3-sentence chunks.
Handles entries where sentence counts match.

Usage:
    python3 chunk_sentences_phase1.py
"""

import json
import re

def split_english_sentences(text):
    """
    Split English text into sentences.
    Handles abbreviations like Dr., Mr., U.S., etc.
    """
    # Replace common abbreviations temporarily
    text = text.replace('Dr.', 'Dr<DOT>')
    text = text.replace('Mr.', 'Mr<DOT>')
    text = text.replace('Mrs.', 'Mrs<DOT>')
    text = text.replace('Ms.', 'Ms<DOT>')
    text = text.replace('U.S.', 'U<DOT>S<DOT>')
    text = text.replace('U.K.', 'U<DOT>K<DOT>')
    text = text.replace('etc.', 'etc<DOT>')
    text = text.replace('Ltd.', 'Ltd<DOT>')
    text = text.replace('Inc.', 'Inc<DOT>')
    text = text.replace('Co.', 'Co<DOT>')
    
    # Split on sentence endings: . ! ? followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Restore abbreviations
    sentences = [s.replace('<DOT>', '.') for s in sentences]
    
    # Clean and filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def split_hindi_sentences(text):
    """
    Split Hindi text into sentences.
    Uses । (purna viram) and also . ! ?
    """
    # Split on Hindi purna viram or English punctuation
    sentences = re.split(r'[।.!?]\s+', text)
    
    # Clean and filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_into_groups(sentences, chunk_size=3):
    """
    Chunk sentences into groups of chunk_size.
    """
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i+chunk_size]
        chunks.append(chunk)
    return chunks


def process_phase1():
    """
    Phase 1: Process entries with matching sentence counts.
    """
    print("=" * 70)
    print("Bilingual Dataset Sentence Chunker - Phase 1")
    print("=" * 70)
    print("\nProcessing entries with matching sentence counts...\n")
    
    # Load data
    with open('pib_bilingual_ultra_clean.jsonl', 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f]
    
    matched_chunks = []
    mismatched_entries = []
    
    stats = {
        'total_entries': len(entries),
        'matched': 0,
        'mismatched': 0,
        'total_chunks_created': 0
    }
    
    for i, entry in enumerate(entries, 1):
        eng_text = entry['english']
        hin_text = entry['hindi']
        
        # Split into sentences
        eng_sentences = split_english_sentences(eng_text)
        hin_sentences = split_hindi_sentences(hin_text)
        
        eng_count = len(eng_sentences)
        hin_count = len(hin_sentences)
        
        print(f"Entry {i}: EN={eng_count} sentences, HI={hin_count} sentences", end=" ")
        
        if eng_count == hin_count:
            print("✓ MATCH")
            stats['matched'] += 1
            
            # Chunk into 3-sentence groups
            eng_chunks = chunk_into_groups(eng_sentences, 3)
            hin_chunks = chunk_into_groups(hin_sentences, 3)
            
            # Create paired chunks
            for eng_chunk, hin_chunk in zip(eng_chunks, hin_chunks):
                matched_chunks.append({
                    'english': ' '.join(eng_chunk),
                    'hindi': ' '.join(hin_chunk),
                    'source_entry': i,
                    'sentence_count': len(eng_chunk)
                })
                stats['total_chunks_created'] += 1
        else:
            print("⚠ MISMATCH - flagged for LLM alignment")
            stats['mismatched'] += 1
            mismatched_entries.append({
                'entry_num': i,
                'english': eng_text,
                'hindi': hin_text,
                'eng_sentences': eng_count,
                'hin_sentences': hin_count
            })
    
    # Save matched chunks
    with open('pib_chunked_matched.jsonl', 'w', encoding='utf-8') as f:
        for chunk in matched_chunks:
            # Save only english and hindi for final dataset
            output = {
                'english': chunk['english'],
                'hindi': chunk['hindi']
            }
            f.write(json.dumps(output, ensure_ascii=False) + '\n')
    
    # Save mismatched entries for Phase 2
    with open('pib_mismatched_for_llm.jsonl', 'w', encoding='utf-8') as f:
        for entry in mismatched_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  Total entries processed:    {stats['total_entries']}")
    print(f"  Matched (chunked):          {stats['matched']}")
    print(f"  Mismatched (need LLM):      {stats['mismatched']}")
    print(f"  Total chunks created:       {stats['total_chunks_created']}")
    print(f"\nOutput files:")
    print(f"  ✓ pib_chunked_matched.jsonl ({stats['total_chunks_created']} chunks)")
    print(f"  ⚠ pib_mismatched_for_llm.jsonl ({stats['mismatched']} entries)")
    print("\n" + "=" * 70)
    print("")


if __name__ == '__main__':
    process_phase1()
