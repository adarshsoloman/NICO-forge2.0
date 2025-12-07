"""
OPTIMIZED BILINGUAL PIPELINE - COLAB STANDALONE
================================================
Copy this entire script into a Google Colab cell and run.
All dependencies and utilities are included.

USAGE IN COLAB:
1. Upload your JSONL file (or use files from Drive)
2. Set your OpenRouter API key below
3. Run this cell
4. Processing will show real-time progress bar

Expected speed: 5,000 rows in 30-45 minutes (vs 9+ hours)
"""

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

LLM_API_KEY = "your-openrouter-api-key-here"  # Get from https://openrouter.ai/
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # Free tier model

INPUT_FILE = "pib_mismatched_for_llm.jsonl"  # Your uploaded file
OUTPUT_FILE = "pib_chunked_llm_aligned.jsonl"  # Output file
CHECKPOINT_FILE = "phase2_checkpoint.json"  # Checkpoint for resumability

# Performance settings
MAX_WORKERS = 15  # Number of parallel workers (10-20 recommended)
RATE_LIMIT = 10.0  # Max API requests per second
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N entries

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

print("Installing dependencies...")
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "openai", "tqdm"])

# ============================================================================
# IMPORTS
# ============================================================================

import json
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from openai import OpenAI
from tqdm.auto import tqdm

# ============================================================================
# CHECKPOINT MANAGER
# ============================================================================

