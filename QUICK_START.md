# Quick Start: LLM Alignment

## Run the Demo

```bash
# Navigate to project directory
cd "d:\ADARSH\7_Programming Files\1. Programming files\Python\Rewat-Forge"

# Run the example
python example_llm_alignment.py
```

## Test Integration

```bash
# Test that everything is installed correctly
python test_llm_alignment.py
```

## Use in Your Pipeline

1. **Edit config.py:**
   ```python
   USE_LLM_ALIGNMENT = True
   ```

2. **Run pipeline:**
   ```bash
   python rewat_pipeline.py english.pdf hindi.pdf
   ```

## Common Issues

**Import Error?**
- Make sure you're in the project directory
- Check that `modules/llm_alignment.py` exists

**API Error?**
- Verify `LLM_API_KEY` in config.py
- Check `LLM_BASE_URL` is correct
- Ensure you have API credits

**No Output?**
- Check both English and Hindi text are non-empty
- Lower temperature to 0.0 for more deterministic results
- Try a different model (gpt-4o-mini is very reliable)

## Next Steps

1. ✅ Run `python example_llm_alignment.py`
2. ✅ Review output and aligned pairs
3. ✅ Read `LLM_ALIGNMENT_GUIDE.md` for details
4. ✅ Integrate into your workflow
