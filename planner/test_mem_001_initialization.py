#!/usr/bin/env python3
"""
Test Case 1.1.1: ConversationMemory Initialization
Test ID: MEM_001
Test Type: Functional
Priority: High

This test validates that ConversationMemory initializes correctly with default parameters.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the planner directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import ConversationMemory
from langchain.memory import ConversationSummaryBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.base import BaseLanguageModel

class TestConversationMemoryInitialization(unittest.TestCase):
    """Test class for ConversationMemory initialization validation"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_session_id = "test-session-001"
        self.expected_max_token_limit = 4000
        
        # Clean up any existing test database files
        self.cleanup_test_db()
    
    def tearDown(self):
        """Clean up test environment after each test"""
        self.cleanup_test_db()
    
    def cleanup_test_db(self):
        """Remove test database files"""
        db_path = Path("memory") / f"{self.test_session_id}.db"
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception as e:
                print(f"Warning: Could not clean up test database: {e}")
    
    @patch('memory_manager.ChatAnthropic')
    def test_mem_001_conversation_memory_initialization_with_defaults(self, mock_chat_anthropic):
        """
        Test Case 1.1.1: ConversationMemory Initialization
        
        Test Steps:
        1. Mock ChatAnthropic to avoid API calls during testing
        2. Create ConversationMemory instance with test session ID and default max_token_limit
        3. Validate object creation and attribute assignment
        4. Verify LangChain memory initialization
        5. Confirm Claude model configuration
        """
        
        # Step 1: Mock ChatAnthropic to avoid API calls
        mock_llm = MagicMock(spec=BaseLanguageModel)
        mock_llm.model_name = "claude-3-sonnet-20240229"
        mock_chat_anthropic.return_value = mock_llm
        
        # Step 2: Create ConversationMemory instance with test parameters
        print(f"Step 2: Creating ConversationMemory with session_id='{self.test_session_id}' and default max_token_limit")
        
        try:
            conversation_memory = ConversationMemory(
                session_id=self.test_session_id,
                max_token_limit=self.expected_max_token_limit
            )
            print("✅ ConversationMemory object created successfully")
        except Exception as e:
            self.fail(f"❌ Failed to create ConversationMemory object: {e}")
        
        # Step 3: Validate object creation and attribute assignment
        print("Step 3: Validating object attributes")
        
        # Validation Point 1: Session ID is stored correctly
        self.assertEqual(
            conversation_memory.session_id, 
            self.test_session_id,
            f"Expected session_id to be '{self.test_session_id}', got '{conversation_memory.session_id}'"
        )
        print(f"✅ Session ID validated: {conversation_memory.session_id}")
        
        # Validation Point 2: Max token limit is set correctly
        self.assertEqual(
            conversation_memory.max_token_limit,
            self.expected_max_token_limit,
            f"Expected max_token_limit to be {self.expected_max_token_limit}, got {conversation_memory.max_token_limit}"
        )
        print(f"✅ Max token limit validated: {conversation_memory.max_token_limit}")
        
        # Step 4: Verify LangChain memory initialization
        print("Step 4: Validating LangChain memory initialization")
        
        # Validation Point 3: Memory is instance of ConversationSummaryBufferMemory
        self.assertIsInstance(
            conversation_memory.memory,
            ConversationSummaryBufferMemory,
            f"Expected memory to be instance of ConversationSummaryBufferMemory, got {type(conversation_memory.memory)}"
        )
        print(f"✅ Memory type validated: {type(conversation_memory.memory).__name__}")
        
        # Verify memory configuration
        self.assertEqual(
            conversation_memory.memory.max_token_limit,
            self.expected_max_token_limit,
            f"Expected memory max_token_limit to be {self.expected_max_token_limit}, got {conversation_memory.memory.max_token_limit}"
        )
        print(f"✅ Memory max_token_limit validated: {conversation_memory.memory.max_token_limit}")
        
        self.assertTrue(
            conversation_memory.memory.return_messages,
            "Expected memory.return_messages to be True"
        )
        print(f"✅ Memory return_messages validated: {conversation_memory.memory.return_messages}")
        
        # Step 5: Confirm Claude model configuration
        print("Step 5: Validating Claude model configuration")
        
        # Validation Point 4: LLM is configured correctly
        self.assertIsNotNone(
            conversation_memory.llm,
            "Expected llm attribute to be initialized"
        )
        print(f"✅ LLM attribute is initialized")
        
        # Verify ChatAnthropic was called with correct model
        mock_chat_anthropic.assert_called_once_with(model="claude-3-sonnet-20240229")
        print(f"✅ ChatAnthropic called with correct model: claude-3-sonnet-20240229")
        
        # Verify the mocked LLM is assigned
        self.assertEqual(
            conversation_memory.llm,
            mock_llm,
            "Expected llm to be the mocked ChatAnthropic instance"
        )
        print(f"✅ LLM instance validated")
        
        print("\n🎉 All validation points passed successfully!")
    
    @patch('memory_manager.ChatAnthropic')
    def test_mem_001_custom_max_token_limit(self, mock_chat_anthropic):
        """
        Test ConversationMemory initialization with custom max_token_limit
        
        Test Steps:
        1. Create ConversationMemory with custom max_token_limit
        2. Validate custom limit is applied correctly
        """
        
        # Step 1: Setup custom parameters
        custom_token_limit = 8000
        mock_llm = MagicMock(spec=BaseLanguageModel)
        mock_llm.model_name = "claude-3-sonnet-20240229"
        mock_chat_anthropic.return_value = mock_llm
        
        print(f"Testing with custom max_token_limit: {custom_token_limit}")
        
        # Step 2: Create instance with custom limit
        conversation_memory = ConversationMemory(
            session_id=self.test_session_id,
            max_token_limit=custom_token_limit
        )
        
        # Step 3: Validate custom limit
        self.assertEqual(
            conversation_memory.max_token_limit,
            custom_token_limit,
            f"Expected max_token_limit to be {custom_token_limit}, got {conversation_memory.max_token_limit}"
        )
        
        self.assertEqual(
            conversation_memory.memory.max_token_limit,
            custom_token_limit,
            f"Expected memory max_token_limit to be {custom_token_limit}, got {conversation_memory.memory.max_token_limit}"
        )
        
        print(f"✅ Custom max_token_limit validated: {custom_token_limit}")
    
    @patch('memory_manager.ChatAnthropic')
    def test_mem_001_memory_attributes_initialization(self, mock_chat_anthropic):
        """
        Test detailed memory attributes initialization
        
        Test Steps:
        1. Create ConversationMemory instance
        2. Validate all memory-specific attributes
        """
        
        mock_llm = MagicMock(spec=BaseLanguageModel)
        mock_llm.model_name = "claude-3-sonnet-20240229"
        mock_chat_anthropic.return_value = mock_llm
        
        conversation_memory = ConversationMemory(
            session_id=self.test_session_id
        )
        
        # Validate memory buffer initialization
        self.assertTrue(
            hasattr(conversation_memory.memory, 'moving_summary_buffer'),
            "Expected memory to have moving_summary_buffer attribute"
        )
        
        # Validate chat memory initialization
        self.assertTrue(
            hasattr(conversation_memory.memory, 'chat_memory'),
            "Expected memory to have chat_memory attribute"
        )
        
        # Validate initial messages list is empty
        self.assertEqual(
            len(conversation_memory.memory.chat_memory.messages),
            0,
            "Expected initial chat_memory messages to be empty"
        )
        
        print("✅ All memory attributes initialized correctly")

