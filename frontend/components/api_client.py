"""
Backend API communication client
"""
import requests
import streamlit as st
from typing import Dict, Any, Optional, Tuple
import time
import json
from config.settings import ENDPOINTS
from components.session_manager import SessionManager

class APIClient:
    """Handle all backend API communications"""
    
    def __init__(self):
        self.base_url = SessionManager.get_backend_url()
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                     params: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Make HTTP request with retry logic and error handling
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=params, timeout=self.timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, timeout=self.timeout)
                else:
                    return False, {"error": f"Unsupported HTTP method: {method}"}
                
                # Check if request was successful
                if response.status_code == 200:
                    try:
                        result = response.json()
                        SessionManager.set_backend_status(True)
                        return True, result
                    except json.JSONDecodeError:
                        return False, {"error": "Invalid JSON response from server"}
                
                elif response.status_code == 422:
                    # Validation error
                    try:
                        error_detail = response.json()
                        return False, {"error": "Validation error", "details": error_detail}
                    except json.JSONDecodeError:
                        return False, {"error": "Validation error (invalid response format)"}
                
                else:
                    return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    SessionManager.set_backend_status(False)
                    return False, {"error": "Cannot connect to backend server"}
                time.sleep(self.retry_delay * (attempt + 1))
            
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    return False, {"error": "Request timeout"}
                time.sleep(self.retry_delay * (attempt + 1))
            
            except requests.exceptions.RequestException as e:
                return False, {"error": f"Request failed: {str(e)}"}
        
        return False, {"error": "Max retries exceeded"}
    
    def check_backend_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if backend is healthy and responsive
        """
        return self._make_request("GET", ENDPOINTS["health"])
    
    def get_kb_stats(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Get knowledge base statistics
        """
        return self._make_request("GET", ENDPOINTS["kb_stats"])
    
    def send_profile_collection_request(self, user_input: str, 
                                      current_profile: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Send profile collection request to backend
        
        Expected response format:
        {
            "status": "in_progress",
            "next_question": "What is your first name?",
            "user_profile": {"first_name": "John", ...}
        }
        """
        # Convert current_profile dict to UserProfile structure if needed
        from components.session_manager import UserProfile
        if isinstance(current_profile, dict):
            # Create UserProfile object to ensure proper structure
            try:
                profile_obj = UserProfile(**current_profile)
                user_profile = profile_obj.to_dict()
            except Exception as e:
                # If conversion fails, use empty profile
                user_profile = UserProfile().to_dict()
        else:
            user_profile = UserProfile().to_dict()
        
        # Get current language preference
        from components.session_manager import SessionManager
        language = SessionManager.get_language()
        
        data = {
            "message": user_input,
            "user_profile": user_profile,
            "language": language
        }
        
        success, response = self._make_request("POST", ENDPOINTS["collect_user_info"], data)
        
        if success and SessionManager.get_debug_mode():
            st.write("**Debug - Profile Collection Response:**")
            st.json(response)
        
        return success, response
    
    def send_chat_request(self, user_question: str, 
                         user_profile: Dict[str, Any], 
                         conversation_history: list = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Send chat request to backend
        
        Expected response format:
        {
            "status": "answered",
            "answer": "Based on your profile...",
            "sources": ["document1.pdf", "guideline2.txt"],
            "retrieved_chunks": [...],
            "user_profile_used": {...},
            "context_used": true
        }
        """
        # Convert user_profile dict to UserProfile structure if needed
        from components.session_manager import UserProfile
        if isinstance(user_profile, dict):
            # Create UserProfile object to ensure proper structure
            profile_obj = UserProfile(**user_profile)
            user_profile = profile_obj.to_dict()
        
        # Pass current UI language to backend so answers are in the same language
        from components.session_manager import SessionManager
        language = SessionManager.get_language()
        data = {
            "message": user_question,
            "user_profile": user_profile,
            "history": conversation_history or [],
            "language": language
        }
        
        success, response = self._make_request("POST", ENDPOINTS["chat"], data)
        
        if success and SessionManager.get_debug_mode():
            st.write("**Debug - Chat Response:**")
            debug_info = {
                "response_length": len(response.get("response", "")),
                "sources_count": len(response.get("sources", [])),
                "chunks_count": len(response.get("retrieved_chunks", [])),
                "confidence": response.get("confidence", "N/A")
            }
            st.json(debug_info)
        
        return success, response
    
    def handle_api_error(self, error_data: Dict[str, Any], language: str = "he") -> str:
        """
        Format API error for user display
        """
        error_msg = error_data.get("error", "Unknown error")
        
        # Check for detailed error information
        if "details" in error_data:
            details = error_data["details"]
            if isinstance(details, dict) and "detail" in details:
                error_msg = f"{error_msg}: {details['detail']}"
        
        # Translate common errors
        if language == "he":
            error_translations = {
                "Cannot connect to backend server": "לא ניתן להתחבר לשרת",
                "Request timeout": "זמן הקשר פג", 
                "Validation error": "שגיאה בוולידציה",
                "Invalid JSON response from server": "תגובה לא תקינה מהשרת",
                "HTTP 422": "שגיאה בפורמט הבקשה"
            }
            
            for eng_error, he_error in error_translations.items():
                if eng_error in error_msg:
                    return f"{he_error}: {error_msg}"
        
        return error_msg
    
    def format_request_for_logging(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format request data for logging (remove sensitive info)
        """
        safe_data = data.copy()
        
        # Remove or mask sensitive fields
        sensitive_fields = ["id_number", "hmo_card_number", "phone_number"]
        for field in sensitive_fields:
            if field in safe_data:
                safe_data[field] = "***masked***"
        
        return {
            "endpoint": endpoint,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": safe_data
        }
    
    def test_connection(self) -> bool:
        """
        Test backend connection and update session state
        """
        success, response = self.check_backend_health()
        SessionManager.set_backend_status(success)
        return success

# Singleton instance
api_client = APIClient()

# Convenience functions
def send_profile_collection_request(user_input: str, current_profile: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Convenience function for profile collection"""
    return api_client.send_profile_collection_request(user_input, current_profile)

def send_chat_request(user_question: str, user_profile: Dict[str, Any], 
                     conversation_history: list = None) -> Tuple[bool, Dict[str, Any]]:
    """Convenience function for chat requests"""
    return api_client.send_chat_request(user_question, user_profile, conversation_history)

def check_backend_health() -> Tuple[bool, Dict[str, Any]]:
    """Convenience function for health check"""
    return api_client.check_backend_health()

def test_backend_connection() -> bool:
    """Convenience function to test connection"""
    return api_client.test_connection()
