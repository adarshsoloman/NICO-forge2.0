"""
LLM Verification Module

Optional LLM-based verification and refinement of Hindi translations.
Supports any OpenAI-compatible API provider.
"""

import requests
import time
import config


def llm_map(eng_chunk: str, hin_chunk_raw: str) -> tuple[str, str]:
    """
    Verify and optionally correct Hindi translation using LLM.
    
    Args:
        eng_chunk: English text chunk
        hin_chunk_raw: Raw extracted Hindi chunk
    
    Returns:
        Tuple of (hin_chunk_verified, llm_flags)
        - hin_chunk_verified: Verified/corrected Hindi text
        - llm_flags: Optional flags like "[UNCERTAIN]"
    """
    # If LLM verification is disabled, return raw chunk unchanged
    if not config.USE_LLM_VERIFICATION:
        return (hin_chunk_raw, "")
    
    # Check if API key is configured
    if not config.LLM_API_KEY:
        return (hin_chunk_raw, "[NO_API_KEY]")
    
    # Call LLM API with retry logic
    try:
        verified_text, flags = call_llm_api(eng_chunk, hin_chunk_raw)
        return (verified_text, flags)
    except Exception as e:
        # On error, return raw chunk with error flag
        return (hin_chunk_raw, f"[LLM_ERROR: {str(e)}]")


def call_llm_api(eng_chunk: str, hin_chunk_raw: str) -> tuple[str, str]:
    """
    Make API call to LLM provider with retry logic.
    
    Args:
        eng_chunk: English text
        hin_chunk_raw: Raw Hindi text
    
    Returns:
        Tuple of (verified_hindi, flags)
    
    Raises:
        Exception: If all retries fail
    """
    # Construct verification prompt
    prompt = create_verification_prompt(eng_chunk, hin_chunk_raw)
    
    # Prepare API request
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a bilingual Hindi-English translator. Verify and correct Hindi translations for accuracy."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": config.LLM_TEMPERATURE,
    }
    
    # Retry loop
    last_error = None
    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            response = requests.post(
                f"{config.LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                verified_text = data['choices'][0]['message']['content'].strip()
                
                # Extract flags if present
                flags = extract_flags(verified_text)
                
                # Remove flags from verified text
                verified_text = remove_flags(verified_text)
                
                return (verified_text, flags)
            
            # Handle rate limiting (429) with retry
            elif response.status_code == 429:
                if attempt < config.LLM_MAX_RETRIES - 1:
                    time.sleep(config.LLM_RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    raise Exception(f"Rate limit exceeded after {config.LLM_MAX_RETRIES} retries")
            
            # Other errors
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(config.LLM_RETRY_DELAY)
            else:
                raise Exception(f"Request failed after {config.LLM_MAX_RETRIES} retries: {str(last_error)}")
    
    raise Exception(f"LLM API call failed: {str(last_error)}")


def create_verification_prompt(eng_chunk: str, hin_chunk_raw: str) -> str:
    """
    Create verification prompt for LLM.
    
    Optimized for translation models like MADLAD-400.
    
    Args:
        eng_chunk: English text
        hin_chunk_raw: Raw Hindi text
    
    Returns:
        Formatted prompt string
    """
    # Handle empty Hindi chunks
    if not hin_chunk_raw or hin_chunk_raw.strip() == "":
        prompt = f"""Translate the following English text to Hindi. Provide accurate, natural-sounding Hindi translation.

Source (English): {eng_chunk}

Target (Hindi):"""
    else:
        prompt = f"""You are a professional English-Hindi translator. Review and improve the Hindi translation below.

Task: Compare the English source with the Hindi translation. If the Hindi is accurate, return it as-is. If there are errors, provide the corrected version.

Source (English):
{eng_chunk}

Current Hindi Translation:
{hin_chunk_raw}

Instructions:
- Return ONLY the final Hindi text (no explanations)
- Preserve technical terms and proper nouns appropriately
- Ensure grammatical correctness in Hindi
- Maintain the same meaning and tone as the English
- If the translation is already perfect, return it unchanged
- If uncertain about correctness, add [UNCERTAIN] at the end

Verified Hindi:"""
    
    return prompt


def extract_flags(text: str) -> str:
    """
    Extract flags like [UNCERTAIN] from verified text.
    
    Args:
        text: Verified text possibly containing flags
    
    Returns:
        Extracted flags as string, empty if none found
    """
    flags = []
    
    if '[UNCERTAIN]' in text:
        flags.append('[UNCERTAIN]')
    
    return ', '.join(flags) if flags else ""


def remove_flags(text: str) -> str:
    """
    Remove flags from verified text.
    
    Args:
        text: Text possibly containing flags
    
    Returns:
        Text with flags removed
    """
    # Remove common flags
    text = text.replace('[UNCERTAIN]', '').strip()
    
    return text
