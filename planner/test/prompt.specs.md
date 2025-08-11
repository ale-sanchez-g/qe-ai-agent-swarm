# Test Specifications: MCP Agent Planner Chat UI

## Document Metadata
- **Document Title**: Test Specifications for Planner Chat UI API
- **Version**: 1.0.0
- **Created Date**: 2025-08-11
- **Author**: QE AI Agent Swarm Team
- **Application Version**: 1.0.0
- **Application Name**: Planner Chat UI API
- **Technology Stack**: FastAPI, WebSocket, SQLite, LaunchDarkly, MCP Agents
- **Test Environment**: Development/Staging
- **Last Updated**: 2025-08-11

## Application Overview
The MCP Agent Planner is a FastAPI-based web interface for interacting with MCP (Model Context Protocol) agents. It provides real-time chat functionality with AI agents, conversation memory management, file handling, and session management capabilities.

## Application URL
http://localhost:8000


### Key Features
- Interactive web chat interface with WebSocket communication
- Conversation memory management with SQLite backend
- Multi-MCP server integration (Atlassian, filesystem, fetch)
- LaunchDarkly AI integration for dynamic configuration
- Session management for multiple concurrent users
- File management for downloading and viewing reports
- Real-time status updates and system messages

---

## Test Categories

### 1. API Endpoint Testing

#### 1.1 Chat Interface Endpoints

##### Test Case 1.1.1: Main Chat Interface
- **Test ID**: TC_001
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify the main chat interface loads correctly
- **Endpoint**: `GET /`
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: text/html
  - Serves chat.html template
  - Interface loads without errors
- **Test Data**: N/A
- **Validation Points**:
  - Response contains valid HTML structure
  - Chat interface elements are present
  - No JavaScript errors in browser console

##### Test Case 1.1.2: Health Check Endpoint
- **Test ID**: TC_002
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify health check endpoint returns service status
- **Endpoint**: `GET /health`
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: application/json
  - Returns `{"status": "ok"}`
- **Test Data**: N/A
- **Validation Points**:
  - Response format matches expected JSON structure
  - Status field contains "ok" value

#### 1.2 File Management Endpoints

##### Test Case 1.2.1: Download Existing File
- **Test ID**: TC_003
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify file download functionality for existing files
- **Endpoint**: `GET /download/{filename}`
- **Prerequisites**: Valid file exists in output directory
- **Test Data**: Valid filename (e.g., "test_report.md")
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: text/markdown
  - File content is returned correctly
  - Content-Disposition header includes filename
- **Validation Points**:
  - File content matches expected data
  - Proper headers are set for file download

##### Test Case 1.2.2: Download Non-Existent File
- **Test ID**: TC_004
- **Test Type**: Negative
- **Priority**: Medium
- **Description**: Verify error handling for non-existent file downloads
- **Endpoint**: `GET /download/{filename}`
- **Test Data**: Non-existent filename (e.g., "nonexistent.md")
- **Expected Behavior**:
  - Returns HTTP 200 status (current implementation)
  - Returns JSON error message `{"error": "File not found"}`
- **Validation Points**:
  - Error message is properly formatted
  - No file content is returned

##### Test Case 1.2.3: List Reports
- **Test ID**: TC_005
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify listing of available reports
- **Endpoint**: `GET /list_reports`
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: application/json
  - Returns array of report objects with metadata
- **Test Data**: Various files in output directory
- **Validation Points**:
  - Reports array contains correct file information
  - Each report object has filename, created, and size fields
  - Reports are sorted by creation time (newest first)

##### Test Case 1.2.4: Reports Interface
- **Test ID**: TC_006
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify reports viewing interface loads correctly
- **Endpoint**: `GET /reports`
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: text/html
  - Serves reports.html template
- **Validation Points**:
  - Reports interface loads without errors
  - Proper HTML structure is returned

#### 1.3 Memory Management Endpoints

##### Test Case 1.3.1: List Active Sessions
- **Test ID**: TC_007
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify listing of active conversation sessions
- **Endpoint**: `GET /memory/sessions`
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Content-Type: application/json
  - Returns sessions array and count
