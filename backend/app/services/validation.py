import re
from typing import Dict, Any, List, Optional

VALID_HMOS = {"מכבי", "מאוחדת", "כללית"}
VALID_TIERS = {"זהב", "כסף", "ארד"}

def validate_id_number(id_number: str) -> bool:
    return bool(re.fullmatch(r"\d{9}", id_number))

def validate_age(age: int) -> bool:
    return 0 <= age <= 120

def validate_hmo(hmo: str) -> bool:
    return hmo in VALID_HMOS

def validate_membership_tier(tier: str) -> bool:
    return tier in VALID_TIERS

def validate_user_info(user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize user information
    """
    validated_info = {}
    
    # Validate HMO
    if "hmo" in user_info and validate_hmo(user_info["hmo"]):
        validated_info["hmo"] = user_info["hmo"]
    
    # Validate membership tier
    if "membership_tier" in user_info and validate_membership_tier(user_info["membership_tier"]):
        validated_info["membership_tier"] = user_info["membership_tier"]
    
    # Validate age
    if "age" in user_info and isinstance(user_info["age"], int) and validate_age(user_info["age"]):
        validated_info["age"] = user_info["age"]
    
    # Validate ID number
    if "id_number" in user_info and validate_id_number(user_info["id_number"]):
        validated_info["id_number"] = user_info["id_number"]
    
    # Validate HMO card number
    if "hmo_card_number" in user_info and validate_id_number(user_info["hmo_card_number"]):
        validated_info["hmo_card_number"] = user_info["hmo_card_number"]
    
    # Pass through other fields without validation for now
    for field in ["first_name", "last_name", "gender"]:
        if field in user_info and user_info[field]:
            validated_info[field] = user_info[field]
    
    return validated_info

def extract_user_info_from_message(message: str, user_profile: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract user information from a free-form natural language message.
    - Supports Hebrew and English heuristics for common fields
    - Returns only validated fields
    - If user_profile is provided and marked confirmed, extraction is skipped
    - When user_profile is provided, do not overwrite existing non-empty fields
    """
    if user_profile is not None and getattr(user_profile, "confirmed", False):
        return {}

    proposed: Dict[str, Any] = {}
    text = message.strip()
    text_lower = text.lower()

    # --- HMO (Hebrew + English mapping) ---
    if "מכבי" in text:
        proposed["hmo"] = "מכבי"
    elif "מאוחדת" in text:
        proposed["hmo"] = "מאוחדת"
    elif "כללית" in text:
        proposed["hmo"] = "כללית"
    else:
        # English to Hebrew mapping
        if "maccabi" in text_lower:
            proposed["hmo"] = "מכבי"
        elif "meuhedet" in text_lower:
            proposed["hmo"] = "מאוחדת"
        elif "clalit" in text_lower:
            proposed["hmo"] = "כללית"

    # --- Membership tier (Hebrew + English mapping) ---
    if "זהב" in text:
        proposed["membership_tier"] = "זהב"
    elif "כסף" in text:
        proposed["membership_tier"] = "כסף"
    elif "ארד" in text:
        proposed["membership_tier"] = "ארד"
    else:
        if "gold" in text_lower:
            proposed["membership_tier"] = "זהב"
        elif "silver" in text_lower:
            proposed["membership_tier"] = "כסף"
        elif "bronze" in text_lower:
            proposed["membership_tier"] = "ארד"

    # --- Gender (Hebrew + English) ---
    if any(word in text_lower for word in ["female", "נקבה"]):
        proposed["gender"] = "Female"
    elif any(word in text_lower for word in ["male", "זכר"]):
        proposed["gender"] = "Male"

    # --- Age (heuristics to avoid matching IDs) ---
    age_patterns = [
        r"\b(?:i\s*am|i'm|age|גיל)\s*(\d{1,3})\b",
        r"\bאני\s*(\d{1,3})\b",
        r"\b(\d{1,3})\s*years?\s*old\b",
        r"\bגיל\s*(\d{1,3})\b",
    ]
    age_value: Optional[int] = None
    for pat in age_patterns:
        m = re.search(pat, text_lower)
        if m:
            try:
                age_candidate = int(m.group(1))
                if validate_age(age_candidate):
                    age_value = age_candidate
                    break
            except Exception:
                pass
    if age_value is not None:
        proposed["age"] = age_value

    # --- Names (English + Hebrew common phrases) ---
    # English: "my name is Sarah Levi" | "I am Sarah Levi"
    name_patterns = [
        r"\bmy name is\s+([A-Za-zא-ת'-]+)\s+([A-Za-zא-ת'-]+)\b",
        r"\bi am\s+([A-Za-zא-ת'-]+)\s+([A-Za-zא-ת'-]+)\b",
        r"\bשמי\s+([א-ת'-]+)\s+([א-ת'-]+)\b",
        r"\bקוראים לי\s+([א-ת'-]+)\s+([א-ת'-]+)\b",
    ]
    for pat in name_patterns:
        m = re.search(pat, text_lower)
        if m:
            first_name = m.group(1).strip().title()
            last_name = m.group(2).strip().title()
            proposed["first_name"] = first_name
            proposed["last_name"] = last_name
            break
    
    # If no structured pattern found, try simple name extraction
    # This handles cases like "דוד כהן" or "John Smith" but respects the collection order
    if "first_name" not in proposed and "last_name" not in proposed:
        # Remove numbers and special chars, split by whitespace
        clean_text = re.sub(r'[^\w\s\u0590-\u05FF-]', ' ', text).strip()
        words = clean_text.split()
        # Filter out words that are clearly not names (numbers, very short/long words)
        name_words = [w for w in words if re.match(r'^[A-Za-zא-ת-]{2,20}$', w)]
        
        if len(name_words) >= 1:
            # Check current profile state
            current_first = getattr(user_profile, "first_name", None) if user_profile else None
            current_last = getattr(user_profile, "last_name", None) if user_profile else None
            
            # Only extract what we're missing, following the sequence order
            if not current_first:
                # Missing first name - extract only first word
                proposed["first_name"] = name_words[0]
            elif not current_last and len(name_words) >= 1:
                # Have first name, missing last name - extract as last name
                # If multiple words provided, take the last one as surname
                proposed["last_name"] = name_words[-1] if len(name_words) > 1 else name_words[0]

    # --- ID and HMO card numbers (prefer context; else assign first/second 9-digit) ---
    # Contextual matches
    id_context = re.search(r"(?:id|ת\.?ז\.?|מספר\s*זהות)[^\d]{0,8}(\d{9})", text_lower)
    card_context = re.search(r"(?:card|כרטיס)[^\d]{0,8}(\d{9})", text_lower)
    if id_context:
        proposed["id_number"] = id_context.group(1)
    if card_context:
        proposed["hmo_card_number"] = card_context.group(1)

    # Fallback: assign first/second 9-digit sequences
    if "id_number" not in proposed or "hmo_card_number" not in proposed:
        all_nines = re.findall(r"\b(\d{9})\b", text)
        # Assign in order if still missing
        idx = 0
        if "id_number" not in proposed and idx < len(all_nines):
            proposed["id_number"] = all_nines[idx]
            idx += 1
        if "hmo_card_number" not in proposed and idx < len(all_nines):
            proposed["hmo_card_number"] = all_nines[idx]

    # Validate extracted fields
    validated = validate_user_info(proposed)

    # If merging with an existing profile, only include fields that are currently empty/None
    if user_profile is not None and not getattr(user_profile, "confirmed", False):
        safe_merge: Dict[str, Any] = {}
        for field, value in validated.items():
            current = getattr(user_profile, field, None)
            if not current:  # empty string, None, or falsy
                safe_merge[field] = value
        return safe_merge

    return validated
