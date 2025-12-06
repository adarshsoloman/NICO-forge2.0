# LLM-Based Semantic Alignment Guide

This guide explains how to use the new **LLM-based semantic alignment** feature in Rewat-Forge, which uses Rewat's alignment prompt to intelligently match English and Hindi text chunks.

## Overview

Rewat-Forge now supports two alignment methods:

### 1. **Index-Based Alignment** (Default)
- Fast and deterministic
- Pairs chunks by position/index
- Works well for strictly page-aligned PDFs
- No LLM calls required

### 2. **LLM-Based Semantic Alignment** (New)
- Uses AI to semantically match translations
- More accurate for misaligned or complex documents
- Handles variations in text structure
- Requires LLM API calls

## How LLM Alignment Works

The LLM alignment uses Rewat's specialized system prompt to:

1. **Receive raw corpus**: Takes English and Hindi text from each page
2. **Semantic matching**: LLM intelligently maps English chunks to their precise Hindi translations
3. **Exact extraction**: Only uses verbatim text from the corpus (no paraphrasing)
4. **Structured output**: Returns clean CSV mappings in `<csv></csv>` format

### Key Rules

✅ Chunks are 1-3 sentences maximum  
✅ Only exact text from corpus (no synthetic text)  
✅ No grammar fixes or modifications  
✅ Only produces clean, confirmed mappings  

## Configuration

Edit `config.py` to enable LLM alignment:

```python
# Enable LLM-based semantic alignment
USE_LLM_ALIGNMENT = True

# Make sure LLM settings are configured
USE_LLM_VERIFICATION = True  # Can be different from alignment
LLM_BASE_URL = "https://api.bytez.com/v1"
LLM_API_KEY = "your-api-key-here"
LLM_MODEL = "gpt-4o-mini"  # Or any OpenAI-compatible model
LLM_TEMPERATURE = 0.1  # Lower = more consistent
```

## When to Use LLM Alignment

### ✅ Use LLM Alignment When:
- PDFs are not strictly page-aligned
- Text structure varies between languages
- You need higher accuracy over speed
- Documents have complex formatting
- You want to handle missing sections gracefully

### ❌ Use Index Alignment When:
- PDFs are perfectly page-aligned
- Speed is critical
- You have limited API budget
- Documents have consistent 1:1 sentence mapping

## Usage Example

### Basic Usage

```python
from openai import OpenAI
from modules.llm_alignment import align_with_llm

# Initialize LLM client
client = OpenAI(
    base_url="https://api.bytez.com/v1",
    api_key="your-api-key"
)

# Raw text from a PDF page
english_text = """
Chapter 3 discusses photosynthesis. It is a vital process.
Plants use sunlight to create food.
"""

hindi_text = """
अध्याय 3 प्रकाश संश्लेषण पर चर्चा करता है। यह एक महत्वपूर्ण प्रक्रिया है।
पौधे भोजन बनाने के लिए सूर्य के प्रकाश का उपयोग करते हैं।
"""

# Perform LLM alignment
aligned_pairs = align_with_llm(
    english_text=english_text,
    hindi_text=hindi_text,
    llm_client=client,
    model="gpt-4o-mini",
    temperature=0.1
)

# Result: [
#   ("Chapter 3 discusses photosynthesis. It is a vital process.",
#    "अध्याय 3 प्रकाश संश्लेषण पर चर्चा करता है। यह एक महत्वपूर्ण प्रक्रिया है।"),
#   ("Plants use sunlight to create food.",
#    "पौधे भोजन बनाने के लिए सूर्य के प्रकाश का उपयोग करते हैं।")
# ]
```

### Batch Processing Multiple Pages

```python
from modules.llm_alignment import batch_align_pages

page_pairs = [
    (english_page1, hindi_page1),
    (english_page2, hindi_page2),
    (english_page3, hindi_page3),
]

# Process all pages
results = batch_align_pages(
    page_pairs=page_pairs,
    llm_client=client,
    model="gpt-4o-mini",
    temperature=0.1
)

# results[0] = alignments for page 1
# results[1] = alignments for page 2
# etc.
```

## Integrating with Pipeline

