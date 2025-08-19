# Test Case 1.1.1: ConversationMemory Initialization - Detailed Test Steps

## Test Information
- **Test ID**: MEM_001
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify ConversationMemory initializes correctly with default parameters

## Test Data
- `session_id`: "test-session-001"
- `max_token_limit`: default (4000)

## Pre-Conditions
1. Python environment is set up with required dependencies
2. `memory_manager.py` is accessible in the test environment
3. No existing database files for the test session ID
4. Network connectivity for ChatAnthropic initialization (or mocked for unit tests)

## Test Steps

### Step 1: Environment Setup
**Action**: Prepare the test environment
**Details**:
1. Navigate to the planner directory
2. Ensure all required imports are available
3. Clean up any existing test database files
4. Set up test parameters

**Expected Result**: Test environment is ready for execution

**Validation Commands**:
```bash
cd /Users/alejandrosanchez-giraldo/git/qe-ai-agent-swarm/planner
python -c "import memory_manager; print('Import successful')"
ls memory/ | grep test-session-001 # Should return no results
```

### Step 2: Object Instantiation
**Action**: Create ConversationMemory instance with test parameters
**Details**:
```python
from memory_manager import ConversationMemory

# Create instance with test data
conversation_memory = ConversationMemory(
    session_id="test-session-001",
    max_token_limit=4000
)
```

**Expected Result**: Object is created without exceptions

**Manual Validation**:
- No exceptions thrown during instantiation
- Object reference is not None
- Constructor completes successfully

### Step 3: Session ID Validation
**Action**: Verify session ID is stored correctly
**Details**:
```python
# Validation Point 1
assert conversation_memory.session_id == "test-session-001"
print(f"Session ID: {conversation_memory.session_id}")
```

**Expected Result**: `self.session_id == "test-session-001"`

**Manual Validation**:
- Print session_id attribute value
- Compare with expected value "test-session-001"
- Verify string type and exact match

### Step 4: Max Token Limit Validation
**Action**: Verify max_token_limit is set correctly
**Details**:
```python
# Validation Point 2
assert conversation_memory.max_token_limit == 4000
print(f"Max Token Limit: {conversation_memory.max_token_limit}")
```

**Expected Result**: `self.max_token_limit == 4000`

**Manual Validation**:
- Print max_token_limit attribute value
- Verify integer type
- Confirm value equals 4000

### Step 5: LangChain Memory Initialization
**Action**: Verify memory object is properly initialized
**Details**:
```python
from langchain.memory import ConversationSummaryBufferMemory

# Validation Point 3
assert isinstance(conversation_memory.memory, ConversationSummaryBufferMemory)
print(f"Memory Type: {type(conversation_memory.memory)}")
print(f"Memory Max Token Limit: {conversation_memory.memory.max_token_limit}")
print(f"Memory Return Messages: {conversation_memory.memory.return_messages}")
```

**Expected Result**: `self.memory` is instance of ConversationSummaryBufferMemory

**Manual Validation**:
- Verify memory attribute exists
- Check instance type matches ConversationSummaryBufferMemory
- Confirm memory.max_token_limit equals 4000
- Verify memory.return_messages is True
- Check moving_summary_buffer attribute exists

### Step 6: Claude Model Configuration
**Action**: Verify ChatAnthropic LLM is configured correctly
**Details**:
```python
from langchain_anthropic import ChatAnthropic

# Validation Point 4
assert conversation_memory.llm is not None
print(f"LLM Type: {type(conversation_memory.llm)}")
print(f"LLM Model: {conversation_memory.llm.model}")
```

**Expected Result**: `self.llm` is instance of ChatAnthropic

**Manual Validation**:
- Verify llm attribute exists and is not None
- Check instance type matches ChatAnthropic
- Confirm model name is "claude-3-sonnet-20240229"

### Step 7: Memory Structure Validation
**Action**: Verify internal memory structure is properly set up
**Details**:
```python
# Additional validation for memory structure
assert hasattr(conversation_memory.memory, 'chat_memory')
assert hasattr(conversation_memory.memory, 'moving_summary_buffer')
assert len(conversation_memory.memory.chat_memory.messages) == 0

print(f"Chat Memory Messages: {len(conversation_memory.memory.chat_memory.messages)}")
print(f"Has Moving Summary Buffer: {hasattr(conversation_memory.memory, 'moving_summary_buffer')}")
```

**Expected Result**: Memory structure is properly initialized

**Manual Validation**:
- chat_memory attribute exists
- moving_summary_buffer attribute exists
- Initial messages list is empty
- No exceptions during attribute access

## Automated Test Execution

### Running the Unit Test
```bash
cd /Users/alejandrosanchez-giraldo/git/qe-ai-agent-swarm/planner
python test_mem_001_initialization.py
```

### Running with Detailed Output
```bash
python test_mem_001_initialization.py --detailed
```

### Expected Test Output
```
Test Case 1.1.1: ConversationMemory Initialization
Step 2: Creating ConversationMemory with session_id='test-session-001' and default max_token_limit
✅ ConversationMemory object created successfully
Step 3: Validating object attributes
✅ Session ID validated: test-session-001
✅ Max token limit validated: 4000
Step 4: Validating LangChain memory initialization
✅ Memory type validated: ConversationSummaryBufferMemory
✅ Memory max_token_limit validated: 4000
✅ Memory return_messages validated: True
Step 5: Validating Claude model configuration
✅ LLM attribute is initialized
✅ ChatAnthropic called with correct model: claude-3-sonnet-20240229
✅ LLM instance validated

🎉 All validation points passed successfully!
```

## Post-Conditions
1. Test database files are cleaned up
2. No persistent state remains from the test
3. All validation points have been verified

## Error Scenarios to Test

### Test Case 1.1.1a: Invalid Session ID
**Action**: Create ConversationMemory with None or empty session_id
**Expected Result**: Appropriate error handling or default behavior

### Test Case 1.1.1b: Invalid Max Token Limit
**Action**: Create ConversationMemory with negative or zero max_token_limit
**Expected Result**: Appropriate error handling or default behavior

### Test Case 1.1.1c: Network Connectivity Issues
**Action**: Test initialization when ChatAnthropic cannot connect
**Expected Result**: Graceful error handling or retry mechanism

## Manual Verification Checklist

- [ ] ConversationMemory object created successfully
- [ ] session_id attribute equals "test-session-001"
- [ ] max_token_limit attribute equals 4000
- [ ] memory attribute is ConversationSummaryBufferMemory instance
- [ ] memory.max_token_limit equals 4000
- [ ] memory.return_messages is True
- [ ] llm attribute is not None
- [ ] llm is ChatAnthropic instance
- [ ] llm.model equals "claude-3-sonnet-20240229"
- [ ] chat_memory.messages is initially empty
- [ ] No exceptions during initialization
- [ ] All required attributes are accessible

## Troubleshooting

### Common Issues
1. **ImportError**: Ensure all dependencies are installed (`langchain`, `langchain_anthropic`)
2. **Network timeout**: Mock ChatAnthropic for unit tests
3. **Permission errors**: Ensure write access to memory directory
4. **Database locks**: Clean up test databases between runs

### Debug Commands
```python
# Inspect object attributes
print(f"Object attributes: {dir(conversation_memory)}")
print(f"Memory attributes: {dir(conversation_memory.memory)}")
print(f"LLM attributes: {dir(conversation_memory.llm)}")
```
