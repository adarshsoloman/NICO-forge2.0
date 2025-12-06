"""
Simple Test: Verify LLM Alignment Works

This is a minimal test to check if the LLM alignment module works.
"""

print("=" * 70)
print("TESTING LLM ALIGNMENT MODULE")
print("=" * 70)
print()

# Test 1: Import the module
print("Test 1: Importing module...")
try:
    from modules.llm_alignment import align_with_llm, ALIGNMENT_SYSTEM_PROMPT
    from openai import OpenAI
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Check config
print("\nTest 2: Checking configuration...")
try:
    import config
    print(f"✅ LLM_BASE_URL: {config.LLM_BASE_URL}")
    print(f"✅ LLM_MODEL: {config.LLM_MODEL}")
    print(f"✅ USE_LLM_ALIGNMENT: {config.USE_LLM_ALIGNMENT}")
except Exception as e:
    print(f"❌ Config error: {e}")
    exit(1)

# Test 3: Show system prompt
print("\nTest 3: System prompt loaded...")
print(f"✅ Prompt length: {len(ALIGNMENT_SYSTEM_PROMPT)} characters")
print(f"✅ Preview: {ALIGNMENT_SYSTEM_PROMPT[:100]}...")

# Test 4: Initialize client
print("\nTest 4: Initializing LLM client...")
try:
    client = OpenAI(
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY
    )
    print("✅ Client initialized")
except Exception as e:
    print(f"❌ Client initialization failed: {e}")
    exit(1)

# Test 5: Run a simple alignment (this will make an API call)
print("\nTest 5: Running LLM alignment (this will make an API call)...")
print("⚠️  This requires API credits and internet connection")
print()

english_text = "Hello world. This is a test."
hindi_text = "नमस्ते दुनिया। यह एक परीक्षण है।"

try:
    aligned_pairs = align_with_llm(
        english_text=english_text,
        hindi_text=hindi_text,
        llm_client=client,
        model=config.LLM_MODEL,
        temperature=0.1
    )
    
    print(f"✅ Alignment successful! Found {len(aligned_pairs)} pairs")
    print()
    
    for i, (eng, hin) in enumerate(aligned_pairs, 1):
        print(f"Pair {i}:")
        print(f"  EN: {eng}")
        print(f"  HI: {hin}")
        print()
    
except Exception as e:
    print(f"❌ Alignment failed: {e}")
    print()
    print("This could be due to:")
    print("  - Invalid API key")
    print("  - No API credits")
    print("  - Network connection issue")
    print("  - Model unavailable")
    exit(1)

print("=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print()
print("The LLM alignment module is working correctly.")
print("You can now use it in your pipeline or custom scripts.")
