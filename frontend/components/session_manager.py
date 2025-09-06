"""
Session state management for Streamlit application
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from config.settings import PHASE_LANGUAGE_SELECTION, PHASE_COLLECTION, PHASE_CHAT, BACKEND_BASE_URL, REQUIRED_FIELDS

@dataclass
class UserProfile:
    """User profile data structure"""
    first_name: str = ""
    last_name: str = ""
    id_number: str = ""
    gender: str = ""
    age: Optional[int] = None
    hmo: str = ""
    hmo_card_number: str = ""
    membership_tier: str = ""
    phone_number: str = ""
    email: str = ""
    address: str = ""
    emergency_contact: str = ""
    confirmed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper null handling"""
        data = asdict(self)
        # Convert empty strings to None for optional integer fields
        if data.get('age') == "" or data.get('age') == "":
            data['age'] = None
        return data
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        profile_dict = self.to_dict()
        return all(profile_dict.get(field, "") for field in REQUIRED_FIELDS)
    
    def get_completion_percentage(self) -> int:
        """Get completion percentage for required fields"""
        profile_dict = self.to_dict()
        completed = sum(1 for field in REQUIRED_FIELDS if profile_dict.get(field, ""))
        return int((completed / len(REQUIRED_FIELDS)) * 100)

@dataclass
class ChatMessage:
    """Chat message data structure"""
    content: str
    is_user: bool
    timestamp: str = ""
    sources: List[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def initialize_session():
        """Initialize session state with default values"""
        if "initialized" not in st.session_state:
            st.session_state.initialized = True
            st.session_state.current_phase = PHASE_LANGUAGE_SELECTION
            st.session_state.user_profile = UserProfile()
            st.session_state.conversation_history = []
            st.session_state.backend_url = BACKEND_BASE_URL
            st.session_state.language = "he"  # Default to Hebrew
            st.session_state.debug_mode = False
            st.session_state.profile_collection_step = 0
            st.session_state.last_llm_question = ""
            st.session_state.backend_connected = None
            st.session_state.show_profile_summary = False
    
    @staticmethod
    def get_user_profile() -> UserProfile:
        """Get current user profile"""
        SessionManager.initialize_session()
        return st.session_state.user_profile
    
    @staticmethod
    def update_user_profile(updates: Dict[str, Any]):
        """Update user profile with new data"""
        SessionManager.initialize_session()
        profile = st.session_state.user_profile
        
        for field, value in updates.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        st.session_state.user_profile = profile
    
    @staticmethod
    def get_conversation_history() -> List[ChatMessage]:
        """Get conversation history"""
        SessionManager.initialize_session()
        return st.session_state.conversation_history
    
    @staticmethod
    def add_chat_message(content: str, is_user: bool, sources: List[str] = None, debug_info: Dict[str, Any] = None):
        """Add message to conversation history"""
        SessionManager.initialize_session()
        
        message = ChatMessage(
            content=content,
            is_user=is_user,
            sources=sources or [],
            debug_info=debug_info or {}
        )
        
        st.session_state.conversation_history.append(message)
    
    @staticmethod
    def clear_conversation():
        """Clear conversation history"""
        SessionManager.initialize_session()
        st.session_state.conversation_history = []
    
    @staticmethod
    def get_current_phase() -> str:
        """Get current application phase"""
        SessionManager.initialize_session()
        return st.session_state.current_phase
    
    @staticmethod
    def set_phase(phase: str):
        """Set current application phase"""
        SessionManager.initialize_session()
        st.session_state.current_phase = phase
    
    @staticmethod
    def transition_to_chat():
        """Transition from profile collection to chat phase"""
        SessionManager.initialize_session()
        profile = st.session_state.user_profile
        
        if profile.is_complete():
            st.session_state.current_phase = PHASE_CHAT
            st.session_state.show_profile_summary = True
            return True
        return False
    
    @staticmethod
    def get_language() -> str:
        """Get current language setting"""
        SessionManager.initialize_session()
        return st.session_state.language
    
    @staticmethod
    def set_language(language: str):
        """Set language preference"""
        SessionManager.initialize_session()
        st.session_state.language = language
    
    @staticmethod
    def toggle_language():
        """Toggle between Hebrew and English"""
        SessionManager.initialize_session()
        current = st.session_state.language
        st.session_state.language = "en" if current == "he" else "he"
    
    @staticmethod
    def get_debug_mode() -> bool:
        """Get debug mode status"""
        SessionManager.initialize_session()
        return st.session_state.debug_mode
    
    @staticmethod
    def toggle_debug_mode():
        """Toggle debug mode"""
        SessionManager.initialize_session()
        st.session_state.debug_mode = not st.session_state.debug_mode
    
    @staticmethod
    def get_backend_url() -> str:
        """Get backend URL"""
        SessionManager.initialize_session()
        return st.session_state.backend_url
    
    @staticmethod
    def set_backend_url(url: str):
        """Set backend URL"""
        SessionManager.initialize_session()
        st.session_state.backend_url = url
    
    @staticmethod
    def get_backend_status() -> Optional[bool]:
        """Get backend connection status"""
        SessionManager.initialize_session()
        return st.session_state.backend_connected
    
    @staticmethod
    def set_backend_status(connected: bool):
        """Set backend connection status"""
        SessionManager.initialize_session()
        st.session_state.backend_connected = connected
    
    @staticmethod
    def reset_session():
        """Reset entire session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        SessionManager.initialize_session()
    
    @staticmethod
    def get_profile_collection_step() -> int:
        """Get current profile collection step"""
        SessionManager.initialize_session()
        return st.session_state.profile_collection_step
    
    @staticmethod
    def increment_profile_step():
        """Increment profile collection step"""
        SessionManager.initialize_session()
        st.session_state.profile_collection_step += 1
    
    @staticmethod
    def get_last_llm_question() -> str:
        """Get last LLM question"""
        SessionManager.initialize_session()
        return st.session_state.last_llm_question
    
    @staticmethod
    def set_last_llm_question(question: str):
        """Set last LLM question"""
        SessionManager.initialize_session()
        st.session_state.last_llm_question = question
    
    @staticmethod
    def export_session_data() -> Dict[str, Any]:
        """Export session data for debugging"""
        SessionManager.initialize_session()
        
        return {
            "current_phase": st.session_state.current_phase,
            "user_profile": st.session_state.user_profile.to_dict(),
            "conversation_count": len(st.session_state.conversation_history),
            "language": st.session_state.language,
            "debug_mode": st.session_state.debug_mode,
            "profile_completion": st.session_state.user_profile.get_completion_percentage(),
            "backend_status": st.session_state.backend_connected
        }
