"""
MCP Agent Planner: Interactive Chat UI for LLM and MCP Integration

This module provides a FastAPI-based web interface for interacting with MCP agents.
It includes conversation memory management, WebSocket communication, and file management capabilities.
"""

import json
import random
import uuid
import os
import logging
from typing import Dict, List
from pathlib import Path
import time
from datetime import datetime

# Configure structured logging for Dynatrace OTLP integration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_agent.planner_chat")

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi import Query

# Local imports
from memory_manager import session_manager
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from long_term_memory import LongTermMemory

# LangChain imports for message types
from langchain_core.messages import HumanMessage

# LaunchDarkly AI Config
import ldclient
from ldclient import Context
from ldclient.config import Config

try:
    from ldai.client import LDAIClient
    try:
        from ldai.client import AIConfig, ModelConfig, LDMessage, ProviderConfig
    except ImportError:
        from ldai.types import AIConfig, ModelConfig, LDMessage, ProviderConfig
    try:
        from ldai.tracker import TokenUsage
    except ImportError:
        TokenUsage = None
    LDAI_AVAILABLE = True
except ImportError:
    LDAIClient = None
    AIConfig = None
    ModelConfig = None
    LDMessage = None
    ProviderConfig = None
    TokenUsage = None
    LDAI_AVAILABLE = False

# Initialize LaunchDarkly client for AI integration
# Get SDK key from env variable
sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
if not sdk_key or not LDAI_AVAILABLE:
    if not sdk_key:
        print("Warning: LAUNCHDARKLY_SDK_KEY not found in environment variables")
    if not LDAI_AVAILABLE:
        print("Warning: LaunchDarkly AI SDK not available in this environment")
    print("LaunchDarkly features will be disabled")
    ai_chat_config = None
    tracker = None
else:
    try:
        ldclient.set_config(Config(sdk_key))
        
        # Wait for the client to initialize
        if ldclient.get().is_initialized():
            print("LaunchDarkly client initialized successfully")
        else:
            print("Warning: LaunchDarkly client failed to initialize")
            
        aiclient = LDAIClient(ldclient.get())
        # List of 20 pilot users
        array = ["user-1", "user-2", "user-3", "user-4", "user-5", "user-6", "user-7", "user-8", "user-9", "user-10", "user-11", "user-12", "user-13", "user-14", "user-15", "user-16", "user-17", "user-18", "user-19", "user-20"]

        # select random user
        user_id = random.choice(array)

        context = Context.builder(f"chat-bot-{user_id}") \
            .set("firstName", user_id) \
            .set("lastName", "Smith") \
            .build()

        # Fall back to default configuration if needed
        fallback_value = AIConfig(
            enabled=True,
            model=ModelConfig(
                name="claude-3-5-haiku-20241022",
                parameters={"temperature": 0.8},
            ),
            messages=[LDMessage(role="system", content="You are an AI assistant that helps with research and analysis using available tools. Answer user queries using the provided context and tools. Be concise, helpful and accurate.")],
            provider=ProviderConfig(name="anthropic"),
        )

        ai_chat_config, tracker = aiclient.config('master-prompt', context, fallback_value)
        print(f"LaunchDarkly AI config retrieved: {ai_chat_config.enabled}")
        
        # Debug: Print the system message content
        if ai_chat_config.messages and len(ai_chat_config.messages) > 0:
            print(f"System message from LaunchDarkly config: {ai_chat_config.messages[0].content[:100]}...")  # Print first 100 chars
        else:
            print("No system message found in LaunchDarkly config")
            
    except Exception as e:
        print(f"Error initializing LaunchDarkly: {e}")
        print("Falling back to default configuration")
        ai_chat_config = None
        tracker = None

# Initialize the MCP application with default configuration
mcp_app = MCPApp(name="mcp-agent-research")

