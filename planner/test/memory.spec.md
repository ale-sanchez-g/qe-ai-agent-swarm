# Test Specifications: Memory Manager for MCP Agent Planner

## Document Metadata
- **Document Title**: Memory Manager Test Specifications
- **Version**: 1.0.0
- **Created Date**: 2025-08-11
- **Author**: QE AI Agent Swarm Team
- **Module**: memory_manager.py
- **Technology Stack**: Python, LangChain, SQLite, Threading
- **Test Environment**: Development/Staging
- **Last Updated**: 2025-08-11

## Module Overview
The Memory Manager provides conversation memory management for the MCP Agent Planner. It consists of two main classes:
- `ConversationMemory`: Manages individual chat session memory with intelligent context management
- `SessionManager`: Manages multiple conversation sessions with automatic cleanup

### Key Features
- Conversation persistence using SQLite database
- Intelligent message windowing and context management
- Summary buffer for long conversations using LangChain
- Automatic session cleanup with timeout management
- Thread-safe operations for concurrent access

## Application URL
http://localhost:8000

---

## Test Categories

### 1. ConversationMemory Class Testing

#### 1.1 Initialization and Setup

##### Test Case 1.1.1: ConversationMemory Initialization
- **Test ID**: MEM_001
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify ConversationMemory initializes correctly with default parameters
- **Test Data**: 
  - `session_id`: "test-session-001"
  - `max_token_limit`: default (4000)
- **Expected Behavior**:
  - Object is created successfully
  - Session ID is stored correctly
  - LangChain memory is initialized
  - Claude model is configured
- **Validation Points**:
  - `self.session_id == "test-session-001"`
  - `self.max_token_limit == 4000`
  - `self.memory` is instance of ConversationSummaryBufferMemory
  - `self.llm` is instance of ChatAnthropic

##### Test Case 1.1.2: ConversationMemory Custom Token Limit
- **Test ID**: MEM_002
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify ConversationMemory accepts custom token limits
- **Test Data**: 
  - `session_id`: "test-session-002"
  - `max_token_limit`: 2000
- **Expected Behavior**:
  - Custom token limit is set correctly
  - Memory buffer respects the limit
- **Validation Points**:
  - `self.max_token_limit == 2000`
  - Memory configuration uses custom limit

##### Test Case 1.1.3: Database Directory Creation
- **Test ID**: MEM_003
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify memory directory is created during initialization
- **Test Data**: New session in clean environment
- **Expected Behavior**:
  - `memory/` directory is created if it doesn't exist
  - No errors occur during directory creation
- **Validation Points**:
  - `Path("memory").exists() == True`
  - Directory has proper permissions

#### 1.2 Message Management

##### Test Case 1.2.1: Add User Message
- **Test ID**: MEM_004
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify user messages are added correctly to memory
- **Test Data**: "Hello, this is a test user message"
- **Expected Behavior**:
  - Message is added to chat memory
  - Message count increases
  - Data is persisted to database
  - Debug output is generated
- **Validation Points**:
  - `len(memory.chat_memory.messages)` increases by 1
  - Last message is HumanMessage type
  - Message content matches input
  - Database contains the message

##### Test Case 1.2.2: Add AI Message
- **Test ID**: MEM_005
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify AI messages are added correctly to memory
- **Test Data**: "This is a test AI response"
- **Expected Behavior**:
  - Message is added to chat memory
  - Message count increases
  - Data is persisted to database
  - Debug output is generated
- **Validation Points**:
  - `len(memory.chat_memory.messages)` increases by 1
  - Last message is AIMessage type
  - Message content matches input
  - Database contains the message

##### Test Case 1.2.3: Sequential Message Addition
- **Test ID**: MEM_006
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify multiple messages can be added in sequence
- **Test Data**: 
  - User: "Question 1"
  - AI: "Answer 1"
  - User: "Question 2" 
  - AI: "Answer 2"