- **Validation Points**:
  - Sessions array contains valid UUIDs
  - Count matches array length
  - Response format is correct

##### Test Case 1.3.2: Clear Existing Session
- **Test ID**: TC_008
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify clearing memory for existing session
- **Endpoint**: `DELETE /memory/session/{session_id}`
- **Prerequisites**: Valid session exists
- **Test Data**: Valid session UUID
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Returns success message with session ID
- **Validation Points**:
  - Session memory is cleared
  - Success message contains correct session ID

##### Test Case 1.3.3: Clear Non-Existent Session
- **Test ID**: TC_009
- **Test Type**: Negative
- **Priority**: Medium
- **Description**: Verify error handling for non-existent session
- **Endpoint**: `DELETE /memory/session/{session_id}`
- **Test Data**: Non-existent session UUID
- **Expected Behavior**:
  - Returns HTTP 200 status (current implementation)
  - Returns error message `{"error": "Session not found"}`
- **Validation Points**:
  - Proper error message is returned
  - No session data is affected

##### Test Case 1.3.4: Get Session History - Existing Session
- **Test ID**: TC_010
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify retrieval of conversation history for existing session
- **Endpoint**: `GET /memory/session/{session_id}/history`
- **Prerequisites**: Valid session with conversation history
- **Test Data**: Valid session UUID
- **Expected Behavior**:
  - Returns HTTP 200 status
  - Returns session_id and messages array
- **Validation Points**:
  - Messages array contains proper message objects
  - Each message has type and content fields
  - Session ID matches request parameter

##### Test Case 1.3.5: Get Session History - Non-Existent Session
- **Test ID**: TC_011
- **Test Type**: Negative
- **Priority**: Medium
- **Description**: Verify error handling for non-existent session history
- **Endpoint**: `GET /memory/session/{session_id}/history`
- **Test Data**: Non-existent session UUID
- **Expected Behavior**:
  - Returns HTTP 200 status (current implementation)
  - Returns error message `{"error": "Session not found"}`
- **Validation Points**:
  - Proper error message is returned

### 2. WebSocket Communication Testing

#### 2.1 WebSocket Connection Management

##### Test Case 2.1.1: WebSocket Connection Establishment
- **Test ID**: TC_012
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify WebSocket connection can be established
- **Endpoint**: `WebSocket /ws`
- **Expected Behavior**:
  - WebSocket connection is accepted
  - Session ID is assigned
  - Connection is added to active connections
- **Validation Points**:
  - Connection status is established
  - Session ID is valid UUID format
  - No connection errors occur

##### Test Case 2.1.2: WebSocket Message Processing
- **Test ID**: TC_013
- **Test Type**: Functional
- **Priority**: High
- **Description**: Verify WebSocket message processing workflow
- **Endpoint**: `WebSocket /ws`
- **Test Data**: `{"action": "message", "content": "Hello, AI!"}`
- **Expected Behavior**:
  - User message is echoed back
  - System status messages are sent
  - AI response is generated and sent
- **Validation Points**:
  - Message flow follows expected sequence
  - All message types are properly formatted
  - Response content is relevant to input

##### Test Case 2.1.3: WebSocket Error Handling
- **Test ID**: TC_014
- **Test Type**: Negative
- **Priority**: High
- **Description**: Verify WebSocket error handling for invalid messages
- **Endpoint**: `WebSocket /ws`
- **Test Data**: Invalid JSON or malformed message
- **Expected Behavior**:
  - Error is caught gracefully
  - System error message is sent to client
  - Connection remains active
- **Validation Points**:
  - Error message is properly formatted
  - Connection is not terminated
  - Subsequent valid messages work correctly

##### Test Case 2.1.4: WebSocket Disconnection
- **Test ID**: TC_015
- **Test Type**: Functional
- **Priority**: Medium
- **Description**: Verify proper cleanup on WebSocket disconnection
- **Endpoint**: `WebSocket /ws`
- **Expected Behavior**:
  - Connection is removed from active connections
  - Session mapping is cleaned up
  - No memory leaks occur
- **Validation Points**:
  - Connection count decreases
  - Session data is properly cleaned
  - No orphaned connections remain

