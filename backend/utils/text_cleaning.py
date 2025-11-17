"""Text cleaning helpers used by the normalization service."""
from __future__ import annotations
import re
import unidecode


def normalize_whitespace(text: str) -> str:
    """
    Collapse extra whitespace and standardize line endings.
    This version preserves paragraph breaks (double newlines).
    """
    if not text:
        return ""
    
    # Standardize all line endings (e.g., \r\n) to \n
    text = text.replace('\r\n', '\n')
    
    # Replace 3 or more newlines with 2 (preserve paragraphs, remove excess)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace 2 or more spaces or tabs with a single space
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def remove_repeated_headers(text: str) -> str:
    """
    Strips duplicated noise common in scanned PDFs, such as page numbers.
    
    Note: A true header/footer removal heuristic is complex. This function
    provides a simple implementation focused on removing lines that
    only contain digits (common page number OCR artifact).
    """
    if not text:
        return ""
        
    lines = text.split('\n')
    
    # Keep lines that are NOT just digits after stripping whitespace
    cleaned_lines = [line for line in lines if not line.strip().isdigit()]
    
    return '\n'.join(cleaned_lines)


def sanitize_characters(text: str) -> str:
    """
    Remove OCR artifacts (e.g., end-of-line hyphens)
    and convert special unicode characters to ASCII equivalents.
    """
    if not text:
        return ""
        
    # 1. Remove end-of-line hyphens (e.g., "defend-\nant" -> "defendant")
    #    Looks for a hyphen, optional whitespace, a newline, and optional whitespace
    text = re.sub(r'-\s*\n\s*', '', text)
    
    # 2. Convert ligatures and accented characters to their closest ASCII equivalent
    #    E.g., "Instrucción nº 5" -> "Instruccion no 5"
    text = unidecode.unidecode(text)
    
    return text