"""
Parallel LLM Processor
======================
Utilities for parallel LLM API calls with rate limiting and error handling.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Dict, Optional
from dataclasses import dataclass


class RateLimiter:
    """
    Thread-safe rate limiter for API calls.
    
    Uses token bucket algorithm to limit requests per second.
    """
    
    def __init__(self, max_requests_per_second: float = 10.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_second: Maximum requests allowed per second
        """
        self.max_requests = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def acquire(self):
        """Wait if necessary to respect rate limit."""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


@dataclass
class ProcessingResult:
    """Result from processing a single item."""
    entry_id: int
    success: bool
    data: Any
    error: Optional[str] = None
    chunks_created: int = 0


class ParallelLLMProcessor:
    """
    Parallel processor for LLM API calls.
    
    Features:
    - Thread pool for concurrent processing
    - Rate limiting to respect API limits
    - Automatic retry with exponential backoff
    - Progress tracking
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        max_requests_per_second: float = 10.0,
        max_retries: int = 3
    ):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Number of concurrent workers
            max_requests_per_second: Rate limit for API calls
            max_retries: Maximum retry attempts for failed requests
        """
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(max_requests_per_second)
        self.max_retries = max_retries
    
    def process_with_retry(
        self,
        process_func: Callable,
        entry: Dict[str, Any],
        entry_id: int
    ) -> ProcessingResult:
        """
        Process a single entry with retry logic.
        
        Args:
            process_func: Function to process the entry
            entry: Entry data to process
            entry_id: Unique ID for the entry
        
        Returns:
            ProcessingResult with success status and data
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Respect rate limit
                self.rate_limiter.acquire()
                
                # Call processing function
                result = process_func(entry, entry_id)
                
                # Success
                return ProcessingResult(
                    entry_id=entry_id,
                    success=True,
                    data=result.get('chunks', []),
                    chunks_created=len(result.get('chunks', []))
                )
                
            except Exception as e:
                last_error = str(e)
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait_time)
        
        # All retries failed
        return ProcessingResult(
            entry_id=entry_id,
            success=False,
            data=[],
            error=last_error,
            chunks_created=0
        )
    
    def process_batch(
        self,
        entries: List[Dict[str, Any]],
        process_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[ProcessingResult]:
        """
        Process a batch of entries in parallel.
        
        Args:
            entries: List of entries to process
            process_func: Function to process each entry
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of ProcessingResults
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, entry in enumerate(entries):
                future = executor.submit(
                    self.process_with_retry,
                    process_func,
                    entry,
                    entry.get('entry_num', i)
                )
                futures[future] = entry.get('entry_num', i)
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                # Progress callback
                if progress_callback:
                    progress_callback(result)
        
        return results
    
    def process_stream(
        self,
        entry_iterator,
        process_func: Callable,
        progress_callback: Optional[Callable] = None,
        batch_size: int = 100
    ):
        """
        Process entries from an iterator in batches.
        
        Yields results as they're completed, allowing for streaming processing.
        
        Args:
            entry_iterator: Iterator of entries
            process_func: Function to process each entry
            progress_callback: Optional callback for progress updates
            batch_size: Number of entries to process in each batch
        
        Yields:
            ProcessingResult objects
        """
        batch = []
        
        for entry in entry_iterator:
            batch.append(entry)
            
            if len(batch) >= batch_size:
                # Process batch
                results = self.process_batch(batch, process_func, progress_callback)
                for result in results:
                    yield result
                
                # Clear batch
                batch = []
        
        # Process remaining entries
        if batch:
            results = self.process_batch(batch, process_func, progress_callback)
            for result in results:
                yield result
