#!/usr/bin/env python3
"""
Test script for the AI Chat Application
Tests basic functionality and connectivity
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=10)
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

def test_chat_endpoint():
    """Test the chat endpoint with a simple message"""
    try:
        test_message = "Hello! This is a test message."
        response = requests.post(
            'http://localhost:5000/api/chat',
            json={'message': test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint test passed")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Chat endpoint test failed with status {response.status_code}")
            print(f"   Error: {response.json().get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat endpoint test failed: {e}")
        return False

def test_clear_endpoint():
    """Test the clear chat endpoint"""
    try:
        response = requests.post('http://localhost:5000/api/clear', timeout=10)
        if response.status_code == 200:
            print("✅ Clear chat endpoint test passed")
            return True
        else:
            print(f"❌ Clear chat endpoint test failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Clear chat endpoint test failed: {e}")
        return False

def test_static_files():
    """Test that static files are accessible"""
    static_files = [
        'http://localhost:5000/static/css/style.css',
        'http://localhost:5000/static/js/chat.js'
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

def test_main_page():
    """Test that the main page loads"""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            return True
        else:
            print(f"❌ Main page failed to load (status {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Main page test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running AI Chat Application Tests")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if server is running
    print("🔍 Checking if application is running...")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Main Page", test_main_page),
        ("Static Files", test_static_files),
        ("Clear Chat Endpoint", test_clear_endpoint),
        ("Chat Endpoint", test_chat_endpoint),  # This one last as it might take longer
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the application configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()