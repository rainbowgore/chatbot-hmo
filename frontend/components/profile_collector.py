"""
Phase 1: User profile collection interface
"""
import streamlit as st
from typing import Dict, Any, Optional
from components.session_manager import SessionManager, UserProfile
from components.api_client import send_profile_collection_request
from utils.validators import validate_complete_profile, validate_profile_field
from utils.formatters import format_profile_display, format_progress_percentage, format_validation_errors
from utils.hebrew_support import wrap_rtl_content, is_rtl_text
from config.settings import MESSAGES, REQUIRED_FIELDS

class ProfileCollector:
    """Handle user profile collection workflow"""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    def render(self):
        """Render the profile collection interface"""
        language = self.session_manager.get_language()
        messages = MESSAGES[language]
        
        # Header
        st.title(messages["profile_collection"])
        
        # Progress indicator
        self._render_progress_indicator()
        
        # Backend status check
        if not self._check_backend_connection():
            return
        
        # Main collection interface
        self._render_collection_interface()
        
        # Profile summary sidebar
        self._render_profile_summary()
    
    def _render_progress_indicator(self):
        """Display profile completion progress"""
        profile = self.session_manager.get_user_profile()
        progress = profile.get_completion_percentage()
        
        language = self.session_manager.get_language()
        
        if language == "he":
            progress_text = f"התקדמות: {progress}%"
        else:
            progress_text = f"Progress: {progress}%"
        
        st.progress(progress / 100)
        st.write(progress_text)
        
        # Show required vs completed fields
        col1, col2 = st.columns(2)
        
        profile_dict = profile.to_dict()
        completed_required = sum(1 for field in REQUIRED_FIELDS if profile_dict.get(field))
        
        with col1:
            if language == "he":
                st.metric("שדות נדרשים", f"{completed_required}/{len(REQUIRED_FIELDS)}")
            else:
                st.metric("Required Fields", f"{completed_required}/{len(REQUIRED_FIELDS)}")
        
        with col2:
            if profile.is_complete():
                if language == "he":
                    st.success("הפרופיל הושלם!")
                else:
                    st.success("Profile Complete!")
    
    def _check_backend_connection(self) -> bool:
        """Check backend connection and show status"""
        from components.api_client import test_backend_connection
        
        if not test_backend_connection():
            language = self.session_manager.get_language()
            messages = MESSAGES[language]
            
            st.error(messages["backend_error"])
            
            if st.button("🔄 Retry Connection" if language == "en" else "🔄 נסה שוב"):
                st.rerun()
            
            return False
        
        return True
    
    def _render_collection_interface(self):
        """Render the main collection interface"""
        language = self.session_manager.get_language()
        
        # Check if we need to start or continue collection
        last_question = self.session_manager.get_last_llm_question()
        
        # If we lost the last question but the user already has progress,
        # proactively fetch the next question to avoid showing the start screen again
        profile = self.session_manager.get_user_profile()
        try:
            progress_pct = profile.get_completion_percentage()
        except Exception:
            progress_pct = 0
        
        if not last_question and progress_pct > 0:
            # Ask backend for the next missing field without requiring the user to click Start again
            success, response = send_profile_collection_request("", profile.to_dict())
            if success:
                updated_profile = response.get("user_profile", {})
                if updated_profile:
                    self.session_manager.update_user_profile(updated_profile)
                llm_question = response.get("next_question", "")
                if llm_question:
                    self.session_manager.set_last_llm_question(llm_question)
                    last_question = llm_question
            # even if it fails, continue with default flow
        
        if not last_question:
            # Start collection process
            self._start_collection()
        else:
            # Continue with existing question
            self._continue_collection(last_question)
    
    def _start_collection(self):
        """Start the profile collection process"""
        language = self.session_manager.get_language()

        # If the user already made progress, skip the start panel and
        # immediately fetch/continue with the next question to avoid resets.
        profile = self.session_manager.get_user_profile()
        try:
            progress_pct = profile.get_completion_percentage()
        except Exception:
            progress_pct = 0
        if progress_pct > 0:
            success, response = send_profile_collection_request("", profile.to_dict())
            if success:
                updated_profile = response.get("user_profile", {})
                if updated_profile:
                    self.session_manager.update_user_profile(updated_profile)
                llm_question = response.get("next_question", "")
                if llm_question:
                    self.session_manager.set_last_llm_question(llm_question)
                    self._continue_collection(llm_question)
                    return
        
        if language == "he":
            welcome_msg = "🏥 ברוכים הבאים למערכת הבריאות החכמה!"
            subtitle_msg = "המערכת תעזור לך להירשם ולקבל מידע רפואי מותאם אישית"
            instruction_msg = "👇 לחץ על הכפתור כדי להתחיל"
            start_text = "🚀 התחל רישום"
        else:
            welcome_msg = "🏥 Welcome to the Smart Health System!"
            subtitle_msg = "This system will help you register and get personalized medical information"
            instruction_msg = "👇 Click the button below to get started"
            start_text = "🚀 Let's start"
        
        # Welcome section
        st.markdown(f"### {welcome_msg}")
        st.markdown(f"*{subtitle_msg}*")
        st.markdown("---")
        
        # Big, obvious instruction
        if language == "he":
            st.markdown(f'<h2 style="text-align: center; direction: rtl;">{instruction_msg}</h2>', unsafe_allow_html=True)
        else:
            st.markdown(f'<h2 style="text-align: center;">{instruction_msg}</h2>', unsafe_allow_html=True)
        
        # Centered, large button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(start_text, key="start_registration", type="primary", use_container_width=True):
                # Send initial request to backend
                initial_input = "Hi, I want to register" if language == "en" else "שלום, אני רוצה להירשם"
                self._process_user_input(initial_input)
        
        # Additional info
        st.markdown("---")
        if language == "he":
            st.info("💡 המערכת תשאל אותך שאלות כדי לאסוף את הפרטים הנחוצים לרישום", icon="ℹ️")
        else:
            st.info("💡 The system will ask you questions to collect the necessary information for registration", icon="ℹ️")
    
    def _continue_collection(self, llm_question: str):
        """Continue collection with existing LLM question"""
        language = self.session_manager.get_language()
        
        # Display current LLM question in a chat-like format
        with st.chat_message("assistant"):
            st.write(wrap_rtl_content(llm_question) if is_rtl_text(llm_question) else llm_question, 
                    unsafe_allow_html=True)
        
        # User input - use chat_input for better UX
        if language == "he":
            placeholder = "הקלד את תגובתך כאן..."
        else:
            placeholder = "Type your response here..."
        
        user_input = st.chat_input(placeholder)
        
        if user_input and user_input.strip():
            # Show user message
            with st.chat_message("user"):
                st.write(user_input)
            
            # Process the input
            self._process_user_input(user_input.strip())
        
        # Show profile completion status
        profile = self.session_manager.get_user_profile()
        if profile.is_complete():
            self._render_completion_options()
    
    def _process_user_input(self, user_input: str):
        """Process user input through backend"""
        profile = self.session_manager.get_user_profile()
        
        # Debug: Show what we're sending
        if self.session_manager.get_debug_mode():
            st.write("**Debug - Sending to backend:**")
            st.write(f"User input: {user_input}")
            st.write(f"Profile: {profile.to_dict()}")
        
        with st.spinner("Processing..." if self.session_manager.get_language() == "en" else "מעבד..."):
            success, response = send_profile_collection_request(user_input, profile.to_dict())
            
            # Debug: Show response
            if self.session_manager.get_debug_mode():
                st.write("**Debug - Backend response:**")
                st.write(f"Success: {success}")
                st.json(response)
            
            if success:
                # Update profile with the returned user_profile from backend
                updated_profile = response.get("user_profile", {})
                if updated_profile:
                    self.session_manager.update_user_profile(updated_profile)
                
                # Update LLM question for next interaction
                llm_question = response.get("next_question", "")
                self.session_manager.set_last_llm_question(llm_question)
                
                # Check if collection is complete (when status is "complete" or profile is confirmed)
                status = response.get("status", "")
                if status == "complete" or updated_profile.get("confirmed", False):
                    self._handle_collection_complete()
                
                st.rerun()
            
            else:
                # Handle API error
                from components.api_client import api_client
                error_msg = api_client.handle_api_error(response, self.session_manager.get_language())
                st.error(error_msg)
                
                # Show debug info if available
                if self.session_manager.get_debug_mode():
                    st.write("**Debug - Error Details:**")
                    st.json(response)
    
    def _handle_collection_complete(self):
        """Handle completion of profile collection"""
        language = self.session_manager.get_language()
        
        if language == "he":
            st.success("איסוף הפרטים הושלם בהצלחה!")
        else:
            st.success("Profile collection completed successfully!")
        
        # Clear the LLM question to show completion state
        self.session_manager.set_last_llm_question("")
    
    def _render_completion_options(self):
        """Render options when profile collection is complete"""
        language = self.session_manager.get_language()
        messages = MESSAGES[language]
        
        st.divider()
        
        if language == "he":
            st.write("**הפרופיל שלך הושלם! מה תרצה לעשות עכשיו?**")
        else:
            st.write("**Your profile is complete! What would you like to do now?**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(messages["start_chat"]):
                if self.session_manager.transition_to_chat():
                    st.rerun()
        
        with col2:
            if language == "he":
                review_text = "סקור פרטים"
            else:
                review_text = "Review Details"
            
            if st.button(review_text):
                st.session_state.show_profile_summary = True
                st.rerun()
        
        with col3:
            if language == "he":
                edit_text = "ערוך פרטים"
            else:
                edit_text = "Edit Details"
            
            if st.button(edit_text):
                self._render_manual_edit_form()
    
    def _render_profile_summary(self):
        """Render profile summary in sidebar"""
        with st.sidebar:
            language = self.session_manager.get_language()
            
            if language == "he":
                st.subheader("סיכום פרופיל")
            else:
                st.subheader("Profile Summary")
            
            profile = self.session_manager.get_user_profile()
            profile_display = format_profile_display(profile.to_dict(), language)
            
            if profile_display:
                st.markdown(profile_display)
            else:
                if language == "he":
                    st.write("אין פרטים עדיין")
                else:
                    st.write("No details yet")
            
            # Debug information
            if self.session_manager.get_debug_mode():
                st.divider()
                st.subheader("Debug Info")
                debug_data = self.session_manager.export_session_data()
                st.json(debug_data)
    
    def _render_manual_edit_form(self):
        """Render manual profile editing form"""
        language = self.session_manager.get_language()
        
        st.divider()
        
        if language == "he":
            st.subheader("עריכת פרטים ידנית")
        else:
            st.subheader("Manual Profile Editing")
        
        profile = self.session_manager.get_user_profile()
        
        with st.form("manual_edit_form"):
            # Create input fields for all profile fields
            updated_data = {}
            
            field_labels = {
                "first_name": "שם פרטי" if language == "he" else "First Name",
                "last_name": "שם משפחה" if language == "he" else "Last Name",
                "id_number": "תעודת זהות" if language == "he" else "ID Number",
                "gender": "מין" if language == "he" else "Gender",
                "age": "גיל" if language == "he" else "Age",
                "hmo": "קופת חולים" if language == "he" else "HMO",
                "hmo_card_number": "מספר כרטיס" if language == "he" else "Card Number",
                "membership_tier": "דרגת חברות" if language == "he" else "Membership Tier",
                "phone_number": "טלפון" if language == "he" else "Phone",
                "email": "אימייל" if language == "he" else "Email"
            }
            
            # Create text inputs for fields that should be text inputs
            text_input_fields = ["first_name", "last_name", "id_number", "age", "hmo_card_number", "phone_number", "email"]
            
            for field in text_input_fields:
                if field in field_labels:
                    current_value = getattr(profile, field, "")
                    updated_data[field] = st.text_input(field_labels[field], value=current_value, key=f"edit_{field}")
            
            # Gender selection
            gender_options = ["זכר", "נקבה"] if language == "he" else ["Male", "Female"]
            current_gender = getattr(profile, "gender", "")
            
            # Map current gender to display options
            gender_mapping = {
                "Male": "זכר" if language == "he" else "Male",
                "Female": "נקבה" if language == "he" else "Female",
                "זכר": "זכר" if language == "he" else "Male",
                "נקבה": "נקבה" if language == "he" else "Female"
            }
            
            # Find the display value for current gender
            display_gender = gender_mapping.get(current_gender, current_gender)
            
            if display_gender in gender_options:
                gender_index = gender_options.index(display_gender)
            else:
                gender_index = 0
            
            selected_gender = st.selectbox(
                field_labels["gender"], 
                gender_options, 
                index=gender_index,
                key="edit_gender_select"
            )
            
            # Map selected gender back to internal format
            reverse_mapping = {
                "זכר": "Male",
                "נקבה": "Female",
                "Male": "Male",
                "Female": "Female"
            }
            updated_data["gender"] = reverse_mapping.get(selected_gender, selected_gender)
            
            # HMO selection
            hmo_options = ["כללית", "מכבי", "מאוחדת", "לאומית"] if language == "he" else ["Clalit", "Maccabi", "Meuhedet", "Leumit"]
            current_hmo = getattr(profile, "hmo", "")
            
            # Map current HMO to display options
            hmo_mapping = {
                "כללית": "כללית" if language == "he" else "Clalit",
                "מכבי": "מכבי" if language == "he" else "Maccabi",
                "מאוחדת": "מאוחדת" if language == "he" else "Meuhedet",
                "לאומית": "לאומית" if language == "he" else "Leumit",
                "Clalit": "כללית" if language == "he" else "Clalit",
                "Maccabi": "מכבי" if language == "he" else "Maccabi",
                "Meuhedet": "מאוחדת" if language == "he" else "Meuhedet",
                "Leumit": "לאומית" if language == "he" else "Leumit"
            }
            
            display_hmo = hmo_mapping.get(current_hmo, current_hmo)
            
            if display_hmo in hmo_options:
                hmo_index = hmo_options.index(display_hmo)
            else:
                hmo_index = 0
            
            selected_hmo = st.selectbox(
                field_labels["hmo"],
                hmo_options,
                index=hmo_index,
                key="edit_hmo_select"
            )
            
            # Map selected HMO back to internal format
            hmo_reverse_mapping = {
                "כללית": "כללית",
                "מכבי": "מכבי", 
                "מאוחדת": "מאוחדת",
                "לאומית": "לאומית",
                "Clalit": "כללית",
                "Maccabi": "מכבי",
                "Meuhedet": "מאוחדת",
                "Leumit": "לאומית"
            }
            updated_data["hmo"] = hmo_reverse_mapping.get(selected_hmo, selected_hmo)
            
            # Membership tier selection
            tier_options = ["זהב", "כסף", "ארד"] if language == "he" else ["Gold", "Silver", "Bronze"]
            current_tier = getattr(profile, "membership_tier", "")
            
            # Map current tier to display options
            tier_mapping = {
                "זהב": "זהב" if language == "he" else "Gold",
                "כסף": "כסף" if language == "he" else "Silver", 
                "ארד": "ארד" if language == "he" else "Bronze",
                "Gold": "זהב" if language == "he" else "Gold",
                "Silver": "כסף" if language == "he" else "Silver",
                "Bronze": "ארד" if language == "he" else "Bronze"
            }
            
            display_tier = tier_mapping.get(current_tier, current_tier)
            
            if display_tier in tier_options:
                tier_index = tier_options.index(display_tier)
            else:
                tier_index = 0
            
            selected_tier = st.selectbox(
                field_labels["membership_tier"],
                tier_options,
                index=tier_index,
                key="edit_tier_select"
            )
            
            # Map selected tier back to internal format
            tier_reverse_mapping = {
                "זהב": "זהב",
                "כסף": "כסף",
                "ארד": "ארד",
                "Gold": "זהב",
                "Silver": "כסף", 
                "Bronze": "ארד"
            }
            updated_data["membership_tier"] = tier_reverse_mapping.get(selected_tier, selected_tier)
            
            # Submit button
            submit_text = "שמור שינויים" if language == "he" else "Save Changes"
            
            if st.form_submit_button(submit_text, use_container_width=True):
                # Debug: Show what data is being submitted (only in debug mode)
                if self.session_manager.get_debug_mode():
                    st.write("**Debug - Updated Data:**")
                    st.json(updated_data)
                
                # Validate the updated data
                is_valid, errors = validate_complete_profile(updated_data)
                
                if is_valid:
                    # Update profile
                    self.session_manager.update_user_profile(updated_data)
                    
                    success_msg = "הפרטים עודכנו בהצלחה!" if language == "he" else "Profile updated successfully!"
                    st.success(success_msg)
                    
                    # Force a rerun
                    st.rerun()
                else:
                    # Show validation errors
                    error_display = format_validation_errors(errors, language)
                    st.error(error_display)
