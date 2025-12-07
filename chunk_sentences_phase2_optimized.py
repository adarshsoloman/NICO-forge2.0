"""
Bilingual Dataset Sentence Chunker - Phase 2 OPTIMIZED
=======================================================
Uses LLM to align and chunk entries with mismatched sentence counts.

OPTIMIZATIONS:
- Parallel LLM API calls (configurable workers)
- Checkpoint system for resumability
- Stream processing (low memory usage)
- Progress tracking with tqdm
- Automatic retry with exponential backoff
- Rate limiting to respect API limits

Usage:
    # Basic usage
    python chunk_sentences_phase2_optimized.py
    
    # Custom configuration
    python chunk_sentences_phase2_optimized.py --max-workers 20 --checkpoint-interval 100
    
    # Resume from checkpoint
    python chunk_sentences_phase2_optimized.py --resume
    
    # Clear checkpoint and start fresh
    python chunk_sentences_phase2_optimized.py --clear-checkpoint
"""

import json
import time
import argparse
from openai import OpenAI
from tqdm import tqdm
import config
from utils.checkpoint_manager import CheckpointManager
from utils.parallel_llm import ParallelLLMProcessor


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


def align_with_llm(entry: dict, entry_num: int) -> dict:
    """
    Use LLM to align mismatched English-Hindi pairs.
    
    Args:
        entry: Entry dict with 'english', 'hindi', 'eng_sentences', 'hin_sentences'
        entry_num: Entry number for tracking
    
    Returns:
        Dict with 'chunks' (list of aligned pairs) and 'success' (bool)
    """
    user_prompt = f"""Align these English-Hindi texts into 3-sentence chunks:

ENGLISH ({entry['eng_sentences']} sentences):
{entry['english']}

HINDI ({entry['hin_sentences']} sentences):
{entry['hindi']}

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
        return {
            'chunks': [],
            'success': False,
            'error': str(e)
        }


def process_phase2_optimized(
    input_file: str = 'pib_mismatched_for_llm.jsonl',
    output_file: str = 'pib_chunked_llm_aligned.jsonl',
    checkpoint_file: str = 'checkpoints/phase2_checkpoint.json',
    max_workers: int = 10,
    checkpoint_interval: int = 50,
    max_requests_per_second: float = 10.0,
    resume: bool = False,
    clear_checkpoint: bool = False
):
    """
    Phase 2: Use LLM to align and chunk mismatched entries (OPTIMIZED).
    
    Args:
        input_file: Input JSONL file with mismatched entries
        output_file: Output JSONL file for aligned chunks
        checkpoint_file: Checkpoint file path
        max_workers: Number of parallel workers
        checkpoint_interval: Save checkpoint every N entries
        max_requests_per_second: Rate limit for API calls
        resume: Resume from checkpoint
        clear_checkpoint: Clear checkpoint and start fresh
    """
    print("=" * 70)
    print("Bilingual Dataset Sentence Chunker - Phase 2 OPTIMIZED")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model:                  {config.LLM_MODEL}")
    print(f"  Max Workers:            {max_workers}")
    print(f"  Rate Limit:             {max_requests_per_second} req/s")
    print(f"  Checkpoint Interval:    {checkpoint_interval} entries")
    print(f"  Input:                  {input_file}")
    print(f"  Output:                 {output_file}")
    print(f"  Checkpoint:             {checkpoint_file}")
    
    # Initialize checkpoint manager
    checkpoint = CheckpointManager(checkpoint_file)
    
    if clear_checkpoint:
        checkpoint.clear()
    
    # Load all entries (need to know total count)
    print(f"\nLoading entries from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_entries = [json.loads(line) for line in f]
    
    total_entries = len(all_entries)
    print(f"Loaded {total_entries} mismatched entries")
    
    # Filter out already processed entries if resuming
    if resume or len(checkpoint.processed_ids) > 0:
        entries_to_process = [
            e for e in all_entries 
            if not checkpoint.is_processed(e.get('entry_num', 0))
        ]
        print(f"Resuming: {len(checkpoint.processed_ids)} already processed, {len(entries_to_process)} remaining")
    else:
        entries_to_process = all_entries
    
    if not entries_to_process:
        print("\n✓ All entries already processed!")
        return
    
    # Initialize parallel processor
    print(f"\nStarting parallel processing with {max_workers} workers...")
    processor = ParallelLLMProcessor(
        max_workers=max_workers,
        max_requests_per_second=max_requests_per_second,
        max_retries=3
    )
    
    # Open output file in append mode
    output_mode = 'a' if resume else 'w'
    outfile = open(output_file, output_mode, encoding='utf-8')
    
    # Progress bar
    pbar = tqdm(total=len(entries_to_process), desc="Processing", unit="entry")
    
    # Progress callback
    def on_progress(result):
        # Update progress bar
        status = "✓" if result.success else "✗"
        pbar.set_postfix({
            'status': status,
            'chunks': result.chunks_created,
            'success_rate': f"{checkpoint.stats['successful']}/{checkpoint.stats['total_processed']}"
        })
        pbar.update(1)
        
        # Write chunks to output (filter out invalid chunks)
        if result.success:
            for chunk in result.data:
                # Skip chunks with empty English or Hindi
                if not chunk.get('english', '').strip() or not chunk.get('hindi', '').strip():
                    continue
                    
                output_entry = {
                    'english': chunk['english'],
                    'hindi': chunk['hindi']
                }
                outfile.write(json.dumps(output_entry, ensure_ascii=False) + '\n')
        
        # Update checkpoint
        checkpoint.mark_processed(
            result.entry_id,
            result.success,
            result.chunks_created
        )
        
        # Save checkpoint periodically
        if checkpoint.stats['total_processed'] % checkpoint_interval == 0:
            checkpoint.save()
            outfile.flush()  # Ensure data is written to disk
    
    try:
        # Process in parallel
        start_time = time.time()
        results = processor.process_batch(
            entries_to_process,
            align_with_llm,
            progress_callback=on_progress
        )
        
        # Final checkpoint save
        checkpoint.save()
        
        elapsed_time = time.time() - start_time
        
        pbar.close()
        outfile.close()
        
        # Summary
        stats = checkpoint.get_stats()
        print("\n" + "=" * 70)
        print("PHASE 2 COMPLETE")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  Total processed:            {stats['total_processed']}")
        print(f"  Successfully aligned:       {stats['successful']}")
        print(f"  Failed:                     {stats['failed']}")
        print(f"  Total chunks created:       {stats['chunks_created']}")
        print(f"  Processing time:            {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"  Processing rate:            {stats['total_processed']/elapsed_time:.2f} entries/second")
        print(f"\nOutput file:")
        print(f"  ✓ {output_file} ({stats['chunks_created']} chunks)")
        print(f"\nCheckpoint saved to: {checkpoint_file}")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted! Saving checkpoint...")
        checkpoint.save()
        outfile.close()
        pbar.close()
        print(f"✓ Checkpoint saved. Resume with --resume flag")
    
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        checkpoint.save()
        outfile.close()
        pbar.close()
        raise


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Phase 2 LLM Chunking (Optimized)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python chunk_sentences_phase2_optimized.py
  
  # Use 20 parallel workers
  python chunk_sentences_phase2_optimized.py --max-workers 20
  
  # Resume from checkpoint
  python chunk_sentences_phase2_optimized.py --resume
  
  # Clear checkpoint and start fresh
  python chunk_sentences_phase2_optimized.py --clear-checkpoint
        """
    )
    
    parser.add_argument('--input', default='pib_mismatched_for_llm.jsonl',
                        help='Input JSONL file (default: pib_mismatched_for_llm.jsonl)')
    parser.add_argument('--output', default='pib_chunked_llm_aligned.jsonl',
                        help='Output JSONL file (default: pib_chunked_llm_aligned.jsonl)')
    parser.add_argument('--checkpoint', default='checkpoints/phase2_checkpoint.json',
                        help='Checkpoint file (default: checkpoints/phase2_checkpoint.json)')
    parser.add_argument('--max-workers', type=int, default=10,
                        help='Number of parallel workers (default: 10)')
    parser.add_argument('--checkpoint-interval', type=int, default=50,
                        help='Save checkpoint every N entries (default: 50)')
    parser.add_argument('--rate-limit', type=float, default=10.0,
                        help='Max requests per second (default: 10.0)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint')
    parser.add_argument('--clear-checkpoint', action='store_true',
                        help='Clear checkpoint and start fresh')
    
    args = parser.parse_args()
    
    process_phase2_optimized(
        input_file=args.input,
        output_file=args.output,
        checkpoint_file=args.checkpoint,
        max_workers=args.max_workers,
        checkpoint_interval=args.checkpoint_interval,
        max_requests_per_second=args.rate_limit,
        resume=args.resume,
        clear_checkpoint=args.clear_checkpoint
    )


if __name__ == '__main__':
    main()
