"""
Quick validation script to test Rewat-Forge modules

This script tests each module individually to ensure they work correctly.
"""

import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    try:
        from modules import (
            extract_page_text,
            get_page_count,
            split_sentences,
            create_chunks,
            align_chunks,
            llm_map,
            extract_patterns,
            append_row,
            initialize_csv,
            create_row
        )
        print("  ✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_sentence_splitting():
    """Test sentence splitting for English and Hindi."""
    print("\nTesting sentence splitting...")
    from modules import split_sentences
    
    try:
        # Test English
        eng_text = "This is sentence one. This is sentence two! Is this sentence three?"
        eng_sentences = split_sentences(eng_text, 'english')
        assert len(eng_sentences) == 3, f"Expected 3 English sentences, got {len(eng_sentences)}"
        
        # Test Hindi
        hin_text = "यह पहला वाक्य है। यह दूसरा वाक्य है! क्या यह तीसरा वाक्य है?"
        hin_sentences = split_sentences(hin_text, 'hindi')
        assert len(hin_sentences) == 3, f"Expected 3 Hindi sentences, got {len(hin_sentences)}"
        
        print(f"  ✓ English split: {len(eng_sentences)} sentences")
        print(f"  ✓ Hindi split: {len(hin_sentences)} sentences")
        return True
    except Exception as e:
        print(f"  ✗ Splitting failed: {e}")
        return False


def test_chunking():
    """Test sentence chunking."""
    print("\nTesting chunking...")
    from modules import create_chunks
    
    try:
        sentences = ["One.", "Two.", "Three.", "Four.", "Five."]
        chunks = create_chunks(sentences, chunk_size=2)
        assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"
        assert chunks[0] == "One. Two.", f"First chunk mismatch: {chunks[0]}"
        
        print(f"  ✓ Created {len(chunks)} chunks from {len(sentences)} sentences")
        print(f"  ✓ First chunk: '{chunks[0]}'")
        return True
    except Exception as e:
        print(f"  ✗ Chunking failed: {e}")
        return False


def test_alignment():
    """Test chunk alignment."""
    print("\nTesting alignment...")
    from modules import align_chunks
    
    try:
        eng = ["English 1", "English 2", "English 3"]
        hin = ["Hindi 1", "Hindi 2"]  # Intentionally shorter
        
        aligned = align_chunks(eng, hin)
        assert len(aligned) == 3, f"Expected 3 pairs, got {len(aligned)}"
        assert aligned[2][1] == "", "Expected empty string for padding"
        
        print(f"  ✓ Aligned {len(eng)} eng chunks with {len(hin)} hindi chunks")
        print(f"  ✓ Result: {len(aligned)} aligned pairs (with padding)")
        return True
    except Exception as e:
        print(f"  ✗ Alignment failed: {e}")
        return False


def test_regex_extraction():
    """Test regex pattern extraction."""
    print("\nTesting regex extraction...")
    from modules import extract_patterns
    
    try:
        text = "Chapter 5 was written in 2024. अध्याय 3 discusses history."
        patterns = [r'\b\d{4}\b', r'Chapter \d+', r'अध्याय \d+']
        
        matches_json = extract_patterns(text, patterns)
        import json
        matches = json.loads(matches_json)
        
        assert "2024" in matches, "Year not extracted"
        assert "Chapter 5" in matches, "Chapter not extracted"
        
        print(f"  ✓ Extracted {len(matches)} matches: {matches}")
        return True
    except Exception as e:
        print(f"  ✗ Regex extraction failed: {e}")
        return False


def test_llm_verifier_disabled():
    """Test LLM verifier when disabled."""
    print("\nTesting LLM verifier (disabled mode)...")
    from modules import llm_map
    import config
    
    try:
        # Ensure LLM is disabled
        original_setting = config.USE_LLM_VERIFICATION
        config.USE_LLM_VERIFICATION = False
        
        eng = "This is a test."
        hin_raw = "यह एक परीक्षण है।"
        
        hin_verified, flags = llm_map(eng, hin_raw)
        
        assert hin_verified == hin_raw, "Verified should match raw when LLM disabled"
        assert flags == "", "No flags expected when LLM disabled"
        
        # Restore setting
        config.USE_LLM_VERIFICATION = original_setting
        
        print(f"  ✓ LLM correctly bypassed when disabled")
        print(f"  ✓ Returned raw Hindi unchanged")
        return True
    except Exception as e:
        print(f"  ✗ LLM verifier test failed: {e}")
        return False


def test_csv_row_creation():
    """Test CSV row creation."""
    print("\nTesting CSV row creation...")
    from modules import create_row
    
    try:
        row = create_row(
            doc_id="test_doc",
            page=1,
            chunk_id=0,
            eng_chunk="English text",
            hin_chunk_raw="Hindi raw",
            hin_chunk_verified="Hindi verified",
            alignment_method="index",
            regex_matches='["match1"]',
            llm_flags=""
        )
        
        assert row['doc_id'] == "test_doc"
        assert row['page'] == 1
        assert 'timestamp' in row
        
        print(f"  ✓ Row created with {len(row)} fields")
        print(f"  ✓ Timestamp: {row['timestamp']}")
        return True
    except Exception as e:
        print(f"  ✗ Row creation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("REWAT-FORGE MODULE VALIDATION")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_sentence_splitting,
        test_chunking,
        test_alignment,
        test_regex_extraction,
        test_llm_verifier_disabled,
        test_csv_row_creation,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✨ All tests passed! Pipeline modules are working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
