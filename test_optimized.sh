#!/bin/bash
# Test script for optimized pipeline

echo "=========================================="
echo "Testing Optimized Pipeline Locally"
echo "=========================================="
echo ""

# Test 1: Small test (10 entries)
echo "Test 1: Running with 10 test entries..."
echo "Command: python chunk_sentences_phase2_optimized.py --input test_10_entries.jsonl --output test_output_10.jsonl --max-workers 5"
echo ""

python chunk_sentences_phase2_optimized.py \
  --input test_10_entries.jsonl \
  --output test_output_10.jsonl \
  --max-workers 5 \
  --checkpoint-interval 5

echo ""
echo "=========================================="
echo "Test 1 Complete!"
echo "=========================================="
echo ""
echo "Output file: test_output_10.jsonl"
echo "Checkpoint: checkpoints/phase2_checkpoint.json"
echo ""

# Show results
if [ -f test_output_10.jsonl ]; then
  lines=$(wc -l < test_output_10.jsonl)
  echo "✓ Output file created with $lines chunks"
  echo ""
  echo "Sample output (first 2 entries):"
  head -2 test_output_10.jsonl | jq -C '.'
else
  echo "✗ Output file not created"
fi
