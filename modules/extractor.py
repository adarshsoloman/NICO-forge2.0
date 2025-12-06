"""
PDF Text Extraction Module

Extracts text from PDF pages using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
import re


def extract_page_text(pdf_path: str, page_num: int) -> str:
    """
    Extract text from a specific page of a PDF file.
    
    Args:
        pdf_path: Absolute path to the PDF file
        page_num: Page number (0-indexed)
    
    Returns:
        Extracted and normalized text from the page
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        IndexError: If page number is out of range
    """
    try:
        # Open the PDF document
        doc = fitz.open(pdf_path)
        
        # Check if page number is valid
        if page_num < 0 or page_num >= len(doc):
            doc.close()
            raise IndexError(f"Page {page_num} out of range for PDF with {len(doc)} pages")
        
        # Extract text from the specified page
        page = doc[page_num]
        text = page.get_text()
        
        # Close the document
        doc.close()
        
        # Normalize whitespace
        text = normalize_whitespace(text)
        
        return text
    
    except Exception as e:
        raise Exception(f"Error extracting text from {pdf_path}, page {page_num}: {str(e)}")


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in extracted text.
    
    - Collapses multiple spaces into one
    - Collapses multiple newlines into one
    - Strips leading/trailing whitespace
    
    Args:
        text: Raw extracted text
    
    Returns:
        Normalized text
    """
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Collapse multiple newlines (keep single newlines)
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def get_page_count(pdf_path: str) -> int:
    """
    Get the total number of pages in a PDF.
    
    Args:
        pdf_path: Absolute path to the PDF file
    
    Returns:
        Total page count
    """
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    doc.close()
    return page_count