- **Expected Behavior**:
  - All messages are stored in correct order
  - Message types alternate correctly
  - Total count is accurate
- **Validation Points**:
  - `len(memory.chat_memory.messages) == 4`
  - Messages are in chronological order
  - Types alternate: Human, AI, Human, AI

##### Test Case 1.2.4: Empty Message Handling
- **Test ID**: MEM_007
- **Test Type**: Edge Case
- **Priority**: Medium
- **Description**: Verify handling of empty messages
- **Test Data**: 
  - Empty string: ""
  - Whitespace only: "   "
  - None value (if possible)
- **Expected Behavior**:
  - Empty messages are either rejected or handled gracefully
  - No system errors occur
  - Memory state remains consistent
- **Validation Points**:
  - System doesn't crash
  - Memory count is accurate
  - Error handling is appropriate

##### Test Case 1.2.5: Large Message Handling
- **Test ID**: MEM_008
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify handling of very large messages
- **Test Data**: Message with 10,000+ characters
- **Expected Behavior**:
  - Large messages are stored successfully
  - Performance remains acceptable
  - Memory usage is reasonable
- **Validation Points**:
  - Message is stored completely
  - No truncation occurs unexpectedly
  - System remains responsive

#### 1.3 Context Retrieval Methods

##### Test Case 1.3.1: Get Conversation Context - Empty Memory
- **Test ID**: MEM_009
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify context retrieval when memory is empty
- **Expected Behavior**:
  - Empty string or appropriate default is returned
  - No errors occur
  - Method handles empty state gracefully
- **Validation Points**:
  - Return value is string type
  - No exceptions are raised
  - Result is consistent with empty state

##### Test Case 1.3.2: Get Conversation Context - With Messages
- **Test ID**: MEM_010
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify context retrieval with existing messages
- **Test Data**: 5 alternating user/AI messages
- **Expected Behavior**:
  - Context string contains all relevant messages
  - Format is readable and structured
  - Summary buffer is used when available
- **Validation Points**:
  - All messages are represented in context
  - Format includes "User:" and "Assistant:" labels
  - Content is properly structured

##### Test Case 1.3.3: Get Recent Messages - Default Count
- **Test ID**: MEM_011
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify recent messages retrieval with default count
- **Test Data**: 15 messages in memory
- **Expected Behavior**:
  - Last 10 messages are returned (default)
  - Messages are in chronological order
  - Message objects are complete
- **Validation Points**:
  - `len(result) == 10`
  - First message is oldest of the returned set
  - Last message is most recent
  - All are BaseMessage instances

##### Test Case 1.3.4: Get Recent Messages - Custom Count
- **Test ID**: MEM_012
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify recent messages retrieval with custom count
- **Test Data**: 
  - 20 messages in memory
  - Request count: 5
- **Expected Behavior**:
  - Exactly 5 most recent messages are returned
  - Messages maintain chronological order
- **Validation Points**:
  - `len(result) == 5`
  - Messages are the 5 most recent
  - Order is preserved

##### Test Case 1.3.5: Get Recent Messages Smart - Small Dataset
- **Test ID**: MEM_013
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify smart message retrieval with fewer messages than window
- **Test Data**: 8 messages, request count: 15
- **Expected Behavior**:
  - All 8 messages are returned
  - No padding or errors occur
- **Validation Points**:
  - `len(result) == 8`
  - All messages are included
  - Order is preserved

##### Test Case 1.3.6: Get Recent Messages Smart - Large Dataset
- **Test ID**: MEM_014
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify smart message retrieval with more messages than window
- **Test Data**: 50 messages, request count: 15
- **Expected Behavior**:
  - First message + 14 most recent messages returned
  - Total count is 15
  - Important context is preserved
- **Validation Points**:
  - `len(result) == 15`
  - First element is the very first message
  - Remaining 14 are most recent
  - Gap is handled appropriately

##### Test Case 1.3.7: Get Full Conversation Context
- **Test ID**: MEM_015
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify comprehensive context retrieval including summary
- **Test Data**: Long conversation with summary buffer active
- **Expected Behavior**:
  - Summary is included if available
  - Recent messages are included
  - Format is coherent and readable
- **Validation Points**:
  - Summary section is present when applicable
  - Recent conversation section is present
  - Both sections are properly formatted
  - Content is comprehensive but manageable

#### 1.4 Memory Management Operations

##### Test Case 1.4.1: Clear Memory
- **Test ID**: MEM_016
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify memory can be cleared completely
- **Test Data**: Memory with 10 messages
- **Expected Behavior**:
  - All messages are removed from memory
  - Database is updated
  - Memory count returns to zero
- **Validation Points**:
  - `len(memory.chat_memory.messages) == 0`
  - Database table is empty
  - Context methods return empty results

##### Test Case 1.4.2: Memory Persistence After Clear
- **Test ID**: MEM_017
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify memory remains clear after reload
- **Test Data**: Cleared memory, then reinitialize ConversationMemory
- **Expected Behavior**:
  - New instance loads empty memory
  - No residual messages appear
- **Validation Points**:
  - Fresh instance has zero messages
  - Database reflects cleared state

#### 1.5 Database Operations

##### Test Case 1.5.1: Database Creation
- **Test ID**: MEM_018
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify database file is created for new sessions
- **Test Data**: New unique session ID
- **Expected Behavior**:
  - SQLite database file is created
  - Database has correct schema
  - File permissions are appropriate
- **Validation Points**:
  - File exists at `memory/{session_id}.db`
  - Table "messages" exists with correct schema
  - File is readable/writable

##### Test Case 1.5.2: Database Loading - Existing Data
- **Test ID**: MEM_019
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify existing conversation is loaded from database
- **Test Data**: Pre-existing database with conversation history
- **Expected Behavior**:
  - All messages are loaded in correct order
  - Message types are preserved
  - Timestamps are respected
- **Validation Points**:
  - Loaded messages match database content
  - Chronological order is maintained
  - Human/AI message types are correct

##### Test Case 1.5.3: Database Loading - Corrupted Data
- **Test ID**: MEM_020
- **Test Type**: Error Handling
- **Priority**: Medium
- **Description**: Verify handling of corrupted database files
- **Test Data**: Database file with invalid schema or corrupted data
- **Expected Behavior**:
  - Error is caught gracefully
  - System continues to operate
  - New conversation can be started
- **Validation Points**:
  - No system crash occurs
  - Error is logged appropriately
  - Fresh conversation state is established

##### Test Case 1.5.4: Database Concurrent Access
- **Test ID**: MEM_021
- **Test Type**: Concurrency
- **Priority**: Medium
- **Description**: Verify database handles concurrent access correctly
- **Test Data**: Multiple threads accessing same session database
- **Expected Behavior**:
  - No database locking errors
  - Data integrity is maintained
  - All operations complete successfully
- **Validation Points**:
  - No SQLite locking exceptions
  - Final data state is consistent
  - No data corruption occurs

### 2. SessionManager Class Testing

#### 2.1 Session Creation and Retrieval

##### Test Case 2.1.1: Get or Create Session - New Session
- **Test ID**: SES_001
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify new session creation when session doesn't exist
- **Test Data**: `session_id`: "new-session-001"
- **Expected Behavior**:
  - New ConversationMemory instance is created
  - Session is added to sessions dictionary
  - Timeout is set appropriately
- **Validation Points**:
  - `session_id in session_manager.sessions`
  - Returned object is ConversationMemory instance
  - Timeout is set to current time + cleanup_interval

##### Test Case 2.1.2: Get or Create Session - Existing Session
- **Test ID**: SES_002
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify existing session is returned without creating new one
- **Test Data**: Previously created session ID
- **Expected Behavior**:
  - Existing ConversationMemory instance is returned
  - No new session is created
  - Timeout is updated
- **Validation Points**:
  - Same object reference is returned
  - Session count doesn't increase
  - Timeout is refreshed

##### Test Case 2.1.3: Multiple Session Creation
- **Test ID**: SES_003
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify multiple independent sessions can be created
- **Test Data**: 5 different session IDs
- **Expected Behavior**:
  - All sessions are created successfully
  - Each session is independent
  - Session count matches created count
- **Validation Points**:
  - `len(session_manager.sessions) == 5`
  - Each session has unique ID
  - Sessions don't interfere with each other

#### 2.2 Session Removal

##### Test Case 2.2.1: Remove Existing Session
- **Test ID**: SES_004
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify existing session can be removed
- **Test Data**: Active session to remove
- **Expected Behavior**:
  - Session is removed from sessions dictionary
  - Timeout entry is removed
  - Session count decreases
- **Validation Points**:
  - `session_id not in session_manager.sessions`
  - `session_id not in session_manager.session_timeouts`
  - Session count decreased by 1

##### Test Case 2.2.2: Remove Non-existent Session
- **Test ID**: SES_005
- **Test Type**: Edge Case
- **Priority**: Medium
- **Description**: Verify graceful handling of removing non-existent session
- **Test Data**: Session ID that doesn't exist
- **Expected Behavior**:
  - No errors occur
  - System state remains unchanged
  - Other sessions are unaffected
- **Validation Points**:
  - No exceptions are raised
  - Session count remains same
  - Other sessions still accessible

#### 2.3 Session Cleanup

##### Test Case 2.3.1: Cleanup Thread Initialization
- **Test ID**: SES_006
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify cleanup thread starts correctly during initialization
- **Expected Behavior**:
  - Background thread is created
  - Thread is marked as daemon
  - Thread starts successfully
- **Validation Points**:
  - Thread is running
  - Thread is daemon type
  - No startup errors occur

##### Test Case 2.3.2: Expired Session Detection
- **Test ID**: SES_007
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify expired sessions are identified correctly
- **Test Data**: Sessions with past timeout dates
- **Expected Behavior**:
  - Expired sessions are detected
  - Non-expired sessions are preserved
  - Cleanup is selective
- **Validation Points**:
  - Only expired sessions are removed
  - Active sessions remain intact
  - Cleanup is accurate

##### Test Case 2.3.3: Cleanup Timing Configuration
- **Test ID**: SES_008
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify cleanup interval configuration works correctly
- **Test Data**: Custom cleanup interval (e.g., 1 hour)
- **Expected Behavior**:
  - Sessions expire after configured interval
  - Cleanup respects timing configuration
- **Validation Points**:
  - Timeout calculation uses correct interval
  - Sessions expire at expected time

##### Test Case 2.3.4: Cleanup Under Load
- **Test ID**: SES_009
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify cleanup works correctly with many sessions
- **Test Data**: 100+ sessions with various expiry times
- **Expected Behavior**:
  - Cleanup processes all sessions efficiently
  - No performance degradation
  - Memory usage remains reasonable
- **Validation Points**:
  - All expired sessions are removed
  - Cleanup completes in reasonable time
  - Memory usage is acceptable

### 3. Integration Testing

#### 3.1 Memory Persistence Integration

##### Test Case 3.1.1: Cross-Session Data Persistence
- **Test ID**: INT_001
- **Test Type**: Integration
- **Priority**: High
- **Description**: Verify data persists across application restarts
- **Test Data**: Active conversation, then restart application
- **Expected Behavior**:
  - Conversation history is restored
  - Session state is maintained
  - No data loss occurs
- **Validation Points**:
  - All messages are restored correctly
  - Session can continue seamlessly
  - Data integrity is maintained

##### Test Case 3.1.2: Multiple Session Persistence
- **Test ID**: INT_002
- **Test Type**: Integration
- **Priority**: High
- **Description**: Verify multiple sessions persist independently
- **Test Data**: 3 different sessions with different conversations
- **Expected Behavior**:
  - Each session maintains its own data
  - No cross-contamination occurs
  - All sessions restore correctly
