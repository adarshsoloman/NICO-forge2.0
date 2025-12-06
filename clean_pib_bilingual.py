"""
PIB Bilingual JSONL Cleaner
============================
Processes the pib_bilingual.jsonl file to:
1. Remove excessive newline characters (\n)
2. Clean up fragmented text and whitespace
3. Properly align English-Hindi pairs
4. Output clean dataset ready for use

Usage:
    python3 clean_pib_bilingual.py
"""

import json
import re

def clean_text(text):
    """
    Clean text by removing special characters and excessive whitespace.
    
    Args:
        text: Input text string
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Replace newlines with spaces
    text = text.replace('\\n', ' ')
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def process_jsonl_file(input_file, output_file):
    """
    Process the JSONL file and create cleaned output.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output cleaned JSONL file
    """
    processed_count = 0
    total_entries = 0
    
    print("=" * 70)
    print("PIB Bilingual JSONL Cleaner")
    print("=" * 70)
    print(f"\nInput file:  {input_file}")
    print(f"Output file: {output_file}\n")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            total_entries += 1
            
            try:
                # Parse JSON line
                data =json.loads(line)
                
                # Extract and clean English and Hindi text
                english_text = data.get('english', '')
                hindi_text = data.get('hindi', '')
                
                # Clean both texts
                cleaned_english = clean_text(english_text)
                cleaned_hindi = clean_text(hindi_text)
                
                # Create cleaned entry
                cleaned_entry = {
                    'english': cleaned_english,
                    'hindi': cleaned_hindi
                }
                
                # Write to output file
                outfile.write(json.dumps(cleaned_entry, ensure_ascii=False) + '\n')
                
                processed_count += 1
                
                # Show progress every 10 lines
                if line_num % 10 == 0:
                    print(f"Processed: {line_num} entries...")
                    
            except json.JSONDecodeError as e:
                print(f"⚠ Warning: Skipping line {line_num} due to JSON error: {e}")
            except Exception as e:
                print(f"⚠ Warning: Error processing line {line_num}: {e}")
    
    print(f"\n✓ Processing complete!")
    print(f"  Total entries: {total_entries}")
    print(f"  Successfully processed: {processed_count}")
    print(f"  Output saved to: {output_file}\n")
    
    # Show sample of cleaned data
    print("=" * 70)
    print("Sample cleaned entry (first entry):")
    print("=" * 70)
    
    with open(output_file, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        sample = json.loads(first_line)
        
        print(f"\nEnglish (first 200 chars):")
        print(f"{sample['english'][:200]}...")
        print(f"\nHindi (first 200 chars):")
        print(f"{sample['hindi'][:200]}...")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    # Input and output file paths
    input_file = 'pib_bilingual.jsonl'
    output_file = 'pib_bilingual_cleaned.jsonl'
    
    # Process the file
    process_jsonl_file(input_file, output_file)
    
    print("🎉 Done! Your cleaned bilingual dataset is ready to use!")
    print("")