# Initialize FastAPI application with full OpenAPI configuration
app = FastAPI(
    title="Planner Chat UI API",
    description="""
    Interactive Chat UI for LLM and MCP Integration
    
    This API provides a FastAPI-based web interface for interacting with MCP agents.
    It includes conversation memory management, WebSocket communication, and file management capabilities.
    
    ## Features
    - Interactive web chat interface with WebSocket communication
    - Conversation memory management with SQLite backend
    - Multi-MCP server integration (Atlassian, filesystem, fetch)
    - LaunchDarkly AI integration for dynamic configuration
    - Session management for multiple concurrent users
    - File management for downloading and viewing reports
    - Real-time status updates and system messages
    """,
    version="1.0.0",
    contact={
        "name": "QE AI Agent Swarm Team",
        "email": "alejandro.sanchez-giraldo@devops1.com.au"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Chat Interface",
            "description": "Main chat interface and health endpoints"
        },
        {
            "name": "File Management", 
            "description": "File download and report management endpoints"
        },
        {
            "name": "Memory Management",
            "description": "Session and conversation memory management"
        }
    ]
)

# Setup directory structure for templates and static files
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
css_dir = static_dir / "css"
css_dir.mkdir(exist_ok=True)
js_dir = static_dir / "js"
js_dir.mkdir(exist_ok=True)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory=str(templates_dir))

