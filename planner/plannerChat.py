"""
MCP Agent Planner: Interactive Chat UI for LLM and MCP Integration
"""

import asyncio
import os
import time
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM


# Token usage tracking
token_usage = {
    "total_requests": 0,
    "total_tokens": 0,
    "start_time": None
}

# Initialize the MCP application
mcp_app = MCPApp(name="mcp-agent-research")

# Initialize FastAPI
app = FastAPI(title="Planner Chat UI")

# Create templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create static directory for CSS and JS
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
css_dir = static_dir / "css"
css_dir.mkdir(exist_ok=True)
js_dir = static_dir / "js"
js_dir.mkdir(exist_ok=True)

# Create templates and static files
templates = Jinja2Templates(directory=str(templates_dir))

# Create connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def track_token_usage(func):
    """Decorator to track token usage for LLM calls"""
    async def wrapper(*args, **kwargs):
        global token_usage
        if token_usage["start_time"] is None:
            token_usage["start_time"] = time.time()
        
        token_usage["total_requests"] += 1
        result = await func(*args, **kwargs)
        
        # Log token usage (simplified - in real implementation, would extract from LLM response)
        print(f"Request #{token_usage['total_requests']} completed")
        return result
    return wrapper

async def process_message(user_message: str, agent: Agent = None, websocket: WebSocket = None):
    """Process a user message through the MCP agent and LLM"""
    
    if not agent:
        async with mcp_app.run() as agent_app:
            logger = agent_app.logger
            
            agent = Agent(
                name="ChatAgent",
                instruction="""You are an AI assistant that helps with research and analysis using available tools.
                               Answer user queries using the provided context and tools.
                               Be concise, helpful and accurate.""",
                server_names=["mcp-atlassian", "filesystem", "fetch"]
            )
    
    async with agent:
        # List available tools
        tools_result = await agent.list_tools()
        available_tools = tools_result.model_dump() if tools_result else {}
        
        if websocket:
            await manager.send_personal_message(
                json.dumps({"type": "system", "content": "Connecting to LLM..."}),
                websocket
            )
        
        # Connect to LLM
        llm = await agent.attach_llm(AnthropicAugmentedLLM)
        
        if websocket:
            await manager.send_personal_message(
                json.dumps({"type": "system", "content": "Processing your request..."}),
                websocket
            )
        
        # Generate response
        response = await llm.generate_str(
            message=f"""
            User query: {user_message}
            
            Available tools: {json.dumps(available_tools)}
            
            Respond to the user query using the available tools when appropriate.
            If specific information is requested that can be found in Confluence or other sources,
            use the appropriate tool to fetch that information.
            
            Format your response in markdown for better readability.
            """
        )
        
        return response

# Create HTML template for the chat interface
with open(templates_dir / "chat.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Planner Chat</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>MCP Planner Chat</h1>
            <div class="connection-status">
                <span id="status-indicator" class="status-disconnected"></span>
                <span id="status-text">Disconnected</span>
            </div>
        </div>
        
        <div class="chat-messages" id="chat-messages"></div>
        
        <div class="chat-input-container">
            <textarea id="message-input" placeholder="Type your message here..." rows="3"></textarea>
            <button id="send-button" disabled>Send</button>
        </div>
    </div>

    <script src="/static/js/chat.js"></script>
</body>
</html>
    """)

# Create CSS file
with open(css_dir / "style.css", "w") as f:
    f.write("""
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
    background-color: #f5f5f5;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.chat-container {
    width: 90%;
    max-width: 1000px;
    height: 90vh;
    background-color: #fff;
    border-radius: 10px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
}

.chat-header {
    padding: 15px;
    background-color: #2c3e50;
    color: white;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.connection-status {
    display: flex;
    align-items: center;
}

.status-connected, .status-disconnected {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-connected {
    background-color: #2ecc71;
}

.status-disconnected {
    background-color: #e74c3c;
}

.chat-messages {
    flex-grow: 1;
    padding: 15px;
    overflow-y: auto;
    background-color: #f9f9f9;
}

.message {
    margin-bottom: 15px;
    padding: 10px 15px;
    border-radius: 8px;
    max-width: 80%;
    word-wrap: break-word;
}

.user-message {
    background-color: #3498db;
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 0;
}

.bot-message {
    background-color: #e9e9eb;
    color: #000;
    margin-right: auto;
    border-bottom-left-radius: 0;
}

.system-message {
    background-color: #f8d7da;
    color: #721c24;
    margin: 10px auto;
    text-align: center;
    max-width: 100%;
}

.chat-input-container {
    padding: 15px;
    display: flex;
    border-top: 1px solid #e9e9e9;
}

#message-input {
    flex-grow: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    resize: none;
    font-size: 14px;
}

#send-button {
    padding: 10px 20px;
    margin-left: 10px;
    background-color: #2c3e50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
}