- **Validation Points**:
  - Session data remains separate
  - Conversations don't mix
  - All sessions are accessible

#### 3.2 LangChain Integration

##### Test Case 3.2.1: Summary Buffer Activation
- **Test ID**: INT_003
- **Test Type**: Integration
- **Priority**: High
- **Description**: Verify LangChain summary buffer activates correctly
- **Test Data**: Conversation exceeding token limit
- **Expected Behavior**:
  - Summary buffer is created automatically
  - Long conversation is summarized
  - Recent messages are preserved
- **Validation Points**:
  - Summary buffer contains content
  - Recent messages are still available
  - Total context size is managed

##### Test Case 3.2.2: Claude Model Integration
- **Test ID**: INT_004
- **Test Type**: Integration
- **Priority**: Medium
- **Description**: Verify Claude model integration for summarization
- **Prerequisites**: Valid Anthropic API key
- **Expected Behavior**:
  - Model connection is established
  - Summarization requests succeed
  - Summaries are coherent
- **Validation Points**:
  - No API connection errors
  - Summaries are generated
  - Summary quality is reasonable

### 4. Performance Testing

#### 4.1 Memory Usage

##### Test Case 4.1.1: Memory Growth with Large Conversations
- **Test ID**: PERF_001
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify memory usage remains bounded with long conversations
- **Test Data**: 1000+ message conversation
- **Expected Behavior**:
  - Memory usage stabilizes due to summary buffer
  - No memory leaks occur
  - Performance remains acceptable
- **Validation Points**:
  - Memory usage doesn't grow linearly
  - Summary buffer manages context size
  - Response times remain reasonable

##### Test Case 4.1.2: Session Manager Memory Usage
- **Test ID**: PERF_002
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify session manager memory usage with many sessions
- **Test Data**: 100+ concurrent sessions
- **Expected Behavior**:
  - Memory usage scales reasonably
  - Cleanup prevents memory buildup
  - System remains responsive
- **Validation Points**:
  - Memory usage is proportional to active sessions
  - Cleanup effectively manages memory
  - No significant memory leaks

#### 4.2 Database Performance

##### Test Case 4.2.1: Database Query Performance
- **Test ID**: PERF_003
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify database operations remain fast with large datasets
- **Test Data**: Database with 10,000+ messages
- **Expected Behavior**:
  - Load times remain acceptable
  - Save operations are efficient
  - Query performance is stable
- **Validation Points**:
  - Load time < 1 second
  - Save operations < 100ms
  - No performance degradation

### 5. Error Handling and Edge Cases

#### 5.1 System Resilience

##### Test Case 5.1.1: Database Connection Failures
- **Test ID**: ERR_001
- **Test Type**: Error Handling
- **Priority**: High
- **Description**: Verify graceful handling of database connection issues
- **Test Data**: Locked or inaccessible database file
- **Expected Behavior**:
  - Errors are caught and logged
  - System continues to operate
  - Fallback behavior is implemented
- **Validation Points**:
  - No system crashes
  - Error messages are appropriate
  - Conversation can continue in memory

##### Test Case 5.1.2: File System Errors
- **Test ID**: ERR_002
- **Test Type**: Error Handling
- **Priority**: Medium
- **Description**: Verify handling of file system permission errors
- **Test Data**: Read-only memory directory
- **Expected Behavior**:
  - Permission errors are handled gracefully
  - Alternative storage strategies are used
  - User receives appropriate feedback
- **Validation Points**:
  - System doesn't crash
  - Error handling is graceful
  - Functionality degrades gracefully

##### Test Case 5.1.3: API Connection Failures
- **Test ID**: ERR_003
- **Test Type**: Error Handling
- **Priority**: Medium
- **Description**: Verify handling of Anthropic API connection failures
- **Test Data**: Invalid API key or network issues
- **Expected Behavior**:
  - API errors are caught
  - Summary functionality degrades gracefully
  - Core memory functions continue to work