class CheckpointManager:
    """Manages checkpoints for resumable processing."""
    
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self.processed_ids: Set[int] = set()
        self.stats: Dict[str, Any] = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'chunks_created': 0
        }
        self._load()
    
    def _load(self):
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
                    self.stats = data.get('stats', self.stats)
                print(f"✓ Loaded checkpoint: {len(self.processed_ids)} entries already processed")
            except Exception as e:
                print(f"⚠ Warning: Could not load checkpoint: {e}")
    
    def save(self):
        try:
            data = {
                'processed_ids': list(self.processed_ids),
                'stats': self.stats
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠ Warning: Could not save checkpoint: {e}")
    
    def is_processed(self, entry_id: int) -> bool:
        return entry_id in self.processed_ids
    
    def mark_processed(self, entry_id: int, success: bool = True, chunks_created: int = 0):
        self.processed_ids.add(entry_id)
        self.stats['total_processed'] += 1
        if success:
            self.stats['successful'] += 1
            self.stats['chunks_created'] += chunks_created
        else:
            self.stats['failed'] += 1

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Thread-safe rate limiter for API calls."""
    
    def __init__(self, max_requests_per_second: float = 10.0):
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                time.sleep(self.min_interval - time_since_last)
            self.last_request_time = time.time()

# ============================================================================
# PARALLEL PROCESSOR
# ============================================================================

@dataclass
class ProcessingResult:
    entry_id: int
    success: bool
    data: Any
    error: Optional[str] = None
    chunks_created: int = 0

class ParallelLLMProcessor:
    """Parallel processor for LLM API calls."""
    
    def __init__(self, max_workers: int = 10, max_requests_per_second: float = 10.0, max_retries: int = 3):
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(max_requests_per_second)
        self.max_retries = max_retries
    
    def process_with_retry(self, process_func: Callable, entry: Dict, entry_id: int) -> ProcessingResult:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.rate_limiter.acquire()
                result = process_func(entry, entry_id)
                return ProcessingResult(
                    entry_id=entry_id,
                    success=True,
                    data=result.get('chunks', []),
                    chunks_created=len(result.get('chunks', []))
                )
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return ProcessingResult(
            entry_id=entry_id,
            success=False,
            data=[],
            error=last_error,
            chunks_created=0
        )
    
    def process_batch(self, entries: List[Dict], process_func: Callable, progress_callback: Optional[Callable] = None) -> List[ProcessingResult]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for entry in entries:
                future = executor.submit(
                    self.process_with_retry,
                    process_func,
                    entry,
                    entry.get('entry_num', 0)
                )
                futures[future] = entry.get('entry_num', 0)
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if progress_callback:
                    progress_callback(result)
        
        return results

# ============================================================================
# LLM PROCESSING FUNCTION
# ============================================================================

# Initialize LLM client
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

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
    """Use LLM to align mismatched English-Hindi pairs."""
    user_prompt = f"""Align these English-Hindi texts into 3-sentence chunks:

ENGLISH ({entry['eng_sentences']} sentences):
{entry['english']}

HINDI ({entry['hin_sentences']} sentences):
{entry['hindi']}

Create aligned chunks (max 3 English sentences per chunk) as JSON array."""

    response = client.chat.completions.create(
        model=LLM_MODEL,
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

# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

def process_optimized(resume=True):
    """Process the dataset with optimizations."""
    print("=" * 70)
    print("OPTIMIZED BILINGUAL PIPELINE - PHASE 2")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model:              {LLM_MODEL}")
    print(f"  Max Workers:        {MAX_WORKERS}")
    print(f"  Rate Limit:         {RATE_LIMIT} req/s")
    print(f"  Input:              {INPUT_FILE}")
    print(f"  Output:             {OUTPUT_FILE}")
    
    # Initialize checkpoint
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    
    # Load entries
    print(f"\nLoading entries from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_entries = [json.loads(line) for line in f]
    
    total_entries = len(all_entries)
    print(f"Loaded {total_entries} entries")
    
    # Filter processed entries
    if resume and len(checkpoint.processed_ids) > 0:
        entries_to_process = [
            e for e in all_entries 
            if not checkpoint.is_processed(e.get('entry_num', 0))
        ]
        print(f"Resuming: {len(checkpoint.processed_ids)} done, {len(entries_to_process)} remaining")
    else:
        entries_to_process = all_entries
    
    if not entries_to_process:
        print("\n✓ All entries already processed!")
        return
    
    # Initialize processor
    processor = ParallelLLMProcessor(
        max_workers=MAX_WORKERS,
        max_requests_per_second=RATE_LIMIT,
        max_retries=3
    )
    
    # Open output file
    output_mode = 'a' if resume else 'w'
    outfile = open(OUTPUT_FILE, output_mode, encoding='utf-8')
    
    # Progress bar
    pbar = tqdm(total=len(entries_to_process), desc="Processing", unit="entry")
    
    # Progress callback
    def on_progress(result):
        status = "✓" if result.success else "✗"
        pbar.set_postfix({
            'status': status,
            'chunks': result.chunks_created,
            'rate': f"{checkpoint.stats['successful']}/{checkpoint.stats['total_processed']}"
        })
        pbar.update(1)
        
        if result.success:
            for chunk in result.data:
                outfile.write(json.dumps({
                    'english': chunk['english'],
                    'hindi': chunk['hindi']
                }, ensure_ascii=False) + '\n')
        
        checkpoint.mark_processed(result.entry_id, result.success, result.chunks_created)
        
        if checkpoint.stats['total_processed'] % CHECKPOINT_INTERVAL == 0:
            checkpoint.save()
            outfile.flush()
    
    try:
        # Process in parallel
        start_time = time.time()
        results = processor.process_batch(
            entries_to_process,
            align_with_llm,
            progress_callback=on_progress
        )
        
        checkpoint.save()
        elapsed_time = time.time() - start_time
        
        pbar.close()
        outfile.close()
        
        # Summary
        stats = checkpoint.stats
        print("\n" + "=" * 70)
        print("✅ PROCESSING COMPLETE")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  Total processed:       {stats['total_processed']}")
        print(f"  Successfully aligned:  {stats['successful']}")
        print(f"  Failed:                {stats['failed']}")
        print(f"  Total chunks created:  {stats['chunks_created']}")
        print(f"  Processing time:       {elapsed_time:.1f}s ({elapsed_time/60:.1f} min)")
        print(f"  Processing rate:       {stats['total_processed']/elapsed_time:.2f} entries/s")
        print(f"\n📁 Output: {OUTPUT_FILE} ({stats['chunks_created']} chunks)")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n⚠ Interrupted! Saving checkpoint...")
        checkpoint.save()
        outfile.close()
        pbar.close()
        print("✓ Checkpoint saved")

# ============================================================================
# RUN THE PIPELINE
# ============================================================================

if __name__ == "__main__":
    process_optimized(resume=True)
