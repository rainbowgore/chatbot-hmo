import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from ..models.user import UserProfile
from . import validation

# Load env vars from .env file
load_dotenv()

# Toggle for safe local testing
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
# Toggle for optional free-form extraction prior to LLM question
USE_EXTRACTION = os.getenv("USE_EXTRACTION", "false").lower() == "true"

# Azure OpenAI credentials
AZURE_API_KEY = os.getenv("AOAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Initialize client only if not in mock mode
client = None
if not USE_MOCK:
    client = AzureOpenAI(
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT
    )


def get_next_question(user_profile, user_message: str, language: str = "he") -> str:
    """
    Determines what to ask the user next following the exact sequence:
    1. First name → 2. Last name → 3. ID → 4. Gender → 5. Age → 6. HMO → 7. Card → 8. Tier → 9. Confirmation
    """

    # Use the language preference passed from frontend
    user_prefers_hebrew = (language == "he")

    # ALWAYS use deterministic sequence for proper flow control
    # Handle simple field assignment based on current missing field
    # Skip initial greetings/registration messages
    greeting_patterns = [
        "hi, i want to register", "hello", "שלום, אני רוצה להירשם", 
        "start", "begin", "התחל", "שלום", "hi"
    ]
    
    # Handle confirmation responses
    confirmation_yes = ["yes", "כן", "y", "אישור"]
    confirmation_no = ["no", "לא", "n"]
    
    if user_message and user_message.strip():
        message_lower = user_message.strip().lower()
        
        # Skip processing if it's an initial greeting/registration message
        if message_lower in greeting_patterns:
            pass  # Don't assign to any field
        else:
            # Determine which field we're currently collecting based on what's missing
            if not user_profile.first_name:
                user_profile.first_name = user_message.strip()
            elif not user_profile.last_name:
                user_profile.last_name = user_message.strip()
            elif not user_profile.id_number and user_message.isdigit() and len(user_message) == 9:
                user_profile.id_number = user_message.strip()
            elif not user_profile.gender and user_message.lower() in ['male', 'female', 'זכר', 'נקבה', 'm', 'f']:
                if user_message.lower() in ['male', 'זכר', 'm']:
                    user_profile.gender = 'Male'
                elif user_message.lower() in ['female', 'נקבה', 'f']:
                    user_profile.gender = 'Female'
            elif not user_profile.age and user_message.isdigit():
                age = int(user_message)
                if 0 <= age <= 120:
                    user_profile.age = age
            elif not user_profile.hmo:
                # Handle both Hebrew and English HMO names
                message_lower = user_message.lower().strip()
                if message_lower in ['מכבי', 'maccabi']:
                    user_profile.hmo = 'מכבי'
                elif message_lower in ['כללית', 'clalit']:
                    user_profile.hmo = 'כללית'
                elif message_lower in ['מאוחדת', 'meuhedet']:
                    user_profile.hmo = 'מאוחדת'
                elif message_lower in ['לאומית', 'leumit']:
                    user_profile.hmo = 'לאומית'
            elif not user_profile.hmo_card_number and user_message.isdigit() and len(user_message) == 9:
                user_profile.hmo_card_number = user_message.strip()
            elif not user_profile.membership_tier:
                # Handle both Hebrew and English membership tiers
                message_lower = user_message.lower().strip()
                if message_lower in ['זהב', 'gold']:
                    user_profile.membership_tier = 'זהב'
                elif message_lower in ['כסף', 'silver']:
                    user_profile.membership_tier = 'כסף'
                elif message_lower in ['ארד', 'bronze']:
                    user_profile.membership_tier = 'ארד'

    # If all required fields are present but not yet confirmed, handle confirmation flow first
    required_filled = all([
        bool(getattr(user_profile, 'first_name', None)),
        bool(getattr(user_profile, 'last_name', None)),
        bool(getattr(user_profile, 'id_number', None)),
        bool(getattr(user_profile, 'gender', None)),
        getattr(user_profile, 'age', None) is not None,
        bool(getattr(user_profile, 'hmo', None)),
        bool(getattr(user_profile, 'hmo_card_number', None)),
        bool(getattr(user_profile, 'membership_tier', None)),
    ])

    if required_filled and not getattr(user_profile, 'confirmed', False):
        if user_message and user_message.strip().lower() in confirmation_yes:
            user_profile.confirmed = True
            return (
                "הרישום הושלם! ניתן לעבור לשאלות רפואיות."
                if user_prefers_hebrew else
                "Registration complete! You can proceed to Medical Q&A."
            )
        if user_message and user_message.strip().lower() in confirmation_no:
            return (
                "איזה שדה תרצה לתקן? (שם פרטי, שם משפחה, תעודת זהות, מין, גיל, קופה, כרטיס קופה, דרגה)"
                if user_prefers_hebrew else
                "Which field would you like to correct? (first name, last name, ID, gender, age, HMO, HMO card, tier)"
            )

    # Always follow the deterministic sequence regardless of USE_MOCK
    # This ensures consistent order
    if not user_profile.first_name:
        if user_prefers_hebrew:
            return "מה שמך הפרטי?"
        else:
            return "What is your first name?"
    
    if not user_profile.last_name:
        if user_prefers_hebrew:
            return "מה שם המשפחה שלך?"
        else:
            return "What is your last name?"
    
    if not user_profile.id_number:
        if user_prefers_hebrew:
            return "אנא הזן מספר זהות בן 9 ספרות"
        else:
            return "Could you please provide your ID number?"
    
    if not user_profile.gender:
        if user_prefers_hebrew:
            return "מה המין שלך? זכר / נקבה"
        else:
            return "What is your gender (Male or Female)?"
    
    if not user_profile.age:
        if user_prefers_hebrew:
            return "מה הגיל שלך?"
        else:
            return "What is your age?"
    
    if not user_profile.hmo:
        if user_prefers_hebrew:
            return "באיזו קופת חולים אתה חבר? (מכבי, מאוחדת, כללית, לאומית)"
        else:
            return "Which HMO do you belong to (Maccabi, Clalit, Meuhedet, Leumit)?"
    
    if not user_profile.hmo_card_number:
        if user_prefers_hebrew:
            return "אנא הזן מספר כרטיס קופה בן 9 ספרות"
        else:
            return "What is your HMO card number?"
    
    if not user_profile.membership_tier:
        if user_prefers_hebrew:
            return "מה דרגת החברות שלך? (זהב, כסף, ארד)"
        else:
            return "What is your membership tier (Gold, Silver, Bronze)?"

    # All fields completed - show confirmation
    if user_prefers_hebrew:
        # Map gender to Hebrew for display
        gender_display = user_profile.gender
        if user_profile.gender == "Male":
            gender_display = "זכר"
        elif user_profile.gender == "Female":
            gender_display = "נקבה"
        
        return f"""סיכום:
שם פרטי: {user_profile.first_name}
שם משפחה: {user_profile.last_name}
תעודת זהות: {user_profile.id_number}
מין: {gender_display}
גיל: {user_profile.age}
קופת חולים: {user_profile.hmo}
כרטיס קופה: {user_profile.hmo_card_number}
דרגה: {user_profile.membership_tier}

האם כל המידע נכון? (כן/לא)"""
    else:
        return f"""Summary:
First Name: {user_profile.first_name}
Last Name: {user_profile.last_name}
ID: {user_profile.id_number}
Gender: {user_profile.gender}
Age: {user_profile.age}
HMO: {user_profile.hmo}
HMO Card: {user_profile.hmo_card_number}
Tier: {user_profile.membership_tier}

Is all the information correct and confirmed?"""
