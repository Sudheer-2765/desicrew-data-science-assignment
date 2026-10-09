"""Deterministic field format validators and regex checks for insurance and ID documents."""

import re
from datetime import datetime
from typing import Tuple, Optional


def clean_str(val: Optional[str]) -> str:
    """Normalize string by removing extraneous whitespace."""
    if val is None:
        return ""
    return str(val).strip()


def validate_aadhaar(val: str) -> Tuple[bool, Optional[str]]:
    """Validate 12-digit Indian Aadhaar number format."""
    digits = re.sub(r"[\s\-]", "", clean_str(val))
    if not digits.isdigit():
        return False, "Aadhaar must contain only digits"
    if len(digits) != 12:
        return False, f"Aadhaar must be 12 digits (found {len(digits)})"
    return True, None


def validate_pan(val: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian PAN format (5 letters + 4 digits + 1 letter)."""
    clean_val = clean_str(val).upper().replace(" ", "")
    if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean_val):
        return True, None
    return False, f"Value '{clean_val}' does not match standard PAN format (AAAAA9999A)"


def validate_dl(val: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian Driving Licence format."""
    clean_val = clean_str(val).upper()
    # E.g. MH12 2021 0001234 or MH1220210001234
    normalized = re.sub(r"[\s\-]", "", clean_val)
    if len(normalized) >= 13 and normalized[:2].isalpha() and normalized[2:].isalnum():
        return True, None
    return False, f"Value '{clean_val}' does not match standard DL format"


def validate_passport(val: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian Passport number format (1 letter + 7 digits)."""
    clean_val = clean_str(val).upper().replace(" ", "")
    if re.match(r"^[A-Z][0-9]{7}$", clean_val):
        return True, None
    return False, f"Value '{clean_val}' does not match standard passport format (1 letter + 7 digits)"


def validate_mrz_line2(val: str) -> Tuple[bool, Optional[str]]:
    """Validate Passport MRZ Line 2 structure (typically 44 characters containing passport number and check digits)."""
    clean_val = clean_str(val).replace(" ", "")
    if len(clean_val) >= 40 and "<" in clean_val:
        return True, None
    return False, f"Value '{clean_val}' does not appear to be a valid 44-char MRZ string"


def validate_ifsc(val: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian IFSC Code (4 letters + '0' + 6 alphanumeric characters)."""
    clean_val = clean_str(val).upper().replace(" ", "")
    if re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", clean_val):
        return True, None
    return False, f"Value '{clean_val}' does not match standard IFSC format (4 letters + '0' + 6 alphanumeric)"


def validate_bank_account(val: str) -> Tuple[bool, Optional[str]]:
    """Validate bank account number (9 to 18 digits)."""
    digits = re.sub(r"[\s\-]", "", clean_str(val))
    if not digits.isdigit():
        return False, "Account number must be numeric"
    if not (9 <= len(digits) <= 18):
        return False, f"Account number length must be 9-18 digits (found {len(digits)})"
    return True, None


def validate_date(val: str) -> Tuple[bool, Optional[str]]:
    """Validate date format and calendar sanity (DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY)."""
    raw = clean_str(val)
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt)
            # Basic sanity: year between 1900 and 2100
            if 1900 <= parsed.year <= 2100:
                return True, None
        except ValueError:
            continue
    return False, f"Value '{raw}' is not a valid recognized date format"


def validate_amount(val: str) -> Tuple[bool, Optional[str]]:
    """Validate financial figure/amount."""
    cleaned = re.sub(r"[₹$,\s]", "", clean_str(val))
    try:
        num = float(cleaned)
        if num > 0:
            return True, None
    except ValueError:
        pass
    return False, f"Value '{val}' is not a valid positive monetary figure"


def validate_field(field_name: str, value: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Route a field value to its respective domain validator.
    """
    if not value or not str(value).strip():
        return False, "Field is empty or null"

    norm_name = field_name.lower().strip()

    if "aadhaar" in norm_name:
        return validate_aadhaar(value)
    if "pan" in norm_name or "tin" in norm_name:
        return validate_pan(value)
    if "dl number" in norm_name or "licence" in norm_name:
        return validate_dl(value)
    if "passport number" in norm_name:
        return validate_passport(value)
    if "mrz" in norm_name:
        return validate_mrz_line2(value)
    if "ifsc" in norm_name:
        return validate_ifsc(value)
    if "account number" in norm_name:
        return validate_bank_account(value)
    if "date" in norm_name or "valid till" in norm_name or "dob" in norm_name:
        return validate_date(value)
    if "amount" in norm_name:
        return validate_amount(value)

    # General non-empty text (names, places, etc.)
    if len(str(value).strip()) >= 2:
        return True, None

    return False, f"Value '{value}' is too short for a valid field entry"

