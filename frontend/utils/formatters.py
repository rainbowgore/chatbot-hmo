"""
Text and UI formatting utilities
"""
from typing import Dict, Any, List
import re

def format_profile_display(profile: Dict[str, Any], language: str = "he") -> str:
    """
    Format user profile for display
    """
    if language == "he":
        field_names = {
            "first_name": "שם פרטי",
            "last_name": "שם משפחה", 
            "id_number": "תעודת זהות",
            "gender": "מין",
            "age": "גיל",
            "hmo": "קופת חולים",
            "hmo_card_number": "מספר כרטיס",
            "membership_tier": "דרגת חברות",
            "phone_number": "טלפון",
            "email": "אימייל"
        }
    else:
        field_names = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "id_number": "ID Number", 
            "gender": "Gender",
            "age": "Age",
            "hmo": "HMO",
            "hmo_card_number": "Card Number",
            "membership_tier": "Membership Tier",
            "phone_number": "Phone",
            "email": "Email"
        }
    
    # Gender value mapping
    def map_gender_value(gender_value: str, target_language: str) -> str:
        if not gender_value:
            return gender_value
        
        gender_mapping = {
            "Male": "זכר" if target_language == "he" else "Male",
            "Female": "נקבה" if target_language == "he" else "Female",
            "זכר": "זכר" if target_language == "he" else "Male",
            "נקבה": "נקבה" if target_language == "he" else "Female"
        }
        return gender_mapping.get(gender_value, gender_value)
    
    formatted_lines = []
    for field, value in profile.items():
        if value and field in field_names:
            # Apply gender mapping if it's the gender field
            display_value = value
            if field == "gender":
                display_value = map_gender_value(value, language)
            
            formatted_lines.append(f"**{field_names[field]}:** {display_value}")
    
    return "\n".join(formatted_lines)

def format_progress_percentage(profile: Dict[str, Any]) -> int:
    """
    Calculate profile completion percentage
    """
    from config.settings import REQUIRED_FIELDS
    
    completed_required = sum(1 for field in REQUIRED_FIELDS if profile.get(field))
    return int((completed_required / len(REQUIRED_FIELDS)) * 100)

def format_field_status(field_name: str, profile: Dict[str, Any]) -> str:
    """
    Get field completion status for UI display
    """
    from config.settings import REQUIRED_FIELDS
    
    value = profile.get(field_name)
    
    if value:
        return "✅"  # Completed
    elif field_name in REQUIRED_FIELDS:
        return "❌"  # Required but missing
    else:
        return "⭕"  # Optional

def format_chat_message(message: str, is_user: bool = False) -> str:
    """
    Format chat message for display
    """
    if is_user:
        return f"👤 **You:** {message}"
    else:
        return f"🤖 **Assistant:** {message}"

def format_hebrew_text(text: str) -> str:
    """
    Apply Hebrew-specific formatting
    """
    # Add RTL marker for Hebrew text
    if contains_hebrew(text):
        return f'<div class="rtl-text hebrew-font">{text}</div>'
    return text

def contains_hebrew(text: str) -> bool:
    """
    Check if text contains Hebrew characters
    """
    hebrew_pattern = r'[\u0590-\u05FF]'
    return bool(re.search(hebrew_pattern, text))

def format_validation_errors(errors: List[str], language: str = "he") -> str:
    """
    Format validation errors for display
    """
    if not errors:
        return ""
    
    if language == "he":
        header = "שגיאות בוולידציה:"
    else:
        header = "Validation Errors:"
    
    formatted_errors = [f"• {error}" for error in errors]
    return f"{header}\n" + "\n".join(formatted_errors)

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text with ellipsis if too long
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_debug_info(data: Dict[str, Any]) -> str:
    """
    Format debug information for display
    """
    lines = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"**{key}:** {len(value) if isinstance(value, list) else 'object'}")
        else:
            lines.append(f"**{key}:** {value}")
    
    return "\n".join(lines)