def run_detailed_test_steps():
    """
    Run the test with detailed step-by-step output for manual validation
    """
    print("=" * 80)
    print("TEST CASE 1.1.1: ConversationMemory Initialization")
    print("Test ID: MEM_001")
    print("Test Type: Functional")
    print("Priority: High")
    print("=" * 80)
    print()
    
    print("DESCRIPTION:")
    print("Verify ConversationMemory initializes correctly with default parameters")
    print()
    
    print("TEST DATA:")
    print("- session_id: 'test-session-001'")
    print("- max_token_limit: default (4000)")
    print()
    
    print("EXPECTED BEHAVIOR:")
    print("- Object is created successfully")
    print("- Session ID is stored correctly")
    print("- LangChain memory is initialized")
    print("- Claude model is configured")
    print()
    
    print("VALIDATION POINTS:")
    print("- self.session_id == 'test-session-001'")
    print("- self.max_token_limit == 4000")
    print("- self.memory is instance of ConversationSummaryBufferMemory")
    print("- self.llm is instance of ChatAnthropic")
    print()
    
    print("EXECUTING TESTS:")
    print("-" * 40)
    
    # Run the unittest
    unittest.main(argv=[''], exit=False, verbosity=2)

if __name__ == "__main__":
    # Check if running in detailed mode
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        run_detailed_test_steps()
    else:
        unittest.main(verbosity=2)
