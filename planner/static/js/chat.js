let socket;
let currentSessionId = null;
let isRobotAnimationActive = false;
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
            // Remove robot animation when bot responds
            removeRobotAnimation();
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
    // Check if this is a processing message and show robot animation instead
    if (message.includes("Processing your request") || 
        message.includes("Connecting to LLM") || 
        message.includes("processing") ||
        message.toLowerCase().includes("working")) {
        // Only add robot animation if one isn't already active
        if (!isRobotAnimationActive) {
            addRobotAnimation(message);
        }
    } else {
        addMessage(message, 'system-message');
    }
}

function addRobotAnimation(statusText = "Processing your request...") {
    // Prevent multiple robot animations
    if (isRobotAnimationActive) {
        return;
    }
    
    isRobotAnimationActive = true;
    
    const robotMessages = [
        "🤖 Analyzing your request...",
        "🔍 Searching for information...",
        "⚙️ Processing data...",
        "🎯 Almost there...",
        "✨ Finalizing results..."
    ];
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message';
    messageDiv.innerHTML = `
        <div class="robot-animation-container">
            <div class="robot-track">
                <div class="robot">🤖</div>
                <div class="progress-dots">
                    <div class="progress-dot"></div>
                    <div class="progress-dot"></div>
                    <div class="progress-dot"></div>
                </div>
            </div>
            <div class="robot-status-text" id="robot-status">${statusText}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Store reference to this animation for removal later
    messageDiv.classList.add('robot-processing');
    
    // Cycle through different status messages
    let messageIndex = 0;
    const statusElement = messageDiv.querySelector('#robot-status');
    const robot = messageDiv.querySelector('.robot');
    
    const messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % robotMessages.length;
        statusElement.textContent = robotMessages[messageIndex];
        
        // Add different robot states
        robot.className = 'robot';
        if (messageIndex % 3 === 0) {
            robot.classList.add('thinking');
        } else if (messageIndex % 3 === 1) {
            robot.classList.add('working');
        }
    }, 2000);
    
    // Store interval ID so we can clear it later
    messageDiv.intervalId = messageInterval;
}

function removeRobotAnimation() {
    const robotMessages = document.querySelectorAll('.robot-processing');
    robotMessages.forEach(msg => {
        if (msg.intervalId) {
            clearInterval(msg.intervalId);
        }
        // Fade out animation
        msg.style.transition = 'opacity 0.5s ease-out';
        msg.style.opacity = '0';
        setTimeout(() => {
            if (msg.parentNode) {
                msg.parentNode.removeChild(msg);
            }
        }, 500);
    });
    
    // Reset the flag to allow new animations
    isRobotAnimationActive = false;
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
        
        // Show robot animation immediately after sending, but only if one isn't already active
        setTimeout(() => {
            if (!isRobotAnimationActive) {
                addRobotAnimation("🤖 Processing your request...");
            }
        }, 100);
        
        setTimeout(() => {
            sendButton.disabled = false;
            messageInput.focus();
        }, 50);
    }
}

function clearCurrentSession() {
    if (currentSessionId) {
        fetch(`/memory/session/${currentSessionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            addSystemMessage("Conversation memory cleared");
            // Clear local chat display
            chatMessages.innerHTML = '';
            // Reset robot animation flag
            isRobotAnimationActive = false;
        })
        .catch(error => {
            console.error('Error clearing session:', error);
        });
    }
}

function showSessionHistory() {
    if (currentSessionId) {
        window.open(`/memory/session/${currentSessionId}/history`, '_blank');
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

// Custom modal functions
function showModal(title, placeholder, callback) {
    const modal = document.getElementById('customModal');
    const modalTitle = document.getElementById('modal-title');
    const modalInput = document.getElementById('modal-input');
    const submitButton = document.getElementById('modal-submit');
    const cancelButton = document.getElementById('modal-cancel');
    
    // Set title and placeholder
    modalTitle.textContent = title;
    modalInput.placeholder = placeholder;
    modalInput.value = '';
    
    // Show modal
    modal.style.display = 'block';
    
    // Focus on input
    setTimeout(() => {
        modalInput.focus();
    }, 100);
    
    // Handle submit
    const handleSubmit = function() {
        const value = modalInput.value.trim();
        if (value !== '') {
            callback(value);
        }
        modal.style.display = 'none';
        
        // Remove event listeners to prevent duplicates
        submitButton.removeEventListener('click', handleSubmit);
        modalInput.removeEventListener('keypress', handleKeyPress);
        cancelButton.removeEventListener('click', handleCancel);
    };
    
    // Handle cancel
    const handleCancel = function() {
        modal.style.display = 'none';
        
        // Remove event listeners to prevent duplicates
        submitButton.removeEventListener('click', handleSubmit);
        modalInput.removeEventListener('keypress', handleKeyPress);
        cancelButton.removeEventListener('click', handleCancel);
    };
    
    // Handle Enter key
    const handleKeyPress = function(event) {
        if (event.key === 'Enter') {
            handleSubmit();
        }
    };
    
    // Add event listeners
    submitButton.addEventListener('click', handleSubmit);
    modalInput.addEventListener('keypress', handleKeyPress);
    cancelButton.addEventListener('click', handleCancel);
    
    // Close if clicked outside
    window.onclick = function(event) {
        if (event.target == modal) {
            handleCancel();
        }
    };
}

// Handle predefined prompt buttons
function setupQuickActionButtons() {
    const confluenceButton = document.getElementById('confluence-button');
    
    confluenceButton.addEventListener('click', function() {
        showModal(
            'Find Information from Confluence', 
            'Enter the Confluence page name or ID',
            function(pageId) {
                const predefinedPrompt = `I'll help you find information about ${pageId} documentation in Confluence.`;
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        action: "message",
                        content: predefinedPrompt
                    }));
                    
                    // Focus back on the input field
                    setTimeout(() => {
                        messageInput.focus();
                    }, 50);
                }
            }
        );
    });
}

// Setup quick action buttons
function setupProjectSummaryButton() {
    const projectSummaryButton = document.getElementById('project-summary');

    projectSummaryButton.addEventListener('click', function() {
        showModal(
            'Provide Project Summary',
            'Enter the Confluence project name or ID',
            function(projectID) {
                const predefinedPrompt = `Analyze project ${projectID} from Confluence and provide a comprehensive summary. Please:

                        1. List all discovered Confluence pages related to project ${projectID}
                        [For each page found]:
                        - URL:
                        - Key content summary (focus on: objectives, scope, deliverables)

                        2. Synthesize overall project objectives from all sources
                        - Primary goal
                        - Key success metrics
                        - Major constraints/dependencies

                        3. Extract and analyze linked JIRA tickets
                        - List ticket URLs
                        - Status summary
                        - Critical blockers/risks

                        Format output as:
                        [Source Links]
                        [Project Summary: 3-5 bullet points]
                        [Key JIRA Insights]`;
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        action: "message",
                        content: predefinedPrompt
                    }));
                    
                    // Focus back on the input field
                    setTimeout(() => {
                        messageInput.focus();
                    }, 50);
                }
            }
        );
    });
}

// Connect on page load
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
    setupQuickActionButtons();
    setupProjectSummaryButton();
    addSystemMessage("FluxAI Chat + Human in the loop.");
});
