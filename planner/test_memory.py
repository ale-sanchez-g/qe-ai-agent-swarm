#!/usr/bin/env python3
"""
Test script to verify memory management improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import ConversationMemory

def test_memory_management():
    """Test the memory management functionality"""
    print("Testing Memory Management...")
    
    # Create a test session
    memory = ConversationMemory("test_session_123", max_token_limit=4000)
    
    # Simulate a long conversation
    conversations = [
        ("Hello, I need help with my project", "Hello! I'd be happy to help with your project. What kind of project are you working on?"),
        ("It's a web application using FastAPI", "Great! FastAPI is an excellent choice for web applications. What specific aspect do you need help with?"),
        ("I'm having issues with database connections", "Database connection issues can be tricky. Are you using SQLAlchemy, or another ORM? What error messages are you seeing?"),
        ("I'm using SQLAlchemy and getting timeout errors", "Timeout errors with SQLAlchemy often relate to connection pool settings. Let me help you troubleshoot this."),
        ("The timeouts happen after 4 requests", "That's very specific! This suggests a connection pool exhaustion issue. Let's check your connection pool configuration."),
        ("How do I configure the connection pool?", "You can configure the connection pool in SQLAlchemy using parameters like pool_size, max_overflow, and pool_timeout."),
        ("What are good default values?", "Good defaults are pool_size=5, max_overflow=10, and pool_timeout=30. But let's see what you currently have set."),
        ("I don't have any pool settings configured", "That's likely the issue! Without explicit pool settings, SQLAlchemy uses defaults that might not work for your use case."),
    ]
    
    print(f"Simulating {len(conversations)} conversation exchanges...")
    
    for i, (user_msg, ai_msg) in enumerate(conversations, 1):
        print(f"\n--- Exchange {i} ---")
        memory.add_user_message(user_msg)
        memory.add_ai_message(ai_msg)
        
        # Test different context retrieval methods
        recent_5 = memory.get_recent_messages(5)
        recent_smart = memory.get_recent_messages_smart(10)
        full_context = memory.get_full_conversation_context()
        
        print(f"Recent 5 messages: {len(recent_5)} messages")
        print(f"Smart recent messages: {len(recent_smart)} messages")
        print(f"Full context length: {len(full_context)} characters")
        
        # Check if the first message is preserved in smart windowing
        if len(memory.messages) > 10:
            first_msg_in_smart = recent_smart[0].content == conversations[0][0]
            print(f"First message preserved in smart windowing: {first_msg_in_smart}")
    
    print("\n--- Final Test Results ---")
    print(f"Total messages in memory: {len(memory.messages)}")
    print(f"Smart windowing preserves context: {len(memory.get_recent_messages_smart(10))}")
    print(f"Full context available: {len(memory.get_full_conversation_context()) > 0}")
    
    # Test conversation context
    context = memory.get_full_conversation_context()
    if "Hello, I need help with my project" in context:
        print("✅ Original context preserved")
    else:
        print("❌ Original context lost")
    
    if "pool settings" in context.lower():
        print("✅ Recent context preserved")
    else:
        print("❌ Recent context lost")
    
    print("\nMemory management test completed!")

if __name__ == "__main__":
    test_memory_management()
