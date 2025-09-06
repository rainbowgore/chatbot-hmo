"""
Main Streamlit Application Entry Point
Smart Health System Frontend
"""
import streamlit as st
import os
from pathlib import Path

# Add the current directory to Python path for imports
import sys
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from components.session_manager import SessionManager
from components.language_selector import LanguageSelector
from components.profile_collector import ProfileCollector
from components.chat_interface import ChatInterface
from config.settings import PHASE_LANGUAGE_SELECTION, PHASE_COLLECTION, PHASE_CHAT, MESSAGES
from utils.hebrew_support import get_language_toggle_text

def load_css():
    """Load custom CSS styling"""
    css_file = current_dir / "assets" / "style.css"
    
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning("CSS file not found. Some styling may be missing.")

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Smart Health System",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "Smart Health System - Medical Q&A with Profile Management"
        }
    )

def render_header():
    """Render application header with navigation"""
    current_phase = SessionManager.get_current_phase()
    
    # Skip header during language selection
    if current_phase == PHASE_LANGUAGE_SELECTION:
        return
    
    language = SessionManager.get_language()
    messages = MESSAGES[language]
    
    # Main title
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        if language == "he":
            st.title("🏥 מערכת הבריאות החכמה")
        else:
            st.title("🏥 Smart Health System")
    
    with col2:
        # Language toggle
        toggle_text = get_language_toggle_text(language)
        if st.button(f"🌐 {toggle_text}", key="header_lang_toggle"):
            SessionManager.toggle_language()
            st.rerun()
    
    with col3:
        # Debug mode toggle (if enabled)
        if st.checkbox("Debug", value=SessionManager.get_debug_mode(), key="header_debug"):
            if SessionManager.get_debug_mode() != st.session_state.header_debug:
                SessionManager.toggle_debug_mode()
                st.rerun()

def render_phase_indicator():
    """Render current phase indicator"""
    current_phase = SessionManager.get_current_phase()
    
    # Skip phase indicator during language selection
    if current_phase == PHASE_LANGUAGE_SELECTION:
        return
    
    language = SessionManager.get_language()
    
    if current_phase == PHASE_COLLECTION:
        if language == "he":
            phase_text = "שלב 1: איסוף פרטי משתמש"
            st.markdown(f'<div style="direction: rtl; text-align: right; background-color: #e1f5fe; color: #000000; padding: 10px; border-radius: 5px; border-left: 4px solid #01579b; margin-top: 10px;">{phase_text}</div>', unsafe_allow_html=True)
        else:
            phase_text = "Phase 1: User Profile Collection"
            st.info(phase_text, icon="📝")
    
    elif current_phase == PHASE_CHAT:
        if language == "he":
            phase_text = "💬 שלב 2: שאלות ותשובות רפואיות"
            st.markdown(f'<div style="direction: rtl; text-align: right; background-color: #e1f5fe; color: #000000; padding: 10px; border-radius: 5px; border-left: 4px solid #01579b; margin-top: 10px;">{phase_text}</div>', unsafe_allow_html=True)
        else:
            phase_text = "Phase 2: Medical Q&A"
            st.info(phase_text, icon="💬")

def render_backend_status():
    """Render backend connection status"""
    current_phase = SessionManager.get_current_phase()
    
    # Skip backend status during language selection
    if current_phase == PHASE_LANGUAGE_SELECTION:
        return
    
    backend_status = SessionManager.get_backend_status()
    language = SessionManager.get_language()
    
    if backend_status is True:
        if language == "he":
            st.markdown('<div style="direction: rtl; text-align: right; background-color: #d4edda; color: #155724; padding: 12px; border-radius: 4px; border: 1px solid #c3e6cb;">🟢 ברוכים הבאים!</div>', unsafe_allow_html=True)
        else:
            st.success("Welcome!", icon="🟢")
    
    elif backend_status is False:
        if language == "he":
            st.markdown('<div style="direction: rtl; text-align: right; background-color: #f8d7da; color: #721c24; padding: 12px; border-radius: 4px; border: 1px solid #f5c6cb;">🔴 שרת מנותק</div>', unsafe_allow_html=True)
        else:
            st.error("🔴 Backend Disconnected", icon="🔴")
        
        # Show reconnect button
        reconnect_text = "נסה להתחבר שוב" if language == "he" else "Try to Reconnect"
        if st.button(reconnect_text):
            from components.api_client import test_backend_connection
            test_backend_connection()
            st.rerun()
    
    else:
        if language == "he":
            st.markdown('<div style="direction: rtl; text-align: right; background-color: #fff3cd; color: #856404; padding: 12px; border-radius: 4px; border: 1px solid #ffeaa7; margin-bottom: 15px;">🟡נא להמתין כבר מתחילים...</div>', unsafe_allow_html=True)
        else:
            st.warning("Getting Started...", icon="🟡")

