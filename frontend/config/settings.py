"""
Frontend configuration and constants
"""
import os
from typing import Dict, List

# Backend Integration
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")

ENDPOINTS = {
    "collect_user_info": "/collect_user_info",
    "chat": "/chat", 
    "health": "/health",
    "kb_stats": "/kb_stats"
}

# UI Constants
PHASE_LANGUAGE_SELECTION = "language_selection"
PHASE_COLLECTION = "profile_collection"
PHASE_CHAT = "medical_chat"

LANGUAGES = ["עברית", "English"]

# Required profile fields
REQUIRED_FIELDS = [
    "first_name", 
    "last_name", 
    "id_number", 
    "gender", 
    "age", 
    "hmo", 
    "hmo_card_number", 
    "membership_tier"
]

# Optional profile fields
OPTIONAL_FIELDS = [
    "phone_number",
    "email",
    "address",
    "emergency_contact"
]

# UI Messages
MESSAGES = {
    "he": {
        "welcome": "ברוכים הבאים למערכת הבריאות החכמה",
        "profile_collection": "איסוף פרטי משתמש",
        "chat_phase": "שאלות ותשובות רפואיות",
        "profile_complete": "הפרופיל הושלם בהצלחה",
        "start_chat": "התחל צ'אט",
        "backend_error": "שגיאה בחיבור לשרת",
        "validation_error": "שגיאה בוולידציה"
    },
    "en": {
        "welcome": "Welcome to Smart Health System",
        "profile_collection": "User Profile Collection", 
        "chat_phase": "Medical Q&A",
        "profile_complete": "Profile completed successfully",
        "start_chat": "Start Chat",
        "backend_error": "Backend connection error",
        "validation_error": "Validation error"
    }
}

# Styling
CSS_CLASSES = {
    "rtl_text": "rtl-text",
    "hebrew_font": "hebrew-font",
    "profile_progress": "profile-progress",
    "field_complete": "field-complete",
    "field_missing": "field-missing",
    "chat_container": "chat-container",
    "user_message": "user-message",
    "bot_message": "bot-message"
}
