"""
Phase 2: Medical Q&A chat interface
"""
import streamlit as st
from typing import Dict, Any, List
from components.session_manager import SessionManager, ChatMessage
from components.api_client import send_chat_request
from utils.formatters import format_profile_display, format_debug_info, truncate_text
from utils.hebrew_support import wrap_rtl_content, is_rtl_text, format_chat_bubble_rtl
from config.settings import MESSAGES

class ChatInterface:
    """Handle medical Q&A chat workflow"""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    def render(self):
        """Render the chat interface"""
        language = self.session_manager.get_language()
        messages = MESSAGES[language]
        
        # Header
        st.title(messages["chat_phase"])
        
        # Profile welcome message
        if st.session_state.get("show_profile_summary", False):
            self._render_welcome_message()
        
        # Backend status check
        if not self._check_backend_connection():
            return
        
        # Chat container
        self._render_chat_container()
        
        # Chat input
        self._render_chat_input()
        
        # Sidebar with profile and controls
        self._render_sidebar()
    
    def _render_welcome_message(self):
        """Display welcome message with profile summary"""
        language = self.session_manager.get_language()
        profile = self.session_manager.get_user_profile()
        
        if language == "he":
            welcome_text = f"שלום {profile.first_name}! אני כאן לעזור לך עם שאלות רפואיות בהתבסס על הפרופיל שלך."
        else:
            welcome_text = f"Hello {profile.first_name}! I'm here to help you with medical questions based on your profile."
        
        if is_rtl_text(welcome_text):
            st.markdown(wrap_rtl_content(welcome_text), unsafe_allow_html=True)
        else:
            st.info(welcome_text, icon="👋")
        
        # Show profile summary
        with st.expander("Profile Summary" if language == "en" else "סיכום פרופיל"):
            profile_display = format_profile_display(profile.to_dict(), language)
            st.markdown(profile_display)
        
        # Mark as shown
        st.session_state.show_profile_summary = False
    
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
    
    def _render_chat_container(self):
        """Render the main chat conversation"""
        conversation = self.session_manager.get_conversation_history()
        
        # Create chat container
        chat_container = st.container()
        
        with chat_container:
            if not conversation:
                # Show initial message
                language = self.session_manager.get_language()
                
                if language == "he":
                    initial_msg = "שאל אותי כל שאלה רפואית והיא תענה בהתבסס על הפרופיל שלך"
                else:
                    initial_msg = "Ask me any medical question and I'll answer based on your profile and my medical knowledge."
                
                with st.chat_message("assistant"):
                    st.write(wrap_rtl_content(initial_msg) if is_rtl_text(initial_msg) else initial_msg,
                            unsafe_allow_html=True)
            
            else:
                # Display conversation history
                for message in conversation:
                    self._render_chat_message(message)
    
    def _render_chat_message(self, message: ChatMessage):
        """Render individual chat message"""
        if message.is_user:
            with st.chat_message("user"):
                content = message.content
                if is_rtl_text(content):
                    st.markdown(wrap_rtl_content(content), unsafe_allow_html=True)
                else:
                    st.write(content)
        
        else:
            with st.chat_message("assistant"):
                content = message.content
                if is_rtl_text(content):
                    st.markdown(wrap_rtl_content(content), unsafe_allow_html=True)
                else:
                    st.write(content)
                
                # Show sources if available
                if message.sources:
                    self._render_sources(message.sources)
                
                # Show debug info if enabled
                if self.session_manager.get_debug_mode() and message.debug_info:
                    self._render_debug_info(message.debug_info)
    
    def _render_sources(self, sources: List[str]):
        """Render source information"""
        language = self.session_manager.get_language()
        
        if sources:
            if language == "he":
                st.caption("מקורות:")
            else:
                st.caption("Sources:")
            
            for i, source in enumerate(sources, 1):
                st.caption(f"{i}. {truncate_text(source, 80)}")
    
    def _render_debug_info(self, debug_info: Dict[str, Any]):
        """Render debug information"""
        with st.expander("🔧 Debug Info"):
            formatted_debug = format_debug_info(debug_info)
            st.text(formatted_debug)
    
    def _render_chat_input(self):
        """Render chat input field"""
        language = self.session_manager.get_language()
        
        # Chat input
        if language == "he":
            placeholder = "שאל שאלה רפואית..."
        else:
            placeholder = "Ask a medical question..."
        
        user_input = st.chat_input(placeholder)
        
        if user_input:
            self._process_chat_message(user_input)
    
    def _process_chat_message(self, user_input: str):
        """Process user chat message"""
        # Add user message to conversation
        self.session_manager.add_chat_message(user_input, is_user=True)
        
        # Get profile and conversation history
        profile = self.session_manager.get_user_profile()
        conversation = self.session_manager.get_conversation_history()
        
        # Convert conversation to format expected by backend
        conversation_history = []
        for msg in conversation[:-1]:  # Exclude the current message
            if msg.is_user:
                conversation_history.append({
                    "user": msg.content,
                    "assistant": ""
                })
            else:
                # If it's an assistant message, add it to the last exchange
                if conversation_history and "assistant" in conversation_history[-1]:
                    conversation_history[-1]["assistant"] = msg.content
                else:
                    conversation_history.append({
                        "user": "",
                        "assistant": msg.content
                    })
        
        # Show user message immediately
        with st.chat_message("user"):
            if is_rtl_text(user_input):
                st.markdown(wrap_rtl_content(user_input), unsafe_allow_html=True)
            else:
                st.write(user_input)
        
        # Process with backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..." if self.session_manager.get_language() == "en" else "חושב..."):
                success, response = send_chat_request(
                    user_input, 
                    profile.to_dict(), 
                    conversation_history
                )
                
                if success:
                    # Extract response data (backend returns "answer" not "response")
                    bot_response = response.get("answer", "")
                    sources = response.get("sources", [])
                    retrieved_chunks = response.get("retrieved_chunks", [])
                    context_used = response.get("context_used", False)
                    status = response.get("status", "answered")
                    
                    # Handle non-standard statuses explicitly so the UI doesn't look frozen
                    if status != "answered":
                        lang = self.session_manager.get_language()
                        if status == "registration_required":
                            msg = (
                                "Please complete your registration first in the previous step."
                                if lang == "en"
                                else "יש להשלים את תהליך הרישום לפני תחילת הצ'אט."
                            )
                            st.warning(msg)
                            # Offer navigation back to profile collection
                            back_text = "Back to Profile" if lang == "en" else "חזרה לפרופיל"
                            if st.button(back_text, key="back_to_profile_from_chat_warning"):
                                self.session_manager.set_phase("profile_collection")
                                st.rerun()
                        elif status == "no_match":
                            msg = (
                                "I couldn't find a relevant answer in the knowledge base. Try rephrasing or adding details."
                                if lang == "en"
                                else "לא נמצא מענה רלוונטי במאגר הידע. נסו לנסח מחדש או להוסיף פרטים."
                            )
                            st.info(msg)
                        else:
                            # Fallback informative message
                            msg = (
                                "I'm having trouble answering right now. Please try again."
                                if lang == "en"
                                else "מתקשה לענות כרגע. נסו שוב."
                            )
                            st.info(msg)
                        # Record the system message in the conversation for completeness
                        self.session_manager.add_chat_message(msg, is_user=False)
                        return
                    
                    # Display response
                    if is_rtl_text(bot_response):
                        st.markdown(wrap_rtl_content(bot_response), unsafe_allow_html=True)
                    else:
                        st.write(bot_response)
                    
                    # Show sources
                    if sources:
                        self._render_sources(sources)
                    
                    # Prepare debug info
                    debug_info = {
                        "retrieved_chunks_count": len(retrieved_chunks),
                        "context_used": context_used,
                        "sources_count": len(sources),
                        "status": status
                    }
                    
                    if self.session_manager.get_debug_mode():
                        debug_info["retrieved_chunks"] = retrieved_chunks
                        self._render_debug_info(debug_info)
                    
                    # Add bot message to conversation
                    self.session_manager.add_chat_message(
                        bot_response, 
                        is_user=False, 
                        sources=sources,
                        debug_info=debug_info
                    )
                
                else:
                    # Handle API error
                    from components.api_client import api_client
                    error_msg = api_client.handle_api_error(response, self.session_manager.get_language())
                    
                    st.error(error_msg)
                    
                    # Add error message to conversation
                    self.session_manager.add_chat_message(
                        f"Error: {error_msg}", 
                        is_user=False
                    )
        
        # Rerun to update the interface
        st.rerun()
    
    def _render_sidebar(self):
        """Render sidebar with profile and controls"""
        with st.sidebar:
            language = self.session_manager.get_language()
            
            # Profile summary
            if language == "he":
                st.subheader("פרופיל משתמש")
            else:
                st.subheader("User Profile")
            
            profile = self.session_manager.get_user_profile()
            profile_display = format_profile_display(profile.to_dict(), language)
            st.markdown(profile_display)
            
            st.divider()
            
            # Chat controls
            if language == "he":
                st.subheader("בקרות צ'אט")
            else:
                st.subheader("Chat Controls")
            
            # Clear conversation button
            clear_text = "נקה שיחה" if language == "he" else "Clear Chat"
            if st.button(clear_text):
                self.session_manager.clear_conversation()
                st.rerun()
            
            # Back to profile button
            back_text = "חזור לפרופיל" if language == "he" else "Back to Profile"
            if st.button(back_text):
                self.session_manager.set_phase("profile_collection")
                st.rerun()
            
            # Language toggle
            from utils.hebrew_support import get_language_toggle_text
            toggle_text = get_language_toggle_text(language)
            if st.button(f"🌐 {toggle_text}"):
                self.session_manager.toggle_language()
                st.rerun()
            
            # Debug mode toggle
            debug_text = "מצב דיבוג" if language == "he" else "Debug Mode"
            debug_enabled = st.checkbox(debug_text, value=self.session_manager.get_debug_mode())
            if debug_enabled != self.session_manager.get_debug_mode():
                self.session_manager.toggle_debug_mode()
                st.rerun()
            
            # Conversation stats
            if self.session_manager.get_debug_mode():
                st.divider()
                st.subheader("Stats")
                conversation = self.session_manager.get_conversation_history()
                st.metric("Messages", len(conversation))
                
                user_messages = sum(1 for msg in conversation if msg.is_user)
                bot_messages = len(conversation) - user_messages
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("User", user_messages)
                with col2:
                    st.metric("Bot", bot_messages)
            
            # Backend status
            st.divider()
            backend_status = self.session_manager.get_backend_status()
            
            if backend_status is True:
                st.success("Backend Connected" if language == "en" else "שרת מחובר")
            elif backend_status is False:
                st.error("Backend Disconnected" if language == "en" else "שרת מנותק")
            else:
                st.warning("Backend Status Unknown" if language == "en" else "סטטוס שרת לא ידוע")