def render_navigation():
    """Render navigation controls"""
    current_phase = SessionManager.get_current_phase()
    language = SessionManager.get_language()
    
    if current_phase == PHASE_CHAT:
        # Show option to go back to profile
        if language == "he":
            back_text = "🔙 חזור לעריכת פרופיל"
        else:
            back_text = "🔙 Back to Profile"
        
        if st.button(back_text, key="nav_back_to_profile"):
            SessionManager.set_phase(PHASE_COLLECTION)
            st.rerun()

def render_footer():
    """Render application footer"""
    language = SessionManager.get_language()
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if language == "he":
            st.caption("מערכת הבריאות החכמה")
        else:
            st.caption("Smart Health System")
    
    with col2:
        # Session controls
        if language == "he":
            reset_text = "🔄 איפוס מערכת"
        else:
            reset_text = "🔄 Reset System"
        
        if st.button(reset_text, key="footer_reset"):
            # Use session state to track confirmation step
            if "confirm_reset" not in st.session_state:
                st.session_state.confirm_reset = False
            
            if not st.session_state.confirm_reset:
                st.session_state.confirm_reset = True
                st.warning("Are you sure you want to reset?" if language == "en" else "האם אתה בטוח שברצונך לאפס?")
                st.rerun()
            else:
                SessionManager.reset_session()
                st.session_state.confirm_reset = False
                st.rerun()
    
    with col3:
        # Show session info in debug mode
        if SessionManager.get_debug_mode():
            session_data = SessionManager.export_session_data()
            st.caption(f"Phase: {session_data['current_phase']}")

def main():
    """Main application function"""
    # Configure page
    configure_page()
    
    # Load CSS
    load_css()
    
    # Initialize session
    SessionManager.initialize_session()
    
    # Render header
    render_header()
    
    # Show backend status
    render_backend_status()
    
    # Show phase indicator
    render_phase_indicator()
    
    # Show navigation if needed
    render_navigation()
    
    # Main content area
    current_phase = SessionManager.get_current_phase()
    
    try:
        if current_phase == PHASE_LANGUAGE_SELECTION:
            # Language Selection Phase
            language_selector = LanguageSelector(SessionManager)
            language_selector.render()
        
        elif current_phase == PHASE_COLLECTION:
            # Profile Collection Phase
            profile_collector = ProfileCollector()
            profile_collector.render()
        
        elif current_phase == PHASE_CHAT:
            # Medical Q&A Chat Phase
            chat_interface = ChatInterface()
            chat_interface.render()
        
        else:
            # Unknown phase - reset to language selection
            st.error("Unknown phase detected. Resetting to language selection.")
            SessionManager.set_phase(PHASE_LANGUAGE_SELECTION)
            st.rerun()
    
    except Exception as e:
        # Error handling
        language = SessionManager.get_language()
        
        if language == "he":
            st.error(f"שגיאה במערכת: {str(e)}")
        else:
            st.error(f"System Error: {str(e)}")
        
        if SessionManager.get_debug_mode():
            st.exception(e)
        
        # Offer to reset
        if language == "he":
            reset_text = "איפוס מערכת"
        else:
            reset_text = "Reset System"
        
        if st.button(reset_text, key="error_reset"):
            SessionManager.reset_session()
            st.rerun()
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()