To use LLM alignment in the main pipeline, you would modify `rewat_pipeline.py`:

```python
import config
from modules import align_with_llm
from openai import OpenAI

# In process_page function:
if config.USE_LLM_ALIGNMENT:
    # Use semantic alignment
    client = OpenAI(
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY
    )
    
    aligned_pairs = align_with_llm(
        english_text=eng_text,
        hindi_text=hin_text,
        llm_client=client,
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE
    )
    
    # Process each aligned pair
    for chunk_id, (eng_chunk, hin_chunk) in enumerate(aligned_pairs):
        # Create CSV row with aligned chunks
        row = create_row(
            doc_id=doc_id,
            page=page_num,
            chunk_id=chunk_id,
            eng_chunk=eng_chunk,
            hin_chunk=hin_chunk,
            # ... other fields
        )
        append_row(output_csv, row)
else:
    # Use traditional index-based alignment
    # ... existing code
```

## System Prompt

The alignment uses this specialized system prompt (stored in `modules/llm_alignment.py`):

```python
from modules.llm_alignment import ALIGNMENT_SYSTEM_PROMPT

print(ALIGNMENT_SYSTEM_PROMPT)
```

You can customize the prompt by editing `modules/llm_alignment.py` if needed.

## Performance Considerations

### Speed
- **Index alignment**: ~30 pages/second
- **LLM alignment**: ~2-10 pages/second (depends on API)

### Cost
- Each page requires one LLM API call
- For 100 pages at $0.001/call = $0.10
- Use cheaper models for cost savings

### Recommended Models

| Model | Speed | Accuracy | Cost | Use Case |
|-------|-------|----------|------|----------|
| `gpt-4o-mini` | Fast | High | Low | General use |
| `gpt-4o` | Medium | Very High | Medium | High quality |
| `claude-3-5-sonnet` | Medium | Very High | Medium | Complex docs |
| `google/madlad400-7b-mt` | Fast | Good | Low | Translation-specific |
| `llama-3.1-70b` | Medium | High | Free/Low | Budget option |

## Troubleshooting

### Empty Results
If alignment returns no pairs:
- Check that both English and Hindi text are non-empty
- Verify LLM API key and endpoint are correct
- Review LLM response for error messages

### Malformed CSV Response
If you get parsing errors:
- Try lowering temperature (0.0 - 0.2)
- Use a more capable model (GPT-4 vs GPT-3.5)
- Check LLM response manually to see format

### Inconsistent Chunking
If chunk sizes vary:
- This is expected behavior (LLM decides optimal chunks)
- Maximum 3 sentences per chunk is enforced by prompt
- LLM adapts to natural translation boundaries

## Example Output

**Input:**
```
English: "The water cycle is important. It involves evaporation. Water vapor rises."
Hindi: "जल चक्र महत्वपूर्ण है। इसमें वाष्पीकरण शामिल है। जल वाष्प ऊपर उठता है।"
```

**LLM Alignment Output:**
```csv
"The water cycle is important. It involves evaporation.","जल चक्र महत्वपूर्ण है। इसमें वाष्पीकरण शामिल है।"
"Water vapor rises.","जल वाष्प ऊपर उठता है।"
```

**Index Alignment Output:**
```csv
"The water cycle is important.","जल चक्र महत्वपूर्ण है।"
"It involves evaporation.","इसमें वाष्पीकरण शामिल है।"
"Water vapor rises.","जल वाष्प ऊपर उठता है।"
```

Notice how LLM alignment intelligently groups the first two sentences because they form a semantic unit, while index alignment strictly maintains 1:1 sentence mapping.

## Best Practices

1. **Test on small samples first**: Try a few pages before processing entire documents
2. **Compare both methods**: Run same document with both alignments and compare quality
3. **Monitor costs**: Track API usage for large batches
4. **Use appropriate models**: Balance cost, speed, and accuracy
5. **Validate output**: Spot-check aligned pairs for quality

## Need Help?

- Check `errors.log` for detailed error messages
- Review LLM response manually in debug mode
- Test with minimal examples first
- Verify API credentials and quotas

---

**Developed as part of Rewat-Forge bilingual dataset extraction initiative.**