#send-button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

#send-button:hover:not(:disabled) {
    background-color: #1a2530;
}

/* Markdown styling for bot messages */
.bot-message a {
    color: #2980b9;
    text-decoration: none;
}

.bot-message a:hover {
    text-decoration: underline;
}

.bot-message pre {
    background-color: #f1f1f1;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 10px 0;
}

.bot-message code {
    font-family: 'Courier New', Courier, monospace;
    background-color: #f1f1f1;
    padding: 2px 4px;
    border-radius: 3px;
}

.bot-message blockquote {
    border-left: 4px solid #ccc;
    margin-left: 0;
    padding-left: 15px;
    color: #555;
}

.bot-message img {
    max-width: 100%;
    height: auto;
}

.bot-message table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
}

.bot-message th, .bot-message td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

.bot-message th {
    background-color: #f2f2f2;
}

.bot-message ul, .bot-message ol {
    margin-left: 20px;
    margin-top: 10px;
    margin-bottom: 10px;
}

.message-time {
    font-size: 12px;
    color: #7f8c8d;
    margin-top: 5px;
    display: block;
}
    """)

# Create JS file
with open(js_dir / "chat.js", "w") as f:
    f.write("""
let socket;
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = function(e) {
        console.log("[WebSocket] Connection established");
        statusIndicator.className = "status-connected";
        statusText.textContent = "Connected";
        sendButton.disabled = false;
        
        addSystemMessage("Connected to chat server");
    };
    
    socket.onmessage = function(event) {
        console.log(`[WebSocket] Message received:`, event.data);
        const data = JSON.parse(event.data);
        
        if (data.type === "user") {
            addUserMessage(data.content);
        } else if (data.type === "bot") {
            addBotMessage(data.content);
        } else if (data.type === "system") {
            addSystemMessage(data.content);
        }
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    
    socket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`[WebSocket] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            console.log('[WebSocket] Connection died');
        }
        statusIndicator.className = "status-disconnected";
        statusText.textContent = "Disconnected";
        sendButton.disabled = true;
        
        addSystemMessage("Disconnected from server. Trying to reconnect...");
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
    
    socket.onerror = function(error) {
        console.log(`[WebSocket] Error: ${error.message}`);
        addSystemMessage("Connection error. Please try again later.");
    };
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function addMessage(messageHTML, className) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    messageDiv.innerHTML = messageHTML;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addUserMessage(message) {
    const time = getCurrentTime();
    const html = `${message}<span class="message-time">${time}</span>`;
    addMessage(html, 'user-message');
}

function addBotMessage(message) {
    const time = getCurrentTime();
    // Convert markdown to HTML and sanitize
    const sanitizedHtml = DOMPurify.sanitize(marked.parse(message));
    const html = `${sanitizedHtml}<span class="message-time">${time}</span>`;
    addMessage(html, 'bot-message');
}

function addSystemMessage(message) {
    addMessage(message, 'system-message');
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (message && socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            action: "message",
            content: message
        }));
        
        messageInput.value = '';
        sendButton.disabled = true;
        setTimeout(() => {
            sendButton.disabled = false;
            messageInput.focus();
        }, 50);
    }
}

// Event listeners
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

messageInput.addEventListener('input', function() {
    sendButton.disabled = !messageInput.value.trim() || !socket || socket.readyState !== WebSocket.OPEN;
});

// Connect on page load
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
    addSystemMessage("Welcome to MCP Planner Chat! Type a message to begin.");
});
    """)

# Setup FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Serve static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    agent = None
    async with mcp_app.run() as agent_app:
        agent = Agent(
            name="ChatAgent",
            instruction="""You are an AI assistant that helps with research and analysis using available tools.
                          Answer user queries using the provided context and tools.
                          Be concise, helpful and accurate.""",
            server_names=["mcp-atlassian", "filesystem", "fetch"]
        )
    
    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            
            if json_data["action"] == "message":
                user_message = json_data["content"]
                
                # Echo the user message back to the client
                await manager.send_personal_message(
                    json.dumps({"type": "user", "content": user_message}),
                    websocket
                )
                
                try:
                    # Process the message
                    response = await process_message(user_message, agent, websocket)
                    
                    # Send bot response back to the client
                    await manager.send_personal_message(
                        json.dumps({"type": "bot", "content": response}),
                        websocket
                    )
                    
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({"type": "system", "content": f"Error processing message: {str(e)}"}),
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_analysis_task():
    """Run the original analysis task but with progress updates"""
    async with mcp_app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())
        
        jira_agent = Agent(
            name="AgentChecker",
            instruction="""
                 Go to CONFLUENCE and review space SD. Focus on extracting only essential information:
                 - Project purpose and core requirements
                 - Key stakeholders and objectives
                 - Critical documentation quality metrics
                 
                 Optimize for minimal token usage while maintaining analysis quality.
            """,
            server_names=["mcp-atlassian", "filesystem"]
        )

        async with jira_agent:
            logger.info("Connected to CONFLUENCE server, fetching projects...")
            result = await jira_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Check if the CONFLUENCE server is available
            if not result:
                logger.error("CONFLUENCE server is not available.")
                return
           
        async with jira_agent:
            logger.info("finder: Connected to server, calling list_tools...")
            result = await jira_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Broadcast progress update if any active connections
            if manager.active_connections:
                await manager.broadcast(json.dumps({
                    "type": "system", 
                    "content": "Starting Confluence analysis task..."
                }))

            # Connect to LLM
            llm = await jira_agent.attach_llm(AnthropicAugmentedLLM)

            # Broadcast progress update
            if manager.active_connections:
                await manager.broadcast(json.dumps({
                    "type": "system", 
                    "content": "Connected to LLM, generating analysis..."
                }))

            # Generate analysis
            comprehensive_analysis = await llm.generate_str(
                message="""
                Task: Complete CONFLUENCE Documentation Analysis and DevOps Review
                
                As a Certified DevOps consultant, perform the following comprehensive analysis:
                
                ## Phase 1: Documentation Review
                1. Go to CONFLUENCE project and review the documentation in space SD
                2. Extract project purpose and core requirements
                3. Identify key stakeholders and objectives
                
                ## Phase 2: Quality Assessment
                Evaluate and rate (1-10 scale) the following areas:
                1. **Content Quality**: Completeness, accuracy, and relevance
                2. **Requirements Clarity**: Specificity and testability of requirements
                3. **Implementation Testability**: How easily can the requirements be tested
                4. **Code Maintainability**: Long-term sustainability and documentation
                5. **Operational Reliability**: Stability, monitoring, and error handling
                
                ## Phase 3: Deliverables
                Create a structured markdown report containing:
                - Executive summary with project overview
                - Quality assessment scores with justifications
                - Specific recommendations for improvements
                - Relevant project links and references
                - Risk assessment and mitigation strategies
                
                ## Output Format
                Structure your response as a complete markdown document that can be saved directly to the output folder.
                Include section headers, bullet points, and a summary table of scores.

                ## References
                - Provide list of relevant confluence pages used for evaluation
                - Include any other documentation or resources referenced in the analysis
                
                Return the complete analysis as one comprehensive response ready for file output.
                """
            )
            logger.info(f"Comprehensive analysis completed: {len(comprehensive_analysis)} characters generated")

            # Save the result
            output_path = "output/confluence_devops_analysis" + f"_{int(time.time())}.md"
            try:
                # Ensure output directory exists
                os.makedirs("output", exist_ok=True)
                
                # Save the comprehensive analysis
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(comprehensive_analysis)
                
                logger.info(f"Analysis saved to {output_path}")
                
                # Broadcast completion
                if manager.active_connections:
                    await manager.broadcast(json.dumps({
                        "type": "system", 
                        "content": f"Analysis completed and saved to {output_path}"
                    }))
                
                # Log summary metrics for monitoring token usage
                word_count = len(comprehensive_analysis.split())
                char_count = len(comprehensive_analysis)
                token_estimate = char_count // 4  # Rough token estimation
                logger.info(f"Report metrics: {word_count} words, {char_count} characters, ~{token_estimate} tokens")
                
            except Exception as e:
                logger.error(f"Failed to save analysis: {e}")
                
                # Broadcast error
                if manager.active_connections:
                    await manager.broadcast(json.dumps({
                        "type": "system", 
                        "content": f"Error saving analysis: {str(e)}"
                    }))
                
            return comprehensive_analysis

# Add a route to trigger the analysis task
@app.post("/run_analysis")
async def run_analysis():
    # Start the analysis task in the background
    asyncio.create_task(run_analysis_task())
    return {"status": "Analysis task started"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = Path("output") / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename, media_type='text/markdown')
    return {"error": "File not found"}

@app.get("/list_reports")
async def list_reports():
    output_dir = Path("output")
    if not output_dir.exists():
        return {"reports": []}
    
    reports = []
    for file in output_dir.glob("*.md"):
        reports.append({
            "filename": file.name,
            "created": file.stat().st_mtime,
            "size": file.stat().st_size
        })
    
    # Sort by creation time, newest first
    reports.sort(key=lambda x: x["created"], reverse=True)
    return {"reports": reports}

if __name__ == "__main__":
    # Start token tracking
    token_usage["start_time"] = time.time()
    
    # Run the FastAPI app with uvicorn
    print("Starting MCP Planner Chat UI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