### 3. Integration Testing

#### 3.1 MCP Agent Integration

##### Test Case 3.1.1: Agent Initialization
- **Test ID**: TC_016
- **Test Type**: Integration
- **Priority**: High
- **Description**: Verify MCP agent initialization and configuration
- **Expected Behavior**:
  - Agent is initialized with correct parameters
  - Server connections are established
  - Tools are available for use
- **Validation Points**:
  - Agent name is set correctly
  - Server names include required services
  - Tool listing returns available tools

##### Test Case 3.1.2: LLM Integration
- **Test ID**: TC_017
- **Test Type**: Integration
- **Priority**: High
- **Description**: Verify LLM integration and response generation
- **Prerequisites**: Valid LaunchDarkly configuration or fallback
- **Expected Behavior**:
  - LLM connection is established
  - Responses are generated for user queries
  - Conversation context is maintained
- **Validation Points**:
  - LLM responses are coherent and relevant
  - Context from previous messages is used
  - Response format is appropriate

#### 3.2 LaunchDarkly Integration

##### Test Case 3.2.1: LaunchDarkly Configuration - Valid Key
- **Test ID**: TC_018
- **Test Type**: Integration
- **Priority**: Medium
- **Description**: Verify LaunchDarkly integration with valid SDK key
- **Prerequisites**: Valid LAUNCHDARKLY_SDK_KEY environment variable
- **Expected Behavior**:
  - Client initializes successfully
  - AI configuration is retrieved
  - Tracking is enabled
- **Validation Points**:
  - Client initialization status is true
  - AI config contains expected properties
  - Tracker object is available

##### Test Case 3.2.2: LaunchDarkly Configuration - Missing Key
- **Test ID**: TC_019
- **Test Type**: Integration
- **Priority**: Medium
- **Description**: Verify fallback behavior when LaunchDarkly key is missing
- **Prerequisites**: No LAUNCHDARKLY_SDK_KEY environment variable
- **Expected Behavior**:
  - Warning messages are logged
  - Fallback configuration is used
  - Application continues to function
- **Validation Points**:
  - Warning messages are displayed
  - Default system prompt is used
  - Chat functionality works without LaunchDarkly

#### 3.3 File System Integration

##### Test Case 3.3.1: Output Directory Management
- **Test ID**: TC_020
- **Test Type**: Integration
- **Priority**: Medium
- **Description**: Verify output directory creation and file management
- **Expected Behavior**:
  - Output directory is created if it doesn't exist
  - Files are saved with correct naming convention
  - File metadata is accurate
- **Validation Points**:
  - Directory exists after first conversation
  - File names follow UUID pattern
  - File content matches conversation data

### 4. Performance Testing

#### 4.1 Concurrent Connections

##### Test Case 4.1.1: Multiple WebSocket Connections
- **Test ID**: TC_021
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify handling of multiple concurrent WebSocket connections
- **Test Data**: 10+ simultaneous connections
- **Expected Behavior**:
  - All connections are accepted
  - Each connection gets unique session ID
  - Messages are processed independently
- **Validation Points**:
  - No connection drops occur
  - Response times remain acceptable
  - Session isolation is maintained

##### Test Case 4.1.2: Message Processing Load
- **Test ID**: TC_022
- **Test Type**: Performance
- **Priority**: Medium
- **Description**: Verify message processing under load
- **Test Data**: High volume of messages per connection
- **Expected Behavior**:
  - Messages are processed in order
  - Response times are reasonable
  - Memory usage remains stable
- **Validation Points**:
  - Message order is preserved
  - No message loss occurs
  - System remains responsive

### 5. Security Testing

#### 5.1 Input Validation

##### Test Case 5.1.1: WebSocket Message Validation
- **Test ID**: TC_023
- **Test Type**: Security
- **Priority**: High
- **Description**: Verify proper validation of WebSocket messages
- **Test Data**: Various malformed and malicious JSON inputs
- **Expected Behavior**:
  - Invalid JSON is rejected gracefully
  - No code injection is possible
  - System remains stable
- **Validation Points**:
  - Error handling is secure
  - No sensitive information is leaked
  - Application continues to function