- **Validation Points**:
  - No system crashes
  - Basic memory functions work without API
  - Error messages are informative

### 6. Security Testing

#### 6.1 Data Security

##### Test Case 6.1.1: Session ID Validation
- **Test ID**: SEC_001
- **Test Type**: Security
- **Priority**: High
- **Description**: Verify session IDs are properly validated
- **Test Data**: Malicious session IDs with path traversal attempts
- **Expected Behavior**:
  - Invalid session IDs are rejected
  - No path traversal is possible
  - Database files are created safely
- **Validation Points**:
  - File paths are sanitized
  - No files created outside memory directory
  - Session ID format is enforced

##### Test Case 6.1.2: Message Content Sanitization
- **Test ID**: SEC_002
- **Test Type**: Security
- **Priority**: Medium
- **Description**: Verify message content is handled safely
- **Test Data**: Messages with SQL injection attempts
- **Expected Behavior**:
  - SQL injection is prevented
  - Parameterized queries are used
  - Data integrity is maintained
- **Validation Points**:
  - No SQL injection is possible
  - Database remains uncorrupted
  - Message content is stored safely

---

## Test Execution Guidelines

### Prerequisites
1. Python environment with required dependencies
2. SQLite database access
3. Valid Anthropic API key (for LangChain integration tests)
4. Sufficient disk space for test databases
5. File system write permissions

### Test Environment Setup
1. Clean memory directory before tests
2. Fresh SessionManager instance for each test suite
3. Isolated test databases for each test case
4. Mock API responses for offline testing

### Test Data Requirements
- Various message content types (text, unicode, special characters)
- Different session ID formats
- Test databases with known conversation data
- Large message datasets for performance testing

### Automation Framework
```python
# Example test structure
import pytest
import tempfile
import shutil
from memory_manager import ConversationMemory, SessionManager

@pytest.fixture
def temp_memory_dir():
    """Create temporary directory for test databases"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def conversation_memory():
    """Create fresh ConversationMemory instance"""
    return ConversationMemory("test-session-001")

@pytest.fixture
def session_manager():
    """Create fresh SessionManager instance"""
    return SessionManager()
```

### Success Criteria
- All functional tests pass with 100% success rate
- Performance tests meet defined thresholds
- Error handling tests demonstrate graceful degradation
- Security tests show no vulnerabilities
- Integration tests verify external service compatibility

---

## Risk Assessment

### High Risk Areas
1. Database corruption during concurrent access
2. Memory leaks in long-running sessions
3. API rate limiting with Anthropic services
4. Thread safety in session management

### Mitigation Strategies
1. Implement database connection pooling and retry logic
2. Monitor memory usage during long conversation tests
3. Add API rate limiting and fallback mechanisms
4. Use thread-safe data structures and locking where needed

---

## Performance Benchmarks

### Target Metrics
- **Message Addition**: < 50ms per message
- **Context Retrieval**: < 100ms for 1000+ messages
- **Session Creation**: < 10ms per session
- **Database Load**: < 1s for 10,000+ messages
- **Memory Usage**: < 100MB for 100 concurrent sessions

### Load Testing Scenarios
1. **High Message Volume**: 10,000 messages in single session
2. **High Session Count**: 500 concurrent sessions
3. **Long Running**: 24+ hour session with periodic activity
4. **Mixed Load**: Combination of above scenarios

---

## Maintenance and Updates

### Test Maintenance Schedule
- Review test cases monthly
- Update performance benchmarks quarterly
- Security test updates based on threat landscape
- Integration test updates when dependencies change

### Documentation Updates
- Update test specifications when features are added
- Maintain test execution results and metrics
- Document known issues and workarounds
- Keep environment setup instructions current

### Monitoring and Alerting
- Set up alerts for test failures in CI/CD
- Monitor performance regression in automated tests
- Track memory usage trends over time
- Alert on security test failures