# WebSocket connection manager for handling multiple client connections
class ConnectionManager:
    """
    Manages WebSocket connections and session mapping for the chat interface.
    
    Handles connection lifecycle, message broadcasting, and session management
    for multiple concurrent users.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_sessions: Dict[WebSocket, str] = {}
        self.connection_users: Dict[WebSocket, str] = {}  # Track user_id per connection
        self.connection_requests: Dict[WebSocket, str] = {}  # Track request_id per connection
        self.message_counts: Dict[str, int] = {}  # Track message count per session

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection and assign a session ID."""
        await websocket.accept()
        self.active_connections.append(websocket)
        # Create a unique session ID and user ID for this connection
        session_id = str(uuid.uuid4())
        user_id = f"user_{random.randint(1, 20)}"  # Use same user list from LaunchDarkly config
        request_id = str(uuid.uuid4())
        
        self.connection_sessions[websocket] = session_id
        self.connection_users[websocket] = user_id
        self.connection_requests[websocket] = request_id
        self.message_counts[session_id] = 0  # Initialize message counter
        
        # Log connection
        logger.info("WebSocket connection established", extra={
            "data": {
                "type": "connection_start",
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection and clean up session data."""
        session_id = self.connection_sessions.get(websocket)
        user_id = self.connection_users.get(websocket)
        
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.connection_sessions:
            # Log disconnection
            logger.info("WebSocket connection closed", extra={
                "data": {
                    "type": "connection_end",
                    "session_id": session_id,
                    "user_id": user_id,
                    "messages_in_session": self.message_counts.get(session_id, 0),
                    "timestamp": datetime.now().isoformat()
                }
            })
            del self.connection_sessions[websocket]
        
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        if websocket in self.connection_requests:
            del self.connection_requests[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Send a message to all active WebSocket connections."""
        for connection in self.active_connections:
            await connection.send_text(message)

    def get_session_id(self, websocket: WebSocket) -> str:
        """Get the session ID associated with a WebSocket connection."""
        return self.connection_sessions.get(websocket, str(uuid.uuid4()))
    
    def get_user_id(self, websocket: WebSocket) -> str:
        """Get the user ID associated with a WebSocket connection."""
        return self.connection_users.get(websocket, "anonymous")
    
    def get_request_id(self, websocket: WebSocket) -> str:
        """Get the request ID associated with a WebSocket connection."""
        return self.connection_requests.get(websocket, str(uuid.uuid4()))

    def increment_message_count(self, session_id: str) -> int:
        """Increment and return the message count for a session"""
        self.message_counts[session_id] = self.message_counts.get(session_id, 0) + 1
        return self.message_counts[session_id]

    def get_message_count(self, session_id: str) -> int:
        """Get the current message count for a session"""
        return self.message_counts.get(session_id, 0)

# Global connection manager instance
manager = ConnectionManager()

# Initialize Long-Term Memory (graceful fallback if deps are missing)
try:
    ltm = LongTermMemory(
        persist_dir=Path(__file__).parent / "memory_index",
        collection_name="planner_memories"
    )
    print("Long-term memory enabled (Chroma + sentence-transformers).")
    # Optional: ingest existing reports once at startup
    # reports_dir = Path(__file__).parent / "output"
    # if reports_dir.exists():
    #     try:
    #         count = ltm.ingest_folder(reports_dir, glob_pattern="*.md", doc_type="report")
    #         if count:
    #             print(f"Ingested {count} report file(s) into long-term memory.")
    #     except Exception as e:
    #         print(f"[WARN] Initial ingest failed: {e}")
    # Ingest curated RAG knowledge base (markdown + text)
    rag_dir = Path(__file__).parent / "rag"
    if rag_dir.exists():
        try:
            total = 0
            total += ltm.ingest_folder(rag_dir, glob_pattern="**/*.md", doc_type="knowledge")
            total += ltm.ingest_folder(rag_dir, glob_pattern="**/*.txt", doc_type="knowledge")
            if total:
                print(f"Ingested {total} knowledge file(s) into long-term memory.")
        except Exception as e:
            print(f"[WARN] Knowledge ingest failed: {e}")
except Exception as e:
    ltm = None
    print(f"Long-term memory disabled: {e}")

async def process_message(user_message: str, agent: Agent = None, websocket: WebSocket = None, session_id: str = None, user_id: str = None, request_id: str = None):
    """
    Process a user message through the MCP agent and LLM with conversation memory.
    
    Args:
        user_message: The user's input message
        agent: Optional pre-initialized Agent instance
        websocket: WebSocket connection for real-time updates
        session_id: Session identifier for conversation context
        user_id: User identifier for tracking
        request_id: Request ID for distributed tracing
        
    Returns:
        str: The AI-generated response
    """
    
    # Generate IDs if not provided
    if not request_id:
        request_id = str(uuid.uuid4())
    if not user_id:
        user_id = "anonymous"
    
    # Log user prompt at reception
    logger.info("User prompt received", extra={
        "data": {
            "type": "user_prompt",
            "content": user_message[:500],
            "content_length": len(user_message),
            "session_id": session_id,
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Retrieve or create conversation memory for this session
    conversation_memory = session_manager.get_or_create_session(session_id, user_id)
    conversation_memory.set_user_context(user_id, request_id)
    
    # Initialize agent if not provided
    if not agent:
        async with mcp_app.run() as agent_app:
            agent = Agent(
                name="ChatAgent",
                instruction="""You are an AI assistant that helps with research and analysis using available tools.
                               Answer user queries using the provided context and tools.
                               Be concise, helpful and accurate.
                               """,
                server_names=["mcp-atlassian", "fetch"]
            )
    
    async with agent:
        # Get available tools for context
        tools_result = await agent.list_tools()
        available_tools = tools_result.model_dump() if tools_result else {}
        
        # Log tool availability
        tool_count = len(available_tools.get("tools", []))
        logger.info("Tools available", extra={
            "data": {
                "type": "tools_available",
                "tool_count": tool_count,
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Send status update via WebSocket
        if websocket:
            await manager.send_personal_message(
                json.dumps({"type": "system", "content": "🤖 Connecting to LLM..."}),
                websocket
            )
        
        # Connect to the LLM
        llm = await agent.attach_llm(AnthropicAugmentedLLM)
        
        # Send processing status update
        if websocket:
            await manager.send_personal_message(
                json.dumps({"type": "system", "content": "🔍 Processing your request..."}),
                websocket
            )
        
        # Build conversation context from memory
        conversation_context = conversation_memory.get_full_conversation_context()
        
        # Retrieve long-term context (RAG) for this query
        retrieved_snippets = []
        if ltm:
            try:
                hits = ltm.search(user_message, k=5)
                for h in hits:
                    meta = h.get("metadata", {})
                    prefix = f"[{meta.get('type','memo')}] {meta.get('filename', meta.get('path',''))}".strip()
                    retrieved_snippets.append(f"{prefix}\n{h['text']}")
            except Exception as e:
                logger.warning("LTM retrieval failed", extra={
                    "data": {
                        "type": "ltm_error",
                        "error": str(e),
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                print(f"[WARN] LTM retrieval failed: {e}")
        
        retrieved_context = "\n\n---\n".join(retrieved_snippets[:5]) if retrieved_snippets else ""
        
        # Log RAG retrieval
        logger.info("RAG context retrieved", extra={
            "data": {
                "type": "rag_retrieval",
                "snippet_count": len(retrieved_snippets),
                "context_length": len(retrieved_context),
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })

        # Debug logging
        print(f"[DEBUG] Session {session_id}: Processing message {len(conversation_memory.messages)//2 + 1}")
        print(f"[DEBUG] Context length: {len(conversation_context)} characters")

        # Get system prompt from LaunchDarkly or use default
        system_prompt = ""
        if ai_chat_config and ai_chat_config.messages and len(ai_chat_config.messages) > 0:
            system_prompt = ai_chat_config.messages[0].content
            print(f"[DEBUG] [1123] Using LaunchDarkly system prompt: {system_prompt[:100]}...")
        else:
            system_prompt = """ONLY RESPOND WITH `LET ME CONNECT YOU WITH A HUMAN`"""
            print("[DEBUG] Using default system prompt")
        
        # Log system prompt
        logger.info("System prompt prepared", extra={
            "data": {
                "type": "system_prompt",
                "system_prompt": system_prompt[:500],
                "system_prompt_length": len(system_prompt),
                "source": "launchdarkly" if ai_chat_config else "default",
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })

        # Generate AI response with full context
        full_message = f"""
        Conversation Context:
        {conversation_context}

        Retrieved Knowledge:
        {retrieved_context if retrieved_context else '(none)'}

        Current User Query: {user_message}

        Available tools: {json.dumps(available_tools)}

        {system_prompt}
        """
        
        # Log LLM request
        logger.info("LLM request prepared", extra={
            "data": {
                "type": "llm_request",
                "request_length": len(full_message),
                "context_length": len(conversation_context),
                "retrieved_context_length": len(retrieved_context),
                "tool_count": len(available_tools.get("tools", [])),
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })

        response = await llm.generate_str(message=full_message)
        
        # Log LLM response
        logger.info("LLM response generated", extra={
            "data": {
                "type": "llm_response",
                "response_length": len(response),
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Track token usage if LaunchDarkly tracker is available
        if tracker and TokenUsage:
            try:
                # Create an instance of TokenUsage with actual values from the model generation
                input_tokens = len(full_message.split()) * 1.3
                output_tokens = len(response.split()) * 1.3
                total_tokens = int(input_tokens + output_tokens)
                
                tokens = TokenUsage(total_tokens, int(input_tokens), int(output_tokens))
                tracker.track_tokens(tokens)
                
                # Log token tracking
                logger.info("Tokens tracked", extra={
                    "data": {
                        "type": "token_usage",
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                        "total_tokens": total_tokens,
                        "session_id": session_id,
                        "user_id": user_id,
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                print(f"[DEBUG] Token usage tracked - Input: {int(input_tokens)}, Output: {int(output_tokens)}, Total: {total_tokens}")
            except Exception as e:
                print(f"Error tracking token usage: {e}")
        elif tracker and not TokenUsage:
            print("[WARN] TokenUsage not available; skipping token tracking")
        
        # Track the interaction if LaunchDarkly is available
        if tracker:
            try:
                tracker.track_success()
            except Exception as e:
                print(f"Error tracking LaunchDarkly interaction: {e}")

        # Record the full turn to keep summary accurate and persist to SQLite
        try:
            conversation_memory.record_turn(user_message, response, user_id=user_id, request_id=request_id)
        except Exception as e:
            logger.error("Failed to record turn", extra={
                "data": {
                    "type": "error",
                    "error": str(e),
                    "session_id": session_id,
                    "user_id": user_id,
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            try:
                conversation_memory.add_user_message(user_message, user_id=user_id, request_id=request_id)
                conversation_memory.add_ai_message(response, request_id=request_id)
            except Exception as e2:
                print(f"[ERROR] Failed to persist conversation turn: {e2}")
        
        # Save response to output file for persistence
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        response_file = output_dir / f"{session_id}_{uuid.uuid4()}.md"
        with open(response_file, "w") as f:
            f.write(f"# Conversation: {session_id}\n\n")
            f.write(f"## User Query\n{user_message}\n\n")
            f.write(f"## Response\n{response}")

        # Log file saved
        logger.info("Response file saved", extra={
            "data": {
                "type": "file_saved",
                "filename": response_file.name,
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        })

        # Persist this turn in long-term memory
        if ltm:
            try:
                ltm.upsert(
                    texts=[f"Q: {user_message}\nA: {response}"],
                    metadatas=[{
                        "type": "dialogue",
                        "session_id": session_id,
                        "user_id": user_id,
                        "created_at": int(time.time())
                    }],
                    ids=[f"turn::{session_id}::{uuid.uuid4()}"]
                )
                logger.info("LTM upserted", extra={
                    "data": {
                        "type": "ltm_upsert",
                        "session_id": session_id,
                        "user_id": user_id,
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception as e:
                logger.warning("LTM upsert failed", extra={
                    "data": {
                        "type": "ltm_error",
                        "error": str(e),
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                print(f"[WARN] LTM upsert failed: {e}")

        return response

# FastAPI Route Handlers

@app.get("/", response_class=HTMLResponse, tags=["Chat Interface"], summary="Get main chat interface")
async def get_chat_page(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health", tags=["Chat Interface"], summary="Health check endpoint")
async def health_check():
    """Health check endpoint for monitoring service status."""
    return {"status": "ok"}

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# WebSocket endpoint for real-time chat communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handle WebSocket connections for real-time chat communication.
    
    Manages the lifecycle of chat sessions, processes messages,
    and maintains conversation state for connected clients.
    """
    await manager.connect(websocket)
    session_id = manager.get_session_id(websocket)
    user_id = manager.get_user_id(websocket)
    request_id = manager.get_request_id(websocket)
    
    # Ensure mapping uses the chosen session_id
    manager.connection_sessions[websocket] = session_id
    
    # Initialize session in session_manager with user_id
    session_manager.get_or_create_session(session_id, user_id)
    
    # Initialize agent for this session
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
            # Receive message from client
            data = await websocket.receive_text()
            json_data = json.loads(data)
            
            if json_data["action"] == "message":
                user_message = json_data["content"]
                
                # Generate new request ID for this message
                message_request_id = str(uuid.uuid4())
                
                # Increment message counter
                message_count = manager.increment_message_count(session_id)
                
                # Log message received from client
                logger.info("Message received from client", extra={
                    "data": {
                        "type": "message_received",
                        "session_id": session_id,
                        "user_id": user_id,
                        "request_id": message_request_id,
                        "message_number": message_count,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                print(f"[DEBUG] Session {session_id}: Message #{message_count} received")
                
                # Echo user message back to client for UI consistency
                await manager.send_personal_message(
                    json.dumps({
                        "type": "user", 
                        "content": user_message,
                        "message_count": message_count
                    }),
                    websocket
                )
                
                try:
                    # Process message with full session context and user tracking
                    response = await process_message(
                        user_message, 
                        agent, 
                        websocket, 
                        session_id,
                        user_id=user_id,
                        request_id=message_request_id
                    )
                    
                    # Send AI response back to client
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "bot", 
                            "content": response,
                            "message_count": message_count
                        }),
                        websocket
                    )
                    
                    # Log successful response
                    logger.info("Response sent to client", extra={
                        "data": {
                            "type": "response_sent",
                            "session_id": session_id,
                            "user_id": user_id,
                            "request_id": message_request_id,
                            "message_number": message_count,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
                except Exception as e:
                    # Handle processing errors gracefully
                    error_msg = f"Error processing message: {str(e)}"
                    
                    logger.error("Message processing failed", extra={
                        "data": {
                            "type": "error",
                            "session_id": session_id,
                            "user_id": user_id,
                            "request_id": message_request_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "system", 
                            "content": error_msg,
                            "message_count": message_count
                        }),
                        websocket
                    )
    
    except WebSocketDisconnect:
        # Clean up when client disconnects
        manager.disconnect(websocket)

# File Management Endpoints

@app.get("/download/{filename}", tags=["File Management"], summary="Download a specific file")
async def download_file(filename: str):
    """
    Download a specific file from the output directory.
    
    Args:
        filename: Name of the file to download
        
    Returns:
        FileResponse with the requested file or error message
    """
    file_path = Path("output") / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename, media_type='text/markdown')
    return {"error": "File not found"}

@app.get("/report/{filename}", tags=["File Management"], summary="Get report content")
async def get_report_content(filename: str):
    """
    Get the content of a specific report file from the output directory.
    
    Args:
        filename: Name of the report file to read
        
    Returns:
        JSON object containing the file content, metadata, or error message
    """
    file_path = Path("output") / filename
    if not file_path.exists():
        return {"error": "File not found"}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Get file metadata
        stat = file_path.stat()
        
        return {
            "filename": filename,
            "content": content,
            "size": stat.st_size,
            "created": stat.st_mtime,
            "modified": stat.st_mtime
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

@app.get("/list_reports", tags=["File Management"], summary="List all available reports")
async def list_reports():
    """
    List all available report files in the output directory.
    
    Returns:
        JSON object containing list of reports with metadata
    """
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

@app.get("/reports", response_class=HTMLResponse, tags=["File Management"], summary="Get reports viewing interface")
async def get_reports_page(request: Request):
    """Serve the reports viewing interface."""
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/view", response_class=HTMLResponse, tags=["File Management"], summary="View report content interface")
async def get_report_view_page(request: Request):
    """Serve the report content viewing interface."""
    return templates.TemplateResponse("report_view.html", {"request": request})

# Memory Management Endpoints

@app.get("/memory/sessions", tags=["Memory Management"], summary="List active conversation sessions")
async def list_sessions():
    """
    List all active conversation sessions.
    
    Returns:
        JSON object with session IDs and count
    """
    return {
        "sessions": list(session_manager.sessions.keys()),
        "count": len(session_manager.sessions)
    }

@app.delete("/memory/session/{session_id}", tags=["Memory Management"], summary="Clear session memory")
async def clear_session(session_id: str):
    """
    Clear conversation memory for a specific session.
    
    Args:
        session_id: ID of the session to clear
        
    Returns:
        Success or error message
    """
    if session_id in session_manager.sessions:
        session_manager.sessions[session_id].clear_memory()
        return {"message": f"Session {session_id} memory cleared"}
    return {"error": "Session not found"}

@app.get("/memory/session/{session_id}/history", tags=["Memory Management"], summary="Get session conversation history")
async def get_session_history(session_id: str):
    """
    Retrieve conversation history for a specific session.
    
    Args:
        session_id: ID of the session to retrieve
        
    Returns:
        JSON object with session history or error message
    """
    if session_id in session_manager.sessions:
        memory = session_manager.sessions[session_id]
        messages = memory.get_recent_messages_smart(50)  # Last 50 messages with smart windowing
        return {
            "session_id": session_id,
            "conversation_context": memory.get_full_conversation_context(),
            "messages": [
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content
                }
                for msg in messages
            ]
        }
    return {"error": "Session not found"}

@app.get("/memory/session/{session_id}/message_count", tags=["Memory Management"], summary="Get message count for session")
async def get_session_message_count(session_id: str):
    """Get the number of messages sent in a specific session."""
    count = manager.get_message_count(session_id)
    return {
        "session_id": session_id,
        "message_count": count
    }

@app.get("/memory/total_messages", tags=["Memory Management"], summary="Get total message count across all sessions")
async def get_total_message_count():
    """Get the total number of messages across all sessions."""
    total = sum(manager.message_counts.values())
    return {
        "total_messages": total,
        "active_sessions": len(manager.message_counts),
        "session_counts": manager.message_counts
    }

@app.get("/memory/longterm/search", tags=["Memory Management"], summary="Search long-term memory (RAG index)")
async def search_longterm(q: str = Query(..., min_length=2), k: int = 5):
    """Semantic search across the long-term memory index."""
    if not ltm:
        return {"error": "Long-term memory not available"}
    try:
        results = ltm.search(q, k=k)
        return {
            "query": q,
            "results": [
                {
                    "id": r.get("id"),
                    "distance": r.get("distance"),
                    "metadata": r.get("metadata"),
                    "preview": (r.get("text") or "")[:400]
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

# Debug Endpoints

@app.get("/debug/tools", tags=["Debug"], summary="List available MCP tools")
async def list_available_tools():
    """
    List all available tools from connected MCP servers.
    
    Returns:
        JSON object with tools from each server
    """
    try:
        async with mcp_app.run() as agent_app:
            agent = Agent(
                name="DebugAgent",
                instruction="Debug agent for listing tools",
                server_names=["mcp-atlassian", "filesystem", "fetch"]
            )
            
            async with agent:
                # Get available tools
                tools_result = await agent.list_tools()
                
                # Get more detailed server information
                server_status = {}
                connected_servers = []
                failed_servers = []
                
                if hasattr(agent, 'mcp_aggregator') and hasattr(agent.mcp_aggregator, 'server_managers'):
                    for server_name, manager in agent.mcp_aggregator.server_managers.items():
                        try:
                            # Check if server is actually connected
                            if hasattr(manager, 'client') and manager.client:
                                connected_servers.append(server_name)
                                server_status[server_name] = "connected"
                            else:
                                failed_servers.append(server_name)
                                server_status[server_name] = "disconnected"
                        except Exception as e:
                            failed_servers.append(server_name)
                            server_status[server_name] = f"error: {str(e)}"
                
                if tools_result:
                    tools_data = tools_result.model_dump()
                    
                    # Group tools by server (based on tool name prefixes)
                    tools_by_server = {}
                    for tool in tools_data.get("tools", []):
                        tool_name = tool.get("name", "")
                        if tool_name.startswith("fetch_"):
                            server = "fetch"
                        elif tool_name.startswith("filesystem_"):
                            server = "filesystem"
                        elif tool_name.startswith("atlassian_") or tool_name.startswith("jira_") or tool_name.startswith("confluence_"):
                            server = "mcp-atlassian"
                        else:
                            server = "unknown"
                        
                        if server not in tools_by_server:
                            tools_by_server[server] = []
                        tools_by_server[server].append(tool)
                    
                    return {
                        "status": "success",
                        "tools": tools_data,
                        "tool_count": len(tools_data.get("tools", [])),
                        "tools_by_server": tools_by_server,
                        "server_status": server_status,
                        "connected_servers": connected_servers,
                        "failed_servers": failed_servers,
                        "requested_servers": ["mcp-atlassian", "filesystem", "fetch"]
                    }
                else:
                    return {
                        "status": "no_tools",
                        "message": "No tools available or agent not properly initialized",
                        "server_status": server_status,
                        "connected_servers": connected_servers,
                        "failed_servers": failed_servers,
                        "requested_servers": ["mcp-atlassian", "filesystem", "fetch"]
                    }
                    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list tools: {str(e)}",
            "error_type": type(e).__name__
        }

# Application Entry Point

if __name__ == "__main__":    
    """
    Start the FastAPI application server.
    
    Runs the MCP Planner Chat UI on all interfaces (0.0.0.0) at port 8000.
    This allows the application to be accessible from other machines on the network.
    """
    print("Starting MCP Planner Chat UI server...")
    print("Server will be available at: http://localhost:8000")
    print("Health check endpoint: http://localhost:8000/health")
    print("Reports interface: http://localhost:8000/reports")
    print("API Documentation: http://localhost:8000/docs")
    print("ReDoc Documentation: http://localhost:8000/redoc")
    print("OpenAPI JSON: http://localhost:8000/openapi.json")
    uvicorn.run(app, host="0.0.0.0", port=8000)
