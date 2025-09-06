"""
Frontend validation helpers
"""
import re
from typing import Dict, Any, List, Tuple

def validate_israeli_id(id_number: str) -> Tuple[bool, str]:
    """
    Validate Israeli ID number using check digit algorithm
    """
    if not id_number or not id_number.isdigit():
        return False, "ID must contain only digits"
    
    if len(id_number) != 9:
        return False, "ID must be exactly 9 digits"
    
    # Israeli ID check digit algorithm
    total = 0
    for i, digit in enumerate(id_number):
        num = int(digit)
        if i % 2 == 1:  # Even position (0-indexed)
            num *= 2
            if num > 9:
                num = num // 10 + num % 10
        total += num
    
    if total % 10 != 0:
        return False, "Invalid Israeli ID number"
    
    return True, ""

def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate Israeli phone number format
    """
    if not phone:
        return True, ""  # Optional field
    
    # Remove spaces and dashes
    clean_phone = re.sub(r'[\s-]', '', phone)
    
    # Israeli mobile: 05X-XXXXXXX or landline: 0X-XXXXXXX
    if not re.match(r'^0[2-9]\d{7,8}$', clean_phone):
        return False, "Invalid phone number format"
    
    return True, ""

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    """
    if not email:
        return True, ""  # Optional field
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, ""

def validate_age(age_str: str) -> Tuple[bool, str]:
    """
    Validate age input
    """
    try:
        age = int(age_str)
        if age < 0 or age > 150:
            return False, "Age must be between 0 and 150"
        return True, ""
    except ValueError:
        return False, "Age must be a number"

def validate_hmo_card_number(card_number: str) -> Tuple[bool, str]:
    """
    Validate HMO card number format
    """
    if not card_number:
        return False, "HMO card number is required"
    
    # Basic validation - should be numeric and reasonable length
    if not card_number.isdigit() or len(card_number) < 6 or len(card_number) > 12:
        return False, "HMO card number should be 6-12 digits"
    
    return True, ""

def validate_profile_field(field_name: str, value: str) -> Tuple[bool, str]:
    """
    Validate individual profile field
    """
    if not value and field_name in ["first_name", "last_name", "gender", "hmo"]:
        return False, f"{field_name} is required"
    
    validators = {
        "id_number": validate_israeli_id,
        "phone_number": validate_phone_number,
        "email": validate_email,
        "age": validate_age,
        "hmo_card_number": validate_hmo_card_number
    }
    
    if field_name in validators:
        return validators[field_name](value)
    
    # Default validation for text fields
    if field_name in ["first_name", "last_name"] and value:
        if len(value) < 2:
            return False, f"{field_name} must be at least 2 characters"
    
    return True, ""

def validate_complete_profile(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate complete user profile
    """
    errors = []
    
    from config.settings import REQUIRED_FIELDS
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in profile or not profile[field]:
            errors.append(f"Missing required field: {field}")
            continue
        
        is_valid, error_msg = validate_profile_field(field, str(profile[field]))
        if not is_valid:
            errors.append(f"{field}: {error_msg}")
    
    # Validate optional fields if present
    optional_fields = ["phone_number", "email"]
    for field in optional_fields:
        if field in profile and profile[field]:
            is_valid, error_msg = validate_profile_field(field, str(profile[field]))
            if not is_valid:
                errors.append(f"{field}: {error_msg}")
    
    return len(errors) == 0, errors
