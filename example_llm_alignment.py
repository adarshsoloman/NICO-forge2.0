"""
Example: Using LLM-Based Semantic Alignment

This script demonstrates how to use the new LLM alignment module
to semantically match English-Hindi text pairs using Rewat's alignment prompt.
"""

from openai import OpenAI
from modules.llm_alignment import align_with_llm, ALIGNMENT_SYSTEM_PROMPT
import config


def main():
    """
    Example usage of LLM-based semantic alignment.
    """
    
    # Sample bilingual corpus (from a PDF page)
    english_text = """
Chapter 3: Photosynthesis

Photosynthesis is the process by which plants make their own food. 
It occurs in the chloroplasts of plant cells. The process requires sunlight, 
water, and carbon dioxide.

The main stages of photosynthesis are light-dependent reactions and 
light-independent reactions. These stages work together to produce glucose.

Plants release oxygen as a byproduct. This oxygen is essential for most 
living organisms on Earth.
    """.strip()
    
    hindi_text = """
अध्याय 3: प्रकाश संश्लेषण

प्रकाश संश्लेषण वह प्रक्रिया है जिसके द्वारा पौधे अपना भोजन बनाते हैं।
यह पौधों की कोशिकाओं के क्लोरोप्लास्ट में होता है। इस प्रक्रिया के लिए 
सूर्य का प्रकाश, पानी और कार्बन डाइऑक्साइड की आवश्यकता होती है।

प्रकाश संश्लेषण के मुख्य चरण प्रकाश-निर्भर प्रतिक्रियाएं और प्रकाश-स्वतंत्र 
प्रतिक्रियाएं हैं। ये चरण ग्लूकोज बनाने के लिए एक साथ काम करते हैं।

पौधे एक उप-उत्पाद के रूप में ऑक्सीजन छोड़ते हैं। यह ऑक्सीजन पृथ्वी पर 
अधिकांश जीवित जीवों के लिए आवश्यक है।
    """.strip()
    
    print("=" * 70)
    print("LLM-BASED SEMANTIC ALIGNMENT DEMO")
    print("=" * 70)
    print()
    
    # Show the system prompt being used
    print("📝 SYSTEM PROMPT:")
    print("-" * 70)
    print(ALIGNMENT_SYSTEM_PROMPT[:200] + "...")
    print("-" * 70)
    print()
    
    # Initialize LLM client
    print("🔧 Initializing LLM client...")
    print(f"   Base URL: {config.LLM_BASE_URL}")
    print(f"   Model: {config.LLM_MODEL}")
    print()
    
    client = OpenAI(
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY
    )
    
    # Perform alignment
    print("🚀 Performing LLM-based semantic alignment...")
    print()
    
    try:
        aligned_pairs = align_with_llm(
            english_text=english_text,
            hindi_text=hindi_text,
            llm_client=client,
            model=config.LLM_MODEL,
            temperature=0.1  # Low temperature for consistency
        )
        
        print(f"✅ Alignment successful! Found {len(aligned_pairs)} pairs")
        print()
        
        # Display results
        print("=" * 70)
        print("ALIGNED TRANSLATION PAIRS")
        print("=" * 70)
        print()
        
        for idx, (eng_chunk, hin_chunk) in enumerate(aligned_pairs, 1):
            print(f"📌 Pair {idx}:")
            print()
            print(f"   🇬🇧 English ({len(eng_chunk)} chars):")
            print(f"      {eng_chunk}")
            print()
            print(f"   🇮🇳 Hindi ({len(hin_chunk)} chars):")
            print(f"      {hin_chunk}")
            print()
            print("-" * 70)
            print()
        
        # Summary statistics
        print("=" * 70)
        print("SUMMARY STATISTICS")
        print("=" * 70)
        print(f"Total aligned pairs: {len(aligned_pairs)}")
        
        avg_eng_chars = sum(len(p[0]) for p in aligned_pairs) / len(aligned_pairs)
        avg_hin_chars = sum(len(p[1]) for p in aligned_pairs) / len(aligned_pairs)
        
        print(f"Average English chunk size: {avg_eng_chars:.1f} characters")
        print(f"Average Hindi chunk size: {avg_hin_chars:.1f} characters")
        print(f"Character ratio (EN/HI): {avg_eng_chars/avg_hin_chars:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Alignment failed: {str(e)}")
        print()
        print("Troubleshooting tips:")
        print("  1. Check your API key is valid")
        print("  2. Verify the LLM_BASE_URL is correct")
        print("  3. Ensure you have API credits/quota")
        print("  4. Try a different model if current one fails")
        return
    
    # Show how this compares to index-based alignment
    print("=" * 70)
    print("COMPARISON WITH INDEX-BASED ALIGNMENT")
    print("=" * 70)
    print()
    print("LLM Alignment:")
    print("  ✅ Semantically groups related sentences")
    print("  ✅ Handles misaligned or complex structures")
    print("  ✅ Adapts to natural translation boundaries")
    print("  ⚠️  Slower (requires API call)")
    print("  ⚠️  Costs API credits")
    print()
    print("Index Alignment:")
    print("  ✅ Very fast (no API calls)")
    print("  ✅ Deterministic and predictable")
    print("  ✅ Works well for aligned PDFs")
    print("  ⚠️  Requires strict page alignment")
    print("  ⚠️  1:1 sentence mapping only")
    print()


if __name__ == "__main__":
    main()
