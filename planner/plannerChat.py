"""
MCP Agent Planner: Interactive Chat UI for LLM and MCP Integration
"""

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

# Add this import for LangChain message types
from memory_manager import session_manager

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM


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
        self.connection_sessions: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Create a session ID for this connection
        session_id = str(uuid.uuid4())
        self.connection_sessions[websocket] = session_id

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def get_session_id(self, websocket: WebSocket) -> str:
        return self.connection_sessions.get(websocket, str(uuid.uuid4()))

manager = ConnectionManager()

async def process_message(user_message: str, agent: Agent = None, websocket: WebSocket = None, session_id: str = None):
    """Process a user message through the MCP agent and LLM with memory"""
    
    # Get conversation memory
    conversation_memory = session_manager.get_or_create_session(session_id)
    
    # Add user message to memory
    conversation_memory.add_user_message(user_message)
    
    if not agent:
        async with mcp_app.run() as agent_app:
            logger = agent_app.logger
            
            agent = Agent(
                name="ChatAgent",
                instruction="""You are an AI assistant that helps with research and analysis using available tools.
                               Answer user queries using the provided context and tools.
                               Be concise, helpful and accurate.
                               """,
                server_names=["mcp-atlassian", "filesystem"]
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
        
        # Get conversation context
        conversation_context = conversation_memory.get_conversation_context()
        recent_messages = conversation_memory.get_recent_messages(5)
        
        # Build context with conversation history
        context_messages = "\n".join([
            f"{'User' if msg.type == 'user' else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        # Generate response with context
        response = await llm.generate_str(
            message=f"""
            Conversation Context:
            {context_messages}
            
            Current User Query: {user_message}
            
            Available tools: {json.dumps(available_tools)}
            
            Respond to the current user query while considering the conversation history.
            Use the available tools when appropriate.
            Review the output folder for any previous context of the conversation.
            If specific information is requested that can be found in Confluence or other sources,
            use the appropriate tool to fetch that information.
            
            Format your response in markdown for better readability.
            """
        )
        
        # Add AI response to memory
        conversation_memory.add_ai_message(response)
        
        # Store all responses in output folder (keep existing behavior)
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Save the response to a file
        response_file = output_dir / f"{session_id}_{uuid.uuid4()}.md"
        with open(response_file, "w") as f:
            f.write(f"# Conversation: {session_id}\n\n")
            f.write(f"## User Query\n{user_message}\n\n")
            f.write(f"## Response\n{response}")

        return response

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
    session_id = manager.get_session_id(websocket)
    
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
                    # Process the message with session context
                    response = await process_message(user_message, agent, websocket, session_id)
                    
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
    for file in output_dir.glob("*.*"):
        reports.append({
            "filename": file.name,
            "created": file.stat().st_mtime,
            "size": file.stat().st_size
        })
    
    # Sort by creation time, newest first
    reports.sort(key=lambda x: x["created"], reverse=True)
    return {"reports": reports}

@app.get("/reports", response_class=HTMLResponse)
async def get_reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/memory/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": list(session_manager.sessions.keys()),
        "count": len(session_manager.sessions)
    }

@app.delete("/memory/session/{session_id}")
async def clear_session(session_id: str):
    """Clear memory for a specific session"""
    if session_id in session_manager.sessions:
        session_manager.sessions[session_id].clear_memory()
        return {"message": f"Session {session_id} memory cleared"}
    return {"error": "Session not found"}

@app.get("/memory/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    if session_id in session_manager.sessions:
        memory = session_manager.sessions[session_id]
        messages = memory.get_recent_messages(50)  # Last 50 messages
        return {
            "session_id": session_id,
            "messages": [
                {
                    "type": msg.type,
                    "content": msg.content
                }
                for msg in messages
            ]
        }
    return {"error": "Session not found"}

if __name__ == "__main__":    
    # Run the FastAPI app with uvicorn
    print("Starting MCP Planner Chat UI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
