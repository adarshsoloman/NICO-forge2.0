#!/bin/bash
# Complete BilingualForge Pipeline Runner for pib_bilingual.jsonl
# Uses OPTIMIZED scripts for 3x faster processing

set -e  # Exit on error

echo "=========================================="
echo "BilingualForge - Complete Pipeline"
echo "=========================================="
echo ""
echo "Input: pib_bilingual.jsonl"
echo "Expected Time: ~40-60 minutes"
echo ""

# Configuration
MAX_WORKERS=15
RATE_LIMIT=15.0

# Step 1: Basic Cleaning
echo "=========================================="
echo "STEP 1/5: Basic Cleaning"
echo "=========================================="
echo "Command: .venv/bin/python3 clean_pib_bilingual.py"
echo ""

.venv/bin/python3 clean_pib_bilingual.py

if [ -f "pib_bilingual_cleaned.jsonl" ]; then
  LINES=$(wc -l < pib_bilingual_cleaned.jsonl)
  echo "✓ Step 1 Complete: $LINES entries cleaned"
else
  echo "✗ Error: pib_bilingual_cleaned.jsonl not created"
  exit 1
fi

echo ""
sleep 1

# Step 2: LLM Deep Cleaning (Optimized)
echo "=========================================="
echo "STEP 2/5: LLM Deep Cleaning (Optimized)"
echo "=========================================="
echo "Command: .venv/bin/python3 llm_deep_clean_phase2_optimized.py"
echo "Workers: $MAX_WORKERS | Rate Limit: $RATE_LIMIT req/sec"
echo ""

.venv/bin/python3 llm_deep_clean_phase2_optimized.py \
  --input pib_bilingual_cleaned.jsonl \
  --output pib_bilingual_final.jsonl \
  --max-workers $MAX_WORKERS \
  --rate-limit $RATE_LIMIT \
  --checkpoint-interval 50

if [ -f "pib_bilingual_final.jsonl" ]; then
  LINES=$(wc -l < pib_bilingual_final.jsonl)
  echo "✓ Step 2 Complete: $LINES entries LLM cleaned"
else
  echo "✗ Error: pib_bilingual_final.jsonl not created"
  exit 1
fi

echo ""
sleep 1

# Step 3: Phase 1 Chunking
echo "=========================================="
echo "STEP 3/5: Phase 1 Chunking (Automatic)"
echo "=========================================="
echo "Command: .venv/bin/python3 chunk_sentences_phase1.py"
echo ""

.venv/bin/python3 chunk_sentences_phase1.py

if [ -f "pib_chunked_matched.jsonl" ]; then
  MATCHED=$(wc -l < pib_chunked_matched.jsonl)
  echo "✓ Matched chunks: $MATCHED"
else
  MATCHED=0
  echo "⚠ Warning: pib_chunked_matched.jsonl not found"
fi

if [ -f "pib_mismatched_for_llm.jsonl" ]; then
  UNMATCHED=$(wc -l < pib_mismatched_for_llm.jsonl)
  echo "⚠ Unmatched entries: $UNMATCHED (will process in Step 4)"
else
  UNMATCHED=0
  echo "✓ All entries matched! Skipping Step 4"
fi

echo ""
sleep 1

# Step 4: Phase 2 LLM Chunking (Only if there are unmatched entries)
if [ -f "pib_mismatched_for_llm.jsonl" ] && [ $(wc -l < pib_mismatched_for_llm.jsonl) -gt 0 ]; then
  echo "=========================================="
  echo "STEP 4/5: Phase 2 LLM Chunking (Optimized)"
  echo "=========================================="
  echo "Command: .venv/bin/python3 chunk_sentences_phase2_optimized.py"
  echo "Workers: 20 | Rate Limit: 20.0 req/sec"
  echo ""

  .venv/bin/python3 chunk_sentences_phase2_optimized.py \
    --input pib_mismatched_for_llm.jsonl \
    --output pib_chunked_llm_aligned.jsonl \
    --max-workers 20 \
    --rate-limit 20.0 \
    --checkpoint-interval 100

  if [ -f "pib_chunked_llm_aligned.jsonl" ]; then
    LLM_ALIGNED=$(wc -l < pib_chunked_llm_aligned.jsonl)
    echo "✓ Step 4 Complete: $LLM_ALIGNED chunks LLM aligned"
  else
    echo "✗ Error: pib_chunked_llm_aligned.jsonl not created"
    exit 1
  fi
else
  echo "=========================================="
  echo "STEP 4/5: Phase 2 LLM Chunking (SKIPPED)"
  echo "=========================================="
  echo "✓ No unmatched entries - all chunks aligned automatically!"
  echo ""
  # Create empty file so merge works
  touch pib_chunked_llm_aligned.jsonl
fi

echo ""
sleep 1

# Step 5: Merge Results
echo "=========================================="
echo "STEP 5/5: Merging Final Dataset"
echo "=========================================="
echo ""

cat pib_chunked_matched.jsonl pib_chunked_llm_aligned.jsonl > pib_final_dataset.jsonl

if [ -f "pib_final_dataset.jsonl" ]; then
  TOTAL=$(wc -l < pib_final_dataset.jsonl)
  echo "✓ Step 5 Complete: Final dataset created"
  echo ""
  echo "=========================================="
  echo "PIPELINE COMPLETE! 🎉"
  echo "=========================================="
  echo ""
  echo "Final Output: pib_final_dataset.jsonl"
  echo "Total Chunks: $TOTAL"
  echo ""
  echo "Breakdown:"
  echo "  - Matched (auto):    $MATCHED chunks"
  echo "  - LLM aligned:       $(wc -l < pib_chunked_llm_aligned.jsonl) chunks"
  echo "  - Total:             $TOTAL chunks"
  echo ""
  echo "Sample output (first 3 entries):"
  head -3 pib_final_dataset.jsonl | jq -C '.'
  echo ""
  echo "✅ Your production-ready dataset is ready!"
  echo ""
else
  echo "✗ Error: Failed to create final dataset"
  exit 1
fi
