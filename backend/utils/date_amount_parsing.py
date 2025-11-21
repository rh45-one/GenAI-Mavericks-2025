"""Parsing helpers for dates, deadlines, and monetary amounts."""
from __future__ import annotations

import re
from typing import List

# --- Pre-compiled Regex Definitions ---

# Regex for numeric dates: 10/05/2024, 10-05-2024, 10.05.2024
DATE_REGEX_NUMERIC = re.compile(r'(\b\d{2}[/.-]\d{2}[/.-]\d{4})\b')

# Regex for Spanish month names (as requested in TODO)
# E.g., "10 de mayo de 2024"
SPANISH_MONTHS = r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
DATE_REGEX_SPANISH = re.compile(
    rf'(\b\d{{1,2}}\s+de\s+{SPANISH_MONTHS}\s+de\s+\d{{4}}\b)',
    re.IGNORECASE
)

# Regex for deadline expressions (strict): detect explicit phrases mentioning a
# plazo / recurso context plus a days number, e.g. "en el plazo de 20 días",
# "para recurrir: 20 días", "plazo de 10 días hábiles".
DEADLINE_REGEX = re.compile(
    r"(\b(?:dentro de|en el plazo de|plazo de|para recurrir|para interponer (?:el )?recurso|recurso de apelaci[oó]n)\s*(?:de\s*)?\d+\s+d[íi]as(?:\s+h[áa]biles)?\b)",
    re.IGNORECASE,
)

# Regex for COP amounts (as requested in TODO)
# Handles variations: $5.000, $ 5.000.000, 5.000 COP, 5.000 pesos
AMOUNT_REGEX_COP = re.compile(
    r'((?:\$?\s*)[\d.,]+\s?(?:COP|pesos)\b)',
    re.IGNORECASE
)

# --- Function Implementations ---

def extract_dates(text: str) -> List[str]:
    """Return normalized date strings found in the text."""
    if not text:
        return []
    
    numeric_dates = DATE_REGEX_NUMERIC.findall(text)
    spanish_dates = DATE_REGEX_SPANISH.findall(text)
    
    # Combine lists of found dates
    return numeric_dates + spanish_dates


def extract_deadlines(text: str) -> List[str]:
    """Detect deadline expressions like 'dentro de 5 días'."""
    # This implementation detects common phrases as per the TODO.
    # Converting them to structured durations is a more complex task.
    if not text:
        return []
    
    return DEADLINE_REGEX.findall(text)


def extract_amounts(text: str) -> List[str]:
    """Pull currency or numeric obligations from the document."""
    # Handles COP amounts with punctuation variations as per the TODO.
    if not text:
        return []
        
    return AMOUNT_REGEX_COP.findall(text)
