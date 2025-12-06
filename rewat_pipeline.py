"""
Rewat-Forge: Bilingual PDF-to-CSV Dataset Extraction Pipeline

Main orchestrator script that coordinates all modules and manages parallel processing.

Usage:
    python rewat_pipeline.py <english_pdf_path> <hindi_pdf_path>
    
Example:
    python rewat_pipeline.py ncert_eng.pdf ncert_hin.pdf
"""

import sys
import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Import configuration
import config

# Import all modules
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
    create_row,
    append_json_line,
    clean_chunk,
    is_chunk_valid,
    is_valid_chunk_pair,
    calculate_quality_score,
    get_quality_label,
    initialize_json_array,
    finalize_json_array
)


def setup_logging():
    """Configure logging for the pipeline."""
    if config.LOG_ERRORS:
        logging.basicConfig(
            filename=config.ERROR_LOG,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )


def process_page(page_num: int, eng_pdf: str, hin_pdf: str, doc_id: str, csv_lock: threading.Lock) -> dict:
    """
    Process a single page from both PDFs with quality filtering and text cleaning.
    
    This function runs in a thread pool worker.
    
    Args:
        page_num: Page number (0-indexed for processing)
        eng_pdf: Path to English PDF
        hin_pdf: Path to Hindi PDF
        doc_id: Document identifier
        csv_lock: Threading lock for CSV writes
    
    Returns:
        Dictionary with processing statistics including quality metrics
    """
    try:
        # 1. Extract text from both PDFs
        eng_text = extract_page_text(eng_pdf, page_num)
        hin_text = extract_page_text(hin_pdf, page_num)
        
        # 2. Split into sentences
        eng_sentences = split_sentences(eng_text, language='english')
        hin_sentences = split_sentences(hin_text, language='hindi')
        
        # 3. Create chunks
        eng_chunks = create_chunks(eng_sentences)
        hin_chunks = create_chunks(hin_sentences)
        
        # 4. Align chunks by index
        aligned_pairs = align_chunks(eng_chunks, hin_chunks)
        
        # 5. Process each chunk pair with quality filtering
        chunks_processed = 0
        chunks_rejected = 0
        quality_scores = []
        
        for chunk_id, (eng_chunk_raw, hin_chunk_raw) in enumerate(aligned_pairs):
            # Clean text chunks
            eng_chunk = clean_chunk(eng_chunk_raw, language='english')
            hin_chunk = clean_chunk(hin_chunk_raw, language='hindi')
            
            # Validate individual chunks
            if not is_chunk_valid(eng_chunk, language='english'):
                chunks_rejected += 1
                continue
            
            if not is_chunk_valid(hin_chunk, language='hindi'):
                chunks_rejected += 1
                continue
            
            # Validate chunk pair
            is_valid, reason = is_valid_chunk_pair(eng_chunk, hin_chunk)
            if not is_valid:
                chunks_rejected += 1
                # Optionally log rejected chunks
                if config.LOG_ERRORS:
                    logging.warning(f"Page {page_num + 1}, Chunk {chunk_id} rejected: {reason}")
                continue
            
            # Optional LLM verification (on cleaned text)
            hin_chunk_verified, llm_flags = llm_map(eng_chunk, hin_chunk)
            
            # Calculate quality score
            final_hin = hin_chunk_verified if hin_chunk_verified else hin_chunk
            quality_score = calculate_quality_score(eng_chunk, final_hin)
            quality_label = get_quality_label(quality_score)
            quality_scores.append(quality_score)
            
            # Regex extraction (on verified if available, otherwise cleaned)
            text_for_regex = hin_chunk_verified if config.REGEX_ON_VERIFIED and hin_chunk_verified else hin_chunk
            regex_matches = extract_patterns(text_for_regex)
            
            # Prepare row data
            row = create_row(
                doc_id=doc_id,
                page=page_num + 1,  # Convert to 1-indexed for user display
                chunk_id=chunk_id,
                eng_chunk=eng_chunk,
                hin_chunk_raw=hin_chunk,  # Now cleaned
                hin_chunk_verified=hin_chunk_verified if hin_chunk_verified else hin_chunk,
                alignment_method='index',
                regex_matches=regex_matches,
                llm_flags=llm_flags,
                quality_score=quality_score,
                quality_label=quality_label
            )
            
            # Write to CSV
            append_row(row, config.OUTPUT_CSV, csv_lock)
            
            # Write to JSON if enabled
            if config.OUTPUT_JSON_ENABLED:
                if config.JSON_FORMAT == "lines":
                    append_json_line(row, config.OUTPUT_JSON, csv_lock)
                # Note: JSON array format requires tracking first item, handled in main()
            
            chunks_processed += 1
        
        # Calculate average quality for this page
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'page': page_num,
            'status': 'success',
            'chunks': chunks_processed,
            'rejected': chunks_rejected,
            'avg_quality': round(avg_quality, 3),
            'error': None
        }
    
    except Exception as e:
        # Log error and return failure status
        error_msg = f"Page {page_num + 1}: {str(e)}"
        if config.LOG_ERRORS:
            logging.error(error_msg)
        
        return {
            'page': page_num,
            'status': 'failed',
            'chunks': 0,
            'rejected': 0,
            'avg_quality': 0.0,
            'error': error_msg
        }


def find_matching_pdfs(eng_path: str, hin_path: str) -> list:
    """
    Find matching PDF pairs from English and Hindi folders/files.
    
    Args:
        eng_path: Path to English PDF file or folder
        hin_path: Path to Hindi PDF file or folder
    
    Returns:
        List of tuples: [(eng_pdf, hin_pdf, doc_id), ...]
    """
    # Case 1: Both are files
    if os.path.isfile(eng_path) and os.path.isfile(hin_path):
        if not eng_path.lower().endswith('.pdf'):
            print(f"Error: English file is not a PDF: {eng_path}")
            sys.exit(1)
        if not hin_path.lower().endswith('.pdf'):
            print(f"Error: Hindi file is not a PDF: {hin_path}")
            sys.exit(1)
        doc_id = Path(eng_path).stem
        return [(eng_path, hin_path, doc_id)]
    
    # Case 2: Both are folders
    if os.path.isdir(eng_path) and os.path.isdir(hin_path):
        # Get all PDFs from both folders
        eng_pdfs = {f.name: str(f) for f in Path(eng_path).glob('*.pdf')}
        hin_pdfs = {f.name: str(f) for f in Path(hin_path).glob('*.pdf')}
        
        if not eng_pdfs:
            print(f"Error: No PDF files found in English folder: {eng_path}")
            sys.exit(1)
        
        if not hin_pdfs:
            print(f"Error: No PDF files found in Hindi folder: {hin_path}")
            sys.exit(1)
        
        # Find matching PDFs by filename
        matching_names = set(eng_pdfs.keys()) & set(hin_pdfs.keys())
        
        if not matching_names:
            print(f"\n❌ Error: No matching PDF pairs found!")
            print(f"\nEnglish PDFs ({len(eng_pdfs)}):")
            for name in sorted(eng_pdfs.keys()):
                print(f"  - {name}")
            print(f"\nHindi PDFs ({len(hin_pdfs)}):")
            for name in sorted(hin_pdfs.keys()):
                print(f"  - {name}")
            print(f"\n💡 Tip: Ensure PDF files have identical names in both folders.")
            sys.exit(1)
        
        # Create pairs
        pairs = []
        for name in sorted(matching_names):
            doc_id = Path(name).stem
            pairs.append((eng_pdfs[name], hin_pdfs[name], doc_id))
        
        return pairs
    
    # Case 3: Mixed file and folder
    print(f"Error: Both inputs must be either files or folders.")
    print(f"  English: {'file' if os.path.isfile(eng_path) else 'folder'}")
    print(f"  Hindi:   {'file' if os.path.isfile(hin_path) else 'folder'}")
    sys.exit(1)


def process_pdf_pair(eng_pdf: str, hin_pdf: str, doc_id: str):
    """
    Process a single PDF pair through the entire pipeline.
    
    Args:
        eng_pdf: Path to English PDF
        hin_pdf: Path to Hindi PDF
        doc_id: Document identifier
    """
    print("\n" + "=" * 70)
    print(f"Processing: {doc_id}")
    print("=" * 70)
    print(f"  English PDF:     {Path(eng_pdf).name}")
    print(f"  Hindi PDF:       {Path(hin_pdf).name}")
    
    # Get page counts
    try:
        eng_page_count = get_page_count(eng_pdf)
        hin_page_count = get_page_count(hin_pdf)
        
        print(f"\nPDF Analysis:")
        print(f"  English pages: {eng_page_count}")
        print(f"  Hindi pages:   {hin_page_count}")
        
        # Warn if page counts don't match
        if eng_page_count != hin_page_count:
            print(f"\n⚠️  WARNING: Page count mismatch!")
            print(f"  Processing will continue with min({eng_page_count}, {hin_page_count}) pages.")
        
        # Process minimum page count to avoid errors
        total_pages = min(eng_page_count, hin_page_count)
        
    except Exception as e:
        print(f"❌ Error analyzing PDFs: {e}")
        return {'doc_id': doc_id, 'status': 'failed', 'error': str(e)}
    
    # Process pages in parallel
    print(f"\n🚀 Processing {total_pages} pages with {config.WORKER_THREADS} workers...")
    
    csv_lock = threading.Lock()
    results = []
    
    with ThreadPoolExecutor(max_workers=config.WORKER_THREADS) as executor:
        # Submit all pages
        futures = {
            executor.submit(process_page, page_num, eng_pdf, hin_pdf, doc_id, csv_lock): page_num
            for page_num in range(total_pages)
        }
        
        # Track progress
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            # Progress update with quality info
            if result['status'] == 'success':
                quality_str = f"Q:{result.get('avg_quality', 0):.2f}" if result.get('avg_quality') else ""
                rejected_str = f" (-{result.get('rejected', 0)})" if result.get('rejected', 0) > 0 else ""
                print(f"  ✓ Page {result['page'] + 1}/{total_pages} - {result['chunks']} chunks{rejected_str} {quality_str} [{completed}/{total_pages}]")
            else:
                print(f"  ✗ Page {result['page'] + 1}/{total_pages} - FAILED: {result['error']}")
    
    # Statistics for this PDF
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    total_chunks = sum(r.get('chunks', 0) for r in results)
    total_rejected = sum(r.get('rejected', 0) for r in results)
    avg_quality = sum(r.get('avg_quality', 0) * r.get('chunks', 0) for r in results if r['status'] == 'success')
    avg_quality = avg_quality / total_chunks if total_chunks > 0 else 0.0
    
    print(f"\n✓ Completed: {doc_id}")
    print(f"  Pages: {successful}/{total_pages} successful, {failed} failed")
    print(f"  Total chunks: {total_chunks} (rejected: {total_rejected})")
    print(f"  Avg quality: {avg_quality:.3f}")
    
    return {
        'doc_id': doc_id,
        'status': 'success' if failed == 0 else 'partial',
        'total_pages': total_pages,
        'successful': successful,
        'failed': failed,
        'total_chunks': total_chunks
    }


