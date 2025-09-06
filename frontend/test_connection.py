#!/usr/bin/env python3
"""
Test script to verify frontend can connect to backend
"""
import requests
import json
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import BACKEND_BASE_URL, ENDPOINTS

def test_backend_connection():
    """Test connection to backend"""
    print("🔍 Testing Backend Connection")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_BASE_URL}")
    print()
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{BACKEND_BASE_URL}{ENDPOINTS['health']}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to backend at {BACKEND_BASE_URL}")
        print(f"   Make sure backend is running: uvicorn app.main:app --reload --port 8001")
        return False
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
        return False
    
    # Test 2: KB Stats
    print("\n2. Testing KB Stats...")
    try:
        response = requests.get(f"{BACKEND_BASE_URL}{ENDPOINTS['kb_stats']}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"   ⚠️  KB not initialized: {data['error']}")
            else:
                print(f"   ✅ KB Stats successful")
                print(f"   Total chunks: {data.get('total_chunks', 0)}")
        else:
            print(f"   ❌ KB Stats failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ KB Stats error: {str(e)}")
    
    # Test 3: Profile Collection
    print("\n3. Testing Profile Collection...")
    try:
        test_payload = {
            "message": "Hi, I want to register",
            "user_profile": {}
        }
        response = requests.post(
            f"{BACKEND_BASE_URL}{ENDPOINTS['collect_user_info']}", 
            json=test_payload, 
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Profile collection successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            if data.get('next_question'):
                print(f"   Next question: {data['next_question'][:100]}...")
        else:
            print(f"   ❌ Profile collection failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Profile collection error: {str(e)}")
    
    # Test 4: Chat (with confirmed profile)
    print("\n4. Testing Chat...")
    try:
        test_payload = {
            "message": "What services are available?",
            "user_profile": {
                "first_name": "Test",
                "last_name": "User", 
                "hmo": "כללית",
                "membership_tier": "כסף",
                "confirmed": True
            },
            "history": []
        }
        response = requests.post(
            f"{BACKEND_BASE_URL}{ENDPOINTS['chat']}", 
            json=test_payload, 
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Chat successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            if data.get('answer'):
                print(f"   Answer: {data['answer'][:100]}...")
            print(f"   Sources: {len(data.get('sources', []))}")
        else:
            print(f"   ❌ Chat failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Chat error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Connection test completed!")
    print("\nTo start the frontend:")
    print("  cd frontend")
    print("  streamlit run streamlit_app.py")
    print("\nThe frontend will be available at: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    test_backend_connection()
