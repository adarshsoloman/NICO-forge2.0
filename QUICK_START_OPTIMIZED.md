# 🚀 Quick Start Guide - Optimized Pipeline

## For Google Colab (RECOMMENDED - Easiest)

### Option 1: Standalone Script (Copy-Paste)

1. **Open Google Colab**: https://colab.research.google.com
2. **Create new notebook**
3. **Copy entire content** of `colab_optimized_standalone.py`
4. **Paste into a code cell**
5. **Update configuration** (lines 13-18):
   ```python
   LLM_API_KEY = "your-actual-api-key"  # Your OpenRouter key
   INPUT_FILE = "your_file.jsonl"  # Your uploaded file
   MAX_WORKERS = 15  # 10-20 recommended
   ```
6. **Upload your JSONL file** using Colab's file browser
7. **Click Run** ▶️
8. **Watch progress bar** - 5,000 rows in ~30-45 minutes!

### Option 2: Upload Python Files

1. Upload these files to Colab:
   - `colab_optimized_standalone.py`
   - Your data file (e.g., `chunk_001.jsonl`)
2. Set API key
3. Run: `!python colab_optimized_standalone.py`

---

## For Local / Lightning AI

### Installation

```bash
# Navigate to project directory
cd Rewat-Forge

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Process your 5,000-row chunk file
python chunk_sentences_phase2_optimized.py \
  --input your_chunk_file.jsonl \
  --output processed_output.jsonl \
  --max-workers 20

# Expected: ~30-45 minutes for 5,000 rows
```

### If Interrupted (Checkpoint Resume)

```bash
# Just add --resume flag
python chunk_sentences_phase2_optimized.py \
  --input your_chunk_file.jsonl \
  --output processed_output.jsonl \
  --max-workers 20 \
  --resume
```

---

## Processing Your 75,000-Row Dataset

### Strategy: Process 15 files × 5,000 rows

```bash
# Option A: Process one file at a time
for i in {1..15}; do
  echo "Processing chunk $i/15..."
  python chunk_sentences_phase2_optimized.py \
    --input chunk_$(printf "%03d" $i).jsonl \
    --output processed_chunk_$(printf "%03d" $i).jsonl \
    --max-workers 20 \
    --checkpoint checkpoints/chunk_${i}_checkpoint.json
  
  echo "Chunk $i complete!"
done

# Merge all results
cat processed_chunk_*.jsonl > final_75k_dataset.jsonl

echo "✅ All 75,000 rows processed!"
```

**Expected total time**: ~7.5-11 hours (vs 5.6 days with original)

---

## Tuning for Your API

### Free Tier (Conservative)
```bash
python chunk_sentences_phase2_optimized.py \
  --max-workers 5 \
  --rate-limit 5.0
```

### Paid Tier (Aggressive)
```bash
python chunk_sentences_phase2_optimized.py \
  --max-workers 20 \
  --rate-limit 20.0
```

---

## Monitoring Progress

The script shows a real-time progress bar:

```
Processing: 62%|██████▏   | 3100/5000 [18:23<11:15, 2.81 entry/s] 
  status=✓ chunks=3 rate=3095/3100
```

- **62%**: Progress percentage
- **3100/5000**: Entries processed / total
- **18:23<11:15**: Elapsed < Remaining
- **2.81 entry/s**: Processing speed
- **rate=3095/3100**: Success rate

---

## Troubleshooting

### Rate Limit Errors
→ Reduce workers: `--max-workers 5`

### Out of Memory
→ Already streaming, but try: `--checkpoint-interval 25`

### Colab Timeout
→ Checkpoints save automatically! Just re-run with `--resume`

### Want to start fresh
→ Clear checkpoint: `--clear-checkpoint`

---

## What You Get

After processing:
- **Output file**: High-quality aligned chunks in JSONL format
- **Checkpoint file**: Resume state (safe to delete after completion)
- **Processing stats**: Success rate, chunks created, time taken

**Output format** (exactly same as original):
```json
{"english": "First sentence. Second sentence.", "hindi": "पहला वाक्य। दूसरा वाक्य।"}
{"english": "Another chunk of text.", "hindi": "पाठ का एक और हिस्सा।"}
```

---

## Need Help?

See detailed documentation:
- **Full Guide**: `OPTIMIZED_PIPELINE_README.md`
- **All Options**: `python chunk_sentences_phase2_optimized.py --help`

**Time Saved**: From 5.6 days to ~10 hours = **Save 4.5 days!** ⚡
