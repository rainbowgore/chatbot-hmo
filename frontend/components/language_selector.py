"""
Language selection component for the Smart Health System
"""
import streamlit as st
from .session_manager import SessionManager
from config.settings import PHASE_COLLECTION


class LanguageSelector:
    """Handle language selection interface"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def render(self):
        """Render the language selection interface"""
        
        # Center the content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Title and welcome message
            st.markdown("# 🏥 Smart Health System")
            st.markdown("### מערכת הבריאות החכמה")
            
            st.markdown("---")
            
            # Language selection prompt in both languages
            st.markdown("""
            <div style='text-align: center; margin: 2rem 0;'>
                <h3>Please select your preferred language</h3>
                <h3 style='direction: rtl;'>אנא בחר את השפה המועדפת עליך</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Language selection buttons
            col_he, col_en = st.columns(2)
            
            with col_he:
                if st.button("🇮🇱 עברית", key="lang_he", use_container_width=True):
                    # Clear any existing session state to ensure clean transition
                    st.session_state.language = "he"
                    st.session_state.current_phase = PHASE_COLLECTION
                    st.session_state.initialized = True
                    # Force rerun with experimental rerun
                    st.rerun()
            
            with col_en:
                if st.button("🇺🇸 English", key="lang_en", use_container_width=True):
                    # Clear any existing session state to ensure clean transition
                    st.session_state.language = "en" 
                    st.session_state.current_phase = PHASE_COLLECTION
                    st.session_state.initialized = True
                    # Force rerun with experimental rerun
                    st.rerun()
            
            # Additional info
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; color: #666; font-size: 0.9rem;'>
                <p>This system will help you register for health services and get personalized medical information</p>
                <p style='direction: rtl;'>מערכת זו תעזור לך להירשם לשירותי בריאות ולקבל מידע רפואי מותאם אישית</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _select_language(self, language: str):
        """Handle language selection and proceed to profile collection"""
        # Set language first
        st.session_state.language = language
        # Set phase to collection
        st.session_state.current_phase = PHASE_COLLECTION
        # Force rerun
        st.rerun()