def main():
    """Main pipeline entry point."""
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python rewat_pipeline.py <english_input> <hindi_input>")
        print("\nInputs can be either:")
        print("  1. PDF files:  python rewat_pipeline.py eng.pdf hin.pdf")
        print("  2. Folders:    python rewat_pipeline.py english_folder/ hindi_folder/")
        print("\nFor folders: PDFs must have identical names in both folders")
        print("Example: english_folder/chapter1.pdf ↔ hindi_folder/chapter1.pdf")
        sys.exit(1)
    
    eng_input = sys.argv[1]
    hin_input = sys.argv[2]
    
    # Validate inputs exist
    if not os.path.exists(eng_input):
        print(f"Error: English input not found: {eng_input}")
        sys.exit(1)
    
    if not os.path.exists(hin_input):
        print(f"Error: Hindi input not found: {hin_input}")
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Find matching PDF pairs
    pdf_pairs = find_matching_pdfs(eng_input, hin_input)
    
    print("=" * 70)
    print("REWAT-FORGE: Bilingual PDF-to-CSV Extraction Pipeline")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Chunk Size:       {config.CHUNK_SIZE} sentences")
    print(f"  Worker Threads:   {config.WORKER_THREADS}")
    print(f"  LLM Verification: {'Enabled' if config.USE_LLM_VERIFICATION else 'Disabled'}")
    if config.USE_LLM_VERIFICATION:
        print(f"  LLM Provider:     {config.LLM_BASE_URL}")
        print(f"  LLM Model:        {config.LLM_MODEL}")
    
    print(f"\nFound {len(pdf_pairs)} PDF pair(s) to process:")
    for eng_pdf, hin_pdf, doc_id in pdf_pairs:
        print(f"  📄 {doc_id}")
    
    # Initialize output files
    csv_lock = threading.Lock()
    initialize_csv(config.OUTPUT_CSV, csv_lock)
    print(f"\n✓ Initialized output CSV: {config.OUTPUT_CSV}")
    
    # Initialize JSON if enabled
    if config.OUTPUT_JSON_ENABLED:
        if config.JSON_FORMAT == "array":
            initialize_json_array(config.OUTPUT_JSON, csv_lock)
        print(f"✓ Initialized output JSON: {config.OUTPUT_JSON} (format: {config.JSON_FORMAT})")
    
    # Process each PDF pair
    all_results = []
    for eng_pdf, hin_pdf, doc_id in pdf_pairs:
        result = process_pdf_pair(eng_pdf, hin_pdf, doc_id)
        all_results.append(result)
    
    # Finalize JSON array if needed
    if config.OUTPUT_JSON_ENABLED and config.JSON_FORMAT == "array":
        finalize_json_array(config.OUTPUT_JSON, csv_lock)
    
    # Overall summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    
    total_pdfs = len(all_results)
    total_chunks = sum(r.get('total_chunks', 0) for r in all_results)
    total_pages_processed = sum(r.get('successful', 0) for r in all_results)
    total_pages_failed = sum(r.get('failed', 0) for r in all_results)
    
    print(f"\nOverall Results:")
    print(f"  Total PDF pairs:  {total_pdfs}")
    print(f"  Total chunks:     {total_chunks}")
    print(f"  Pages processed:  {total_pages_processed}")
    print(f"  Pages failed:     {total_pages_failed}")
    
    print(f"\nOutput:")
    print(f"  CSV file:         {config.OUTPUT_CSV}")
    if config.OUTPUT_JSON_ENABLED:
        print(f"  JSON file:        {config.OUTPUT_JSON}")
    if config.LOG_ERRORS and total_pages_failed > 0:
        print(f"  Error log:        {config.ERROR_LOG}")
    
    print("\n✨ All PDFs processed successfully!\n")


if __name__ == '__main__':
    main()
