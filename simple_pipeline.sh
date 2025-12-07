#!/bin/bash
# Simple Command Sequence for BilingualForge Pipeline
# Copy and paste these commands one by one, or run this script

# ========================================
# OPTIMIZED Pipeline Commands (RECOMMENDED)
# ========================================

# Step 1: Basic Cleaning (~10 seconds)
.venv/bin/python3 clean_pib_bilingual.py

# Step 2: LLM Deep Cleaning - Optimized (~15-20 min)
.venv/bin/python3 llm_deep_clean_phase2_optimized.py \
  --input pib_bilingual_cleaned.jsonl \
  --output pib_bilingual_final.jsonl \
  --max-workers 15 \
  --rate-limit 15.0

# Step 3: Phase 1 Chunking (~10 seconds)
.venv/bin/python3 chunk_sentences_phase1.py

# Step 4: Phase 2 LLM Chunking - Optimized (~20-30 min)
.venv/bin/python3 chunk_sentences_phase2_optimized.py \
  --input pib_mismatched_for_llm.jsonl \
  --output pib_chunked_llm_aligned.jsonl \
  --max-workers 20 \
  --rate-limit 20.0

# Step 5: Merge Final Dataset
cat pib_chunked_matched.jsonl pib_chunked_llm_aligned.jsonl > pib_final_dataset.jsonl

# Verify Output
wc -l pib_final_dataset.jsonl
echo "✅ Pipeline Complete! Output: pib_final_dataset.jsonl"
