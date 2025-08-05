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

async def process_message(user_message: str, agent: Agent = None, websocket: WebSocket = None):
    """Process a user message through the MCP agent and LLM"""
    
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
        
        # Generate response
        response = await llm.generate_str(
            message=f"""
            User query: {user_message}
            
            Available tools: {json.dumps(available_tools)}
            
            Respond to the user query using the available tools when appropriate.
            Review the output folder for any previous context of the conversation
            If specific information is requested that can be found in Confluence or other sources,
            use the appropriate tool to fetch that information.
            
            Format your response in markdown for better readability.
            """
        )
        
        # Store all responses in output folder
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Save the response to a file
        response_file = output_dir / f"{uuid.uuid4()}.md"
        with open(response_file, "w") as f:
            f.write(response)

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

if __name__ == "__main__":    
    # Run the FastAPI app with uvicorn
    print("Starting MCP Planner Chat UI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
