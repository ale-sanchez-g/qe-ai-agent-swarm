
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

// Connect on page load
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
    setupQuickActionButtons();
    addSystemMessage("Welcome to MCP Planner Chat! Type a message to begin.");
});
    