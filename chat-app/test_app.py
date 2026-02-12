#!/usr/bin/env python3
"""
Test script for the AI Chat Application
Tests basic functionality, authentication, and connectivity
Updated for authentication-enabled version
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   AWS Connected: {data.get('aws_connected')}")
            print(f"   LaunchDarkly Connected: {data.get('launchdarkly_connected')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_unauthenticated_redirect():
    """Test that unauthenticated requests to main page redirect to login"""
    try:
        response = requests.get('http://localhost:5001/', timeout=10)
        if response.status_code == 200:
            # Check if we got the login page
            if 'login' in response.text.lower() and 'user id' in response.text.lower():
                print("✅ Unauthenticated access correctly shows login page")
                return True
            else:
                print("❌ Expected login page but got different content")
                return False
        else:
            print(f"❌ Main page returned unexpected status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Main page test failed: {e}")
        return False

def test_login_endpoint():
    """Test the login endpoint with valid credentials"""
    try:
        # Create session to maintain cookies
        session = requests.Session()
        
        # Sample browser details
        browser_details = {
            "userAgent": "Mozilla/5.0 (Test Browser)",
            "platform": "Test Platform",
            "language": "en-US",
            "screenResolution": "1920x1080",
            "timezone": "America/New_York",
            "viewport": "1200x800",
            "deviceType": "Desktop",
            "browserName": "Test Browser",
            "browserVersion": "1.0.0"
        }
        
        login_data = {
            "userId": "testuser123",
            "browserDetails": browser_details
        }
        
        response = session.post(
            'http://localhost:5001/api/login',
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login endpoint test passed")
            print(f"   Status: {data.get('status')}")
            print(f"   User ID: {data.get('userId')}")
            return session  # Return session for subsequent tests
        else:
            print(f"❌ Login endpoint test failed with status {response.status_code}")
            print(f"   Error: {response.json().get('error', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Login endpoint test failed: {e}")
        return None

def test_login_validation():
    """Test login validation with invalid data"""
    try:
        # Test empty user ID
        response = requests.post(
            'http://localhost:5001/api/login',
            json={"userId": "", "browserDetails": {}},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Login validation correctly rejects empty user ID")
        else:
            print(f"❌ Expected 400 for empty user ID, got {response.status_code}")
            return False
        
        # Test invalid characters
        response = requests.post(
            'http://localhost:5001/api/login',
            json={"userId": "test@user!", "browserDetails": {}},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Login validation correctly rejects invalid characters")
            return True
        else:
            print(f"❌ Expected 400 for invalid characters, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login validation test failed: {e}")
        return False

def test_authenticated_chat_endpoint(session):
    """Test the chat endpoint with an authenticated session"""
    if not session:
        print("❌ No authenticated session available for chat test")
        return False
        
    try:
        test_message = "Hello! This is a test message from an authenticated user."
        response = session.post(
            'http://localhost:5001/api/chat',
            json={'message': test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Authenticated chat endpoint test passed")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Chat endpoint test failed with status {response.status_code}")
            print(f"   Error: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat endpoint test failed: {e}")
        return False

def test_unauthenticated_chat_endpoint():
    """Test that unauthenticated chat requests are rejected"""
    try:
        test_message = "This should be rejected"
        response = requests.post(
            'http://localhost:5001/api/chat',
            json={'message': test_message},
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ Unauthenticated chat correctly rejected")
            return True
        else:
            print(f"❌ Expected 401 for unauthenticated chat, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Unauthenticated chat test failed: {e}")
        return False

def test_authenticated_clear_endpoint(session):
    """Test the clear chat endpoint with authenticated session"""
    if not session:
        print("❌ No authenticated session available for clear test")
        return False
        
    try:
        response = session.post('http://localhost:5001/api/clear', timeout=10)
        if response.status_code == 200:
            print("✅ Authenticated clear chat endpoint test passed")
            return True
        else:
            print(f"❌ Clear chat endpoint test failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Clear chat endpoint test failed: {e}")
        return False

def test_unauthenticated_clear_endpoint():
    """Test that unauthenticated clear requests are rejected"""
    try:
        response = requests.post('http://localhost:5001/api/clear', timeout=10)
        if response.status_code == 401:
            print("✅ Unauthenticated clear correctly rejected")
            return True
        else:
            print(f"❌ Expected 401 for unauthenticated clear, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Unauthenticated clear test failed: {e}")
        return False

def test_authenticated_debug_endpoint(session):
    """Test the debug endpoint with authenticated session"""
    if not session:
        print("❌ No authenticated session available for debug test")
        return False
        
    try:
        response = session.get('http://localhost:5001/api/debug', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Authenticated debug endpoint test passed")
            print(f"   User Context Key: {data.get('user_context', {}).get('key', 'N/A')}")
            return True
        else:
            print(f"❌ Debug endpoint test failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Debug endpoint test failed: {e}")
        return False

def test_unauthenticated_debug_endpoint():
    """Test that unauthenticated debug requests are rejected"""
    try:
        response = requests.get('http://localhost:5001/api/debug', timeout=10)
        if response.status_code == 401:
            print("✅ Unauthenticated debug correctly rejected")
            return True
        else:
            print(f"❌ Expected 401 for unauthenticated debug, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Unauthenticated debug test failed: {e}")
        return False

def test_logout_endpoint(session):
    """Test the logout endpoint"""
    if not session:
        print("❌ No authenticated session available for logout test")
        return False
        
    try:
        response = session.post('http://localhost:5001/api/logout', timeout=10)
        if response.status_code == 200:
            print("✅ Logout endpoint test passed")
            return True
        else:
            print(f"❌ Logout endpoint test failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Logout endpoint test failed: {e}")
        return False

def test_static_files():
    """Test that static files are accessible"""
    static_files = [
        'http://localhost:5001/static/css/style.css',
        'http://localhost:5001/static/js/chat.js'
    ]
    
    all_passed = True
    for url in static_files:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Static file accessible: {url.split('/')[-1]}")
            else:
                print(f"❌ Static file not accessible: {url.split('/')[-1]} (status {response.status_code})")
                all_passed = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Static file test failed for {url.split('/')[-1]}: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🧪 Running AI Chat Application Tests (Authentication-Enabled Version)")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Note: Application now requires user authentication")
    print()
    
    # Check if server is running
    print("🔍 Checking if application is running on port 5001...")
    
    # Track authenticated session
    authenticated_session = None
    
    tests = [
        ("Health Endpoint", lambda: test_health_endpoint()),
        ("Unauthenticated Main Page (Login Redirect)", lambda: test_unauthenticated_redirect()),
        ("Static Files", lambda: test_static_files()),
        ("Login Validation", lambda: test_login_validation()),
        ("User Login", lambda: test_login_endpoint()),
        ("Unauthenticated Chat Rejection", lambda: test_unauthenticated_chat_endpoint()),
        ("Unauthenticated Clear Rejection", lambda: test_unauthenticated_clear_endpoint()),
        ("Unauthenticated Debug Rejection", lambda: test_unauthenticated_debug_endpoint()),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        result = test_func()
        if result:
            passed += 1
            # Special case: store session from login test
            if test_name == "User Login" and result != True:
                authenticated_session = result
        else:
            print(f"   Test failed: {test_name}")
    
    # Run authenticated tests if we have a session
    if authenticated_session:
        print("\n" + "=" * 50)
        print("🔐 Running Authenticated Tests...")
        
        auth_tests = [
            ("Authenticated Chat", lambda: test_authenticated_chat_endpoint(authenticated_session)),
            ("Authenticated Clear", lambda: test_authenticated_clear_endpoint(authenticated_session)),
            ("Authenticated Debug", lambda: test_authenticated_debug_endpoint(authenticated_session)),
            ("Logout", lambda: test_logout_endpoint(authenticated_session)),
        ]
        
        for test_name, test_func in auth_tests:
            print(f"\n🧪 Testing {test_name}...")
            if test_func():
                passed += 1
            else:
                print(f"   Test failed: {test_name}")
        
        total += len(auth_tests)
    else:
        print("\n⚠️  Skipping authenticated tests - no valid session obtained")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The authentication-enabled application is working correctly.")
        print("✅ Authentication system is functioning properly")
        print("✅ User context collection is working")
        print("✅ Session management is secure")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the application configuration.")
        print("💡 Common issues:")
        print("   - Check if the application is running on port 5001 (not 5000)")
        print("   - Verify AWS credentials are properly configured")
        print("   - Ensure LaunchDarkly SDK key is set")
        print("   - Check that authentication system is properly initialized")
        sys.exit(1)

if __name__ == "__main__":
    main()