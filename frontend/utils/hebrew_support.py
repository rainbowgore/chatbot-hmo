"""
RTL/Hebrew display helpers
"""
import re
from typing import Dict, Any

def is_rtl_text(text: str) -> bool:
    """
    Determine if text should be displayed RTL
    """
    # Check for Hebrew, Arabic, or other RTL characters
    rtl_pattern = r'[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F]'
    return bool(re.search(rtl_pattern, text))

def wrap_rtl_content(content: str, css_class: str = "rtl-text") -> str:
    """
    Wrap content with RTL CSS class if needed
    """
    if is_rtl_text(content):
        return f'<div class="{css_class}">{content}</div>'
    return content

def get_text_direction(text: str) -> str:
    """
    Get CSS direction property for text
    """
    return "rtl" if is_rtl_text(text) else "ltr"

def format_mixed_text(text: str) -> str:
    """
    Handle mixed Hebrew/English text with proper direction
    """
    # Split by sentences and apply direction per sentence
    sentences = re.split(r'[.!?]\s+', text)
    formatted_sentences = []
    
    for sentence in sentences:
        if sentence.strip():
            direction = get_text_direction(sentence)
            formatted_sentences.append(
                f'<span dir="{direction}">{sentence.strip()}</span>'
            )
    
    return '. '.join(formatted_sentences)

def get_hebrew_font_stack() -> str:
    """
    Get CSS font stack optimized for Hebrew
    """
    return "'Segoe UI', 'Arial Hebrew', 'Noto Sans Hebrew', Arial, sans-serif"

def apply_hebrew_styling(element_type: str = "div") -> Dict[str, str]:
    """
    Get CSS properties for Hebrew text elements
    """
    return {
        "direction": "rtl",
        "text-align": "right",
        "font-family": get_hebrew_font_stack(),
        "line-height": "1.6"
    }

def format_profile_field_hebrew(field_name: str, value: str) -> str:
    """
    Format profile field with proper Hebrew alignment
    """
    hebrew_field_names = {
        "first_name": "שם פרטי",
        "last_name": "שם משפחה",
        "id_number": "תעודת זהות", 
        "gender": "מין",
        "age": "גיל",
        "hmo": "קופת חולים",
        "hmo_card_number": "מספר כרטיס",
        "membership_tier": "דרגת חברות",
        "phone_number": "טלפון",
        "email": "אימייל",
        "address": "כתובת",
        "emergency_contact": "איש קשר לחירום"
    }
    
    hebrew_name = hebrew_field_names.get(field_name, field_name)
    
    # Format with RTL alignment
    return f'<div class="rtl-text"><strong>{hebrew_name}:</strong> {value}</div>'

def get_language_toggle_text(current_lang: str) -> str:
    """
    Get text for language toggle button
    """
    return "English" if current_lang == "he" else "עברית"

def format_chat_bubble_rtl(message: str, is_user: bool = False) -> str:
    """
    Format chat message with proper RTL support
    """
    direction = get_text_direction(message)
    alignment = "right" if direction == "rtl" else "left"
    
    bubble_class = "user-message" if is_user else "bot-message"
    
    return f'''
    <div class="{bubble_class}" style="text-align: {alignment}; direction: {direction};">
        {message}
    </div>
    '''
