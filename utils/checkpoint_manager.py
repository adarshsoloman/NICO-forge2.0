"""
Checkpoint Manager
==================
Manages checkpoints for resumable long-running processing tasks.
"""

import json
import os
from typing import Set, Dict, Any
from pathlib import Path


class CheckpointManager:
    """
    Manages checkpoint state for resumable processing.
    
    Tracks:
    - Processed entry IDs/numbers
    - Progress statistics
    - Last processed timestamp
    """
    
    def __init__(self, checkpoint_file: str):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = checkpoint_file
        self.processed_ids: Set[int] = set()
        self.stats: Dict[str, Any] = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'chunks_created': 0
        }
        
        # Load existing checkpoint if available
        self._load()
    
    def _load(self):
        """Load checkpoint from file if it exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
                    self.stats = data.get('stats', self.stats)
                print(f"✓ Loaded checkpoint: {len(self.processed_ids)} entries already processed")
            except Exception as e:
                print(f"⚠ Warning: Could not load checkpoint: {e}")
                print("  Starting fresh...")
    
    def save(self):
        """Save current checkpoint state to file."""
        try:
            # Create parent directory if needed
            Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'processed_ids': list(self.processed_ids),
                'stats': self.stats
            }
            
            # Write to temp file first, then rename (atomic operation)
            temp_file = f"{self.checkpoint_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.checkpoint_file)
            
        except Exception as e:
            print(f"⚠ Warning: Could not save checkpoint: {e}")
    
    def is_processed(self, entry_id: int) -> bool:
        """Check if an entry has already been processed."""
        return entry_id in self.processed_ids
    
    def mark_processed(self, entry_id: int, success: bool = True, chunks_created: int = 0):
        """
        Mark an entry as processed.
        
        Args:
            entry_id: ID of the entry
            success: Whether processing was successful
            chunks_created: Number of chunks created from this entry
        """
        self.processed_ids.add(entry_id)
        self.stats['total_processed'] += 1
        
        if success:
            self.stats['successful'] += 1
            self.stats['chunks_created'] += chunks_created
        else:
            self.stats['failed'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.stats.copy()
    
    def get_remaining_count(self, total_entries: int) -> int:
        """Get number of entries remaining to process."""
        return total_entries - len(self.processed_ids)
    
    def clear(self):
        """Clear checkpoint (start fresh)."""
        self.processed_ids.clear()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'chunks_created': 0
        }
        
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("✓ Checkpoint cleared")
