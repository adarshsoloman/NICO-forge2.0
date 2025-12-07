# Rewat's Performance Optimization Guide

## 📊 Current Performance Analysis (Your Test)

**Results from your 32-entry test:**
- Time: 175.9 seconds (2.9 minutes)
- Average per entry: **5.5 seconds**
- Workers: 20
- Model: gpt-4o-mini

**Projection for 75,000 rows:**
```
75,000 × 5.5s = 412,500s = 114.6 hours = 4.8 days
With 20 workers: 4.8 days ❌ TOO SLOW!
```

---

## 🚀 Rewat's Optimizations

### 1. Switch to Faster Model (Flash 2.0)

**Update your `.env` file:**

```bash
# Change from:
LLM_MODEL=gpt-4o-mini

# To (Rewat's recommendation):
LLM_MODEL=google/gemini-2.0-flash-exp:free
# OR
LLM_MODEL=google/gemini-flash-1.5
```

**Why:** Gemini Flash 2.0 is:
- **3-5x faster** per request
- **Cheaper** (or free)
- **Good context size** for mapping tasks
- **Just as good** for this type of alignment work

---

### 2. Increase Workers

**Current:**
```bash
--max-workers 20
```

**Optimized (for 75k dataset):**
```bash
--max-workers 50  # Aggressive
# OR
--max-workers 30  # Conservative
```

**ETA Formula (Rewat's suggestion):**
```
Target Time = (Total Rows × Avg Time per Row) / Number of Workers
```

**With 50 workers + Flash 2.0 (2s per entry):**
```
75,000 × 2s / 50 = 3,000s = 50 minutes ✅
```

---

### 3. Enable Prompt Caching (Future Enhancement)

Prompt caching reuses system prompts across requests:
- **Reduces latency** by ~50%
- **Reduces cost** significantly
- **Supported by** Anthropic Claude & Google Gemini

**To enable in future updates:**
- Add caching headers to API calls
- Reuse system prompt across all requests

---

## ⚡ Quick Configuration Changes

### Option A: Update `.env` File (Recommended)

```bash
nano .env
```

Add/Update:
```
LLM_MODEL=google/gemini-2.0-flash-exp:free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-key-here
```

### Option B: Use Command-Line Override

Run with explicit model:
```bash
# Set environment variable for this session
export LLM_MODEL="google/gemini-2.0-flash-exp:free"

# Then run pipeline
python3 chunk_sentences_phase2_optimized.py \
  --input pib_mismatched_for_llm.jsonl \
  --output output.jsonl \
  --max-workers 50
```

---

## 📈 Expected Performance with Optimizations

| Configuration | Workers | Model | Time/Entry | Total Time (75k) |
|---------------|---------|-------|------------|------------------|
| **Current** | 20 | gpt-4o-mini | 5.5s | 4.8 days ❌ |
| **Optimized v1** | 30 | Flash 2.0 | 2.0s | 1.4 hours ✅ |
| **Optimized v2** | 50 | Flash 2.0 | 2.0s | **50 minutes** ✅✅ |
| **With Caching** | 50 | Flash 2.0 | 1.0s | **25 minutes** 🚀 |

---

## 🎯 Recommended Commands for 75k Dataset

### Step 1: Update Model in `.env`
```bash
# Edit .env file
nano .env

# Change:
LLM_MODEL=google/gemini-2.0-flash-exp:free
```

### Step 2: Run with High Worker Count
```bash
# Activate venv
source .venv/bin/activate

# Process with 50 workers
python3 chunk_sentences_phase2_optimized.py \
  --input your_5000_chunk.jsonl \
  --output processed_output.jsonl \
  --max-workers 50 \
  --rate-limit 50.0 \
  --checkpoint-interval 500
```

**Expected:** 5,000 rows in ~3-5 minutes (vs 30-45 minutes currently)

---

## 🧪 Test Before Full Run

Test with small file first:
```bash
# Create 100-entry test file
head -100 your_large_file.jsonl > test_100.jsonl

# Test with Flash 2.0 + 50 workers
python3 chunk_sentences_phase2_optimized.py \
  --input test_100.jsonl \
  --output test_output.jsonl \
  --max-workers 50

# Check time per entry
# Should be ~2 seconds per entry with Flash 2.0
```

---

## 💰 Cost Comparison

| Model | Cost per 1M tokens | Speed | Quality |
|-------|-------------------|-------|---------|
| gpt-4o-mini | $0.15 / $0.60 | Medium | High |
| **gemini-flash-2.0** | $0.075 / $0.30 | **Fast** | High |
| gemini-flash-1.5 | $0.075 / $0.30 | Fast | High |

**For 75k rows:** Flash 2.0 will save ~50% cost AND be 3-5x faster!

---

## 📝 Summary of Changes Needed

1. ✅ **Model:** gpt-4o-mini → Gemini Flash 2.0
2. ✅ **Workers:** 20 → 50
3. ✅ **Rate Limit:** 10 → 50 req/s
4. 🔮 **Future:** Enable prompt caching

**Result:** 4.8 days → ~1 hour for 75k rows! 🚀
