"""
LLM Deep Cleaning - Phase 2
============================
Targets the 28 problematic entries identified in quality assessment.
Focuses on: removing repeated phrases, fixing duplicates, ensuring quality.

Usage:
    python3 llm_deep_clean_phase2.py
"""

import json
import time
from openai import OpenAI
import config

# Initialize LLM client
client = OpenAI(
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL
)

# Problematic entries identified in quality assessment
PROBLEMATIC_ENTRIES = [1, 3, 4, 5, 6, 8, 10, 13, 14, 15, 16, 18, 19, 20, 22, 24, 
                       36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]

# STRICTER System prompt for Phase 2
SYSTEM_PROMPT = """You are an expert data quality specialist for bilingual datasets.

Your task: Clean English-Hindi translation pairs by removing ALL repeated/duplicate content.

CRITICAL RULES:
1. REMOVE ALL DUPLICATES:
   - Remove repeated sentences (even if slightly reworded)
   - Remove repeated phrases within the same text
   - Keep only ONE instance of any duplicated content
   
2. PRESERVE MEANING:
   - Do NOT translate or change the content
   - Do NOT add new information
   - ONLY remove duplicates and clean formatting

3. LENGTH BALANCE:
   - If English and Hindi have very different lengths, check for hidden duplicates
   - The final texts should be roughly similar in length (within 1.5x ratio)

4. OUTPUT FORMAT:
   Return ONLY a JSON object with this exact structure (no markdown, no explanation):
   {
     "english": "cleaned text without any duplicates",
     "hindi": "cleaned text without any duplicates"
   }

EXAMPLE OF DUPLICATION TO REMOVE:
Input: "The Government launched program. The Government has also launched initiative. Government launched..."
Output: "The Government launched program and initiative."

Now clean the provided text pair."""


def deep_clean_with_llm(english_text, hindi_text, entry_num):
    """
    Deep clean with LLM focusing on duplicate removal.
    """
    user_prompt = f"""Remove ALL duplicate/repeated content from this pair:

ENGLISH:
{english_text}

HINDI:
{hindi_text}

Return cleaned JSON with no duplicates."""

    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,  # Zero temperature for consistency
            max_tokens=6000
        )
        
        llm_output = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if llm_output.startswith('```'):
            llm_output = llm_output.split('```')[1]
            if llm_output.startswith('json'):
                llm_output = llm_output[4:]
            llm_output = llm_output.strip()
        
        result = json.loads(llm_output)
        
        return {
            'english': result.get('english', english_text),
            'hindi': result.get('hindi', hindi_text),
            'deep_cleaned': True,
            'error': None
        }
        
    except json.JSONDecodeError as e:
        print(f"  ⚠ Warning: Entry {entry_num} - JSON parse error")
        return {
            'english': english_text,
            'hindi': hindi_text,
            'deep_cleaned': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"  ⚠ Warning: Entry {entry_num} - LLM error: {str(e)}")
        return {
            'english': english_text,
            'hindi': hindi_text,
            'deep_cleaned': False,
            'error': str(e)
        }


def process_phase2():
    """
    Phase 2: Deep clean the 28 problematic entries.
    """
    print("=" * 70)
    print("LLM Deep Cleaning - Phase 2")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Model:              {config.LLM_MODEL}")
    print(f"  Problematic entries: {len(PROBLEMATIC_ENTRIES)}")
    print(f"  Input:              pib_bilingual_final.jsonl")
    print(f"  Output:             pib_bilingual_ultra_clean.jsonl\n")
    
    # Load all entries
    all_entries = []
    with open('pib_bilingual_final.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            all_entries.append(json.loads(line))
    
    print(f"Loaded {len(all_entries)} total entries")
    print(f"Will deep-clean {len(PROBLEMATIC_ENTRIES)} problematic entries\n")
    
    start_time = time.time()
    processed = 0
    failed = 0
    
    # Process each entry
    output_entries = []
    for i, entry in enumerate(all_entries, 1):
        if i in PROBLEMATIC_ENTRIES:
            print(f"Deep cleaning entry {i}/{len(all_entries)} (problematic)...")
            result = deep_clean_with_llm(entry['english'], entry['hindi'], i)
            
            if result['deep_cleaned']:
                processed += 1
                print(f"  ✓ Deep cleaned successfully")
            else:
                failed += 1
                print(f"  ✗ Kept original (cleaning failed)")
            
            output_entries.append({
                'english': result['english'],
                'hindi': result['hindi']
            })
            
            # Rate limiting
            time.sleep(0.5)
        else:
            # Keep good entries as-is
            output_entries.append({
                'english': entry['english'],
                'hindi': entry['hindi']
            })
            print(f"Keeping entry {i}/{len(all_entries)} (already good quality)")
    
    # Write output
    with open('pib_bilingual_ultra_clean.jsonl', 'w', encoding='utf-8') as f:
        for entry in output_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  Total entries:          {len(all_entries)}")
    print(f"  Deep cleaned:           {processed}")
    print(f"  Failed/kept original:   {failed}")
    print(f"  Kept as-is (good):      {len(all_entries) - len(PROBLEMATIC_ENTRIES)}")
    print(f"  Processing time:        {elapsed_time:.1f} seconds")
    print(f"\nOutput: pib_bilingual_ultra_clean.jsonl")
    print("\n✨ Phase 2 deep cleaning complete!")
    print("   Expected quality: 80-90% production-ready")
    print("=" * 70)
    print("")


if __name__ == '__main__':
    process_phase2()
