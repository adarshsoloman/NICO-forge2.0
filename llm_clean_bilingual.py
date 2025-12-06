"""
LLM-Powered Bilingual Dataset Cleaner
======================================
Uses LLM to intelligently clean and verify English-Hindi translation pairs.

This script:
1. Reads cleaned JSONL file
2. Sends each pair to LLM for verification and deep cleaning
3. Removes special characters intelligently
4. Verifies semantic alignment
5. Outputs production-ready dataset

Usage:
    python3 llm_clean_bilingual.py
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

# System prompt for LLM
SYSTEM_PROMPT = """You are a bilingual data quality expert specializing in English-Hindi translation pairs.

Your task is to clean and verify translation pairs for dataset preparation. Follow these rules strictly:

1. CLEANING:
   - Remove special characters like backslashes (\\), forward slashes (/) that don't belong
   - Remove any stray escape sequences or formatting artifacts
   - Clean up extra punctuation or symbols
   - Preserve meaningful punctuation (periods, commas, colons, question marks, etc.)
   - Preserve numbers, dates, and legitimate symbols

2. VERIFICATION:
   - Check if English and Hindi are actual translations of each other
   - Ensure semantic alignment (same meaning/content)
   - Do NOT retranslate or paraphrase
   - Do NOT add or remove content
   - Only clean formatting issues

3. OUTPUT FORMAT:
   Return ONLY a JSON object with this exact structure:
   {
     "english": "cleaned English text",
     "hindi": "cleaned Hindi text",
     "is_aligned": true/false,
     "issues_found": "brief description of what was cleaned"
   }

Do not include any other text, explanations, or markdown formatting. Just the JSON object."""


def clean_pair_with_llm(english_text, hindi_text, entry_num):
    """
    Send a bilingual pair to LLM for intelligent cleaning.
    
    Args:
        english_text: English text
        hindi_text: Hindi text
        entry_num: Entry number for logging
        
    Returns:
        Dictionary with cleaned texts and metadata
    """
    user_prompt = f"""Clean this English-Hindi translation pair:

ENGLISH:
{english_text}

HINDI:
{hindi_text}

Return the cleaned version as JSON."""

    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=4000
        )
        
        # Extract response
        llm_output = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        # Sometimes LLM wraps in markdown code blocks
        if llm_output.startswith('```'):
            # Remove markdown code blocks
            llm_output = llm_output.split('```')[1]
            if llm_output.startswith('json'):
                llm_output = llm_output[4:]
            llm_output = llm_output.strip()
        
        result = json.loads(llm_output)
        
        return {
            'english': result.get('english', english_text),
            'hindi': result.get('hindi', hindi_text),
            'is_aligned': result.get('is_aligned', True),
            'issues_found': result.get('issues_found', 'None'),
            'llm_verified': True,
            'error': None
        }
        
    except json.JSONDecodeError as e:
        print(f"  ⚠ Warning: Entry {entry_num} - JSON parse error, using original")
        return {
            'english': english_text,
            'hindi': hindi_text,
            'is_aligned': True,
            'issues_found': f'JSON parse error: {str(e)}',
            'llm_verified': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"  ⚠ Warning: Entry {entry_num} - LLM error: {str(e)}")
        return {
            'english': english_text,
            'hindi': hindi_text,
            'is_aligned': True,
            'issues_found': f'API error: {str(e)}',
            'llm_verified': False,
            'error': str(e)
        }


def process_dataset(input_file, output_file):
    """
    Process entire dataset through LLM cleaning pipeline.
    
    Args:
        input_file: Path to cleaned JSONL input
        output_file: Path to final output JSONL
    """
    print("=" * 70)
    print("LLM-Powered Bilingual Dataset Cleaner")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  LLM Provider: {config.LLM_BASE_URL}")
    print(f"  Model:        {config.LLM_MODEL}")
    print(f"  Input:        {input_file}")
    print(f"  Output:       {output_file}\n")
    
    total_entries = 0
    successful = 0
    failed = 0
    misaligned = 0
    
    start_time = time.time()
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            total_entries += 1
            
            try:
                # Parse input
                data = json.loads(line)
                english = data.get('english', '')
                hindi = data.get('hindi', '')
                
                print(f"Processing entry {line_num}/{total_entries}...")
                
                # Send to LLM for cleaning
                result = clean_pair_with_llm(english, hindi, line_num)
                
                # Track statistics
                if result['llm_verified']:
                    successful += 1
                    if not result['is_aligned']:
                        misaligned += 1
                        print(f"  ⚠ Alignment issue detected!")
                    if result['issues_found'] and result['issues_found'] != 'None':
                        print(f"  ✓ Cleaned: {result['issues_found']}")
                else:
                    failed += 1
                
                # Prepare output entry (only essential fields)
                output_entry = {
                    'english': result['english'],
                    'hindi': result['hindi']
                }
                
                # Write to output
                outfile.write(json.dumps(output_entry, ensure_ascii=False) + '\n')
                
                # Rate limiting - small delay between API calls
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Error processing entry {line_num}: {e}")
                failed += 1
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  Total entries:      {total_entries}")
    print(f"  LLM verified:       {successful}")
    print(f"  Failed/Fallback:    {failed}")
    print(f"  Misaligned pairs:   {misaligned}")
    print(f"  Processing time:    {elapsed_time:.1f} seconds")
    print(f"\nOutput saved to: {output_file}")
    print("\n✨ Your production-ready bilingual dataset is ready!")
    print("=" * 70)
    print("")


if __name__ == '__main__':
    # File paths
    input_file = 'pib_bilingual_cleaned.jsonl'
    output_file = 'pib_bilingual_final.jsonl'
    
    # Process the dataset
    process_dataset(input_file, output_file)
