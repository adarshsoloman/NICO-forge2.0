"""
LLM Deep Cleaning - OPTIMIZED
==============================
AI-powered deep cleaning and verification of bilingual datasets.

OPTIMIZATIONS:
- Parallel LLM API calls (configurable workers)
- Checkpoint system for resumability
- Stream processing (low memory usage)
- Progress tracking with tqdm
- Automatic retry with exponential backoff
- Rate limiting to respect API limits

Usage:
    # Basic usage
    python llm_deep_clean_phase2_optimized.py
    
    # Custom configuration
    python llm_deep_clean_phase2_optimized.py --max-workers 15 --input mydata.jsonl
    
    # Resume from checkpoint
    python llm_deep_clean_phase2_optimized.py --resume
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

SYSTEM_PROMPT = """You are a bilingual data quality expert specializing in English-Hindi translation pairs.

Your task is to clean and verify translation pairs. Follow these rules:

1. CLEANING:
   - Remove special characters like backslashes (\\), forward slashes (/) that don't belong
   - Remove escape sequences or formatting artifacts
   - Preserve meaningful punctuation and numbers

2. VERIFICATION:
   - Check if English and Hindi are actual translations
   - Ensure semantic alignment
   - Do NOT retranslate or paraphrase

3. OUTPUT: Return ONLY a JSON object:
   {"english": "cleaned text", "hindi": "cleaned text", "is_aligned": true/false, "issues_found": "description"}
"""


def llm_clean_pair(entry: dict, entry_num: int) -> dict:
    """
    Send pair to LLM for cleaning.
    
    Args:
        entry: Dict with 'english' and 'hindi' keys
        entry_num: Entry number for tracking
    
    Returns:
        Dict with 'chunks' (cleaned pair), 'success', and 'error'
    """
    user_prompt = f"""Clean this English-Hindi translation pair:

ENGLISH: {entry['english']}

HINDI: {entry['hindi']}

Return cleaned version as JSON."""
    
    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        llm_output = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if llm_output.startswith('```'):
            llm_output = llm_output.split('```')[1]
            if llm_output.startswith('json'):
                llm_output = llm_output[4:]
            llm_output = llm_output.strip()
        
        result = json.loads(llm_output)
        
        # Return as single-item list for consistency with chunking
        cleaned_entry = {
            'english': result.get('english', entry['english']),
            'hindi': result.get('hindi', entry['hindi'])
        }
        
        return {
            'chunks': [cleaned_entry],
            'success': True,
            'error': None
        }
        
    except Exception as e:
        # On error, return original
        return {
            'chunks': [{'english': entry['english'], 'hindi': entry['hindi']}],
            'success': False,
            'error': str(e)
        }


def process_llm_cleaning_optimized(
    input_file: str = 'pib_bilingual_cleaned.jsonl',
    output_file: str = 'pib_bilingual_final.jsonl',
    checkpoint_file: str = 'checkpoints/llm_clean_checkpoint.json',
    max_workers: int = 10,
    checkpoint_interval: int = 100,
    max_requests_per_second: float = 10.0,
    resume: bool = False,
    clear_checkpoint: bool = False
):
    """
    LLM-powered deep cleaning (OPTIMIZED).
    
    Args:
        input_file: Input JSONL file
        output_file: Output JSONL file
        checkpoint_file: Checkpoint file path
        max_workers: Number of parallel workers
        checkpoint_interval: Save checkpoint every N entries
        max_requests_per_second: Rate limit for API calls
        resume: Resume from checkpoint
        clear_checkpoint: Clear checkpoint and start fresh
    """
    print("=" * 70)
    print("LLM Deep Cleaning - OPTIMIZED")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model:                  {config.LLM_MODEL}")
    print(f"  Max Workers:            {max_workers}")
    print(f"  Rate Limit:             {max_requests_per_second} req/s")
    print(f"  Checkpoint Interval:    {checkpoint_interval} entries")
    print(f"  Input:                  {input_file}")
    print(f"  Output:                 {output_file}")
    
    # Initialize checkpoint manager
    checkpoint = CheckpointManager(checkpoint_file)
    
    if clear_checkpoint:
        checkpoint.clear()
    
    # Load all entries
    print(f"\nLoading entries from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_entries = []
        for i, line in enumerate(f, 1):
            entry = json.loads(line)
            entry['entry_num'] = i  # Add entry number
            all_entries.append(entry)
    
    total_entries = len(all_entries)
    print(f"Loaded {total_entries} entries")
    
    # Filter out already processed entries
    if resume or len(checkpoint.processed_ids) > 0:
        entries_to_process = [
            e for e in all_entries 
            if not checkpoint.is_processed(e['entry_num'])
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
    pbar = tqdm(total=len(entries_to_process), desc="Cleaning", unit="entry")
    
    # Progress callback
    def on_progress(result):
        status = "✓" if result.success else "⚠"
        pbar.set_postfix({
            'status': status,
            'success_rate': f"{checkpoint.stats['successful']}/{checkpoint.stats['total_processed']}"
        })
        pbar.update(1)
        
        # Write cleaned entry to output
        if result.data:
            for cleaned in result.data:
                outfile.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
        
        # Update checkpoint
        checkpoint.mark_processed(
            result.entry_id,
            result.success,
            len(result.data)
        )
        
        # Save checkpoint periodically
        if checkpoint.stats['total_processed'] % checkpoint_interval == 0:
            checkpoint.save()
            outfile.flush()
    
    try:
        # Process in parallel
        start_time = time.time()
        results = processor.process_batch(
            entries_to_process,
            llm_clean_pair,
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
        print("LLM DEEP CLEANING COMPLETE")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  Total processed:            {stats['total_processed']}")
        print(f"  Successfully cleaned:       {stats['successful']}")
        print(f"  Errors:                     {stats['failed']}")
        print(f"  Processing time:            {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"  Processing rate:            {stats['total_processed']/elapsed_time:.2f} entries/second")
        print(f"\nOutput file:")
        print(f"  ✓ {output_file}")
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
    parser = argparse.ArgumentParser(description='LLM Deep Cleaning (Optimized)')
    
    parser.add_argument('--input', default='pib_bilingual_cleaned.jsonl',
                        help='Input JSONL file')
    parser.add_argument('--output', default='pib_bilingual_final.jsonl',
                        help='Output JSONL file')
    parser.add_argument('--checkpoint', default='checkpoints/llm_clean_checkpoint.json',
                        help='Checkpoint file')
    parser.add_argument('--max-workers', type=int, default=10,
                        help='Number of parallel workers (default: 10)')
    parser.add_argument('--checkpoint-interval', type=int, default=100,
                        help='Save checkpoint every N entries (default: 100)')
    parser.add_argument('--rate-limit', type=float, default=10.0,
                        help='Max requests per second (default: 10.0)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint')
    parser.add_argument('--clear-checkpoint', action='store_true',
                        help='Clear checkpoint and start fresh')
    
    args = parser.parse_args()
    
    process_llm_cleaning_optimized(
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