##### Test Case 5.1.2: File Path Validation
- **Test ID**: TC_024
- **Test Type**: Security
- **Priority**: High
- **Description**: Verify file download path validation
- **Test Data**: Path traversal attempts (../../../etc/passwd)
- **Expected Behavior**:
  - Only files from output directory are accessible
  - Path traversal is prevented
  - Error messages don't reveal system structure
- **Validation Points**:
  - Files outside output directory are inaccessible
  - No system files can be accessed
  - Error responses are generic

### 6. Error Handling and Edge Cases

#### 6.1 System Resilience

##### Test Case 6.1.1: Database Connection Issues
- **Test ID**: TC_025
- **Test Type**: Error Handling
- **Priority**: Medium
- **Description**: Verify behavior when session database is unavailable
- **Expected Behavior**:
  - Graceful degradation occurs
  - Error messages are user-friendly
  - System attempts recovery
- **Validation Points**:
  - Application doesn't crash
  - Users receive appropriate feedback
  - Service can recover when DB is restored

##### Test Case 6.1.2: MCP Server Connection Failures
- **Test ID**: TC_026
- **Test Type**: Error Handling
- **Priority**: Medium
- **Description**: Verify handling of MCP server connection failures
- **Expected Behavior**:
  - Connection failures are detected
  - Fallback behavior is implemented
  - User is notified of limited functionality
- **Validation Points**:
  - Error detection is accurate
  - Fallback mechanisms work
  - User experience is maintained

### 7. User Interface Testing

#### 7.1 Frontend Integration

##### Test Case 7.1.1: Chat Interface Functionality
- **Test ID**: TC_027
- **Test Type**: UI
- **Priority**: High
- **Description**: Verify end-to-end chat functionality through UI
- **Expected Behavior**:
  - Messages can be sent via chat interface
  - Responses are displayed correctly
  - Status indicators work properly
- **Validation Points**:
  - Message formatting is correct
  - Real-time updates work
  - UI remains responsive

##### Test Case 7.1.2: Reports Interface Functionality
- **Test ID**: TC_028
- **Test Type**: UI
- **Priority**: Medium
- **Description**: Verify reports interface displays and downloads work
- **Expected Behavior**:
  - Reports list is displayed correctly
  - File downloads work from UI
  - Metadata is shown accurately
- **Validation Points**:
  - Report list updates dynamically
  - Download links function correctly
  - File information is accurate

---

## Test Execution Guidelines

### Prerequisites
1. Application server running on localhost:8000
2. Required dependencies installed
3. Test data files in output directory
4. Environment variables configured appropriately

### Test Environment Setup
1. Clean database state for session testing
2. Known test files in output directory
3. Network connectivity for external integrations
4. Valid LaunchDarkly configuration (optional)

### Test Data Requirements
- Sample conversation files for download testing
- Valid and invalid session UUIDs
- Various message formats for WebSocket testing
- Test files with different formats and sizes

### Automation Considerations
- Use pytest for API endpoint testing
- Implement WebSocket testing with websockets library
- Performance tests with locust or similar tools
- Integration tests with testcontainers for isolation

### Success Criteria
- All functional tests pass with 100% success rate
- Performance tests meet acceptable thresholds
- Security tests show no vulnerabilities
- Error handling gracefully manages edge cases
- Integration tests verify external service connectivity

---

## Risk Assessment

### High Risk Areas
1. WebSocket connection management under load
2. Session memory management and cleanup
3. File system security and path validation
4. External service dependencies (LaunchDarkly, MCP servers)

### Mitigation Strategies
1. Implement comprehensive connection pooling tests
2. Add memory leak detection in test suite
3. Conduct thorough security testing with various attack vectors
4. Design fallback mechanisms for external service failures

---

## Maintenance and Updates

### Test Maintenance Schedule
- Review test cases quarterly
- Update test data monthly
- Performance baseline updates after significant changes
- Security test updates based on threat landscape

### Documentation Updates
- Update test specifications when new features are added
- Maintain test execution results and metrics
- Document known issues and workarounds
- Keep environment setup instructions current
