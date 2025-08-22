// Chat Application JavaScript

class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.clearChatButton = document.getElementById('clear-chat');
        this.healthCheckButton = document.getElementById('health-check');
        this.statusIndicator = document.getElementById('status-indicator');
        
        this.isTyping = false;
        this.init();
    }

    init() {
        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.clearChatButton.addEventListener('click', () => this.clearChat());
        this.healthCheckButton.addEventListener('click', () => this.checkHealth());

        // Auto-resize input
        this.messageInput.addEventListener('input', () => this.autoResizeInput());

        // Check initial health status
        this.checkHealth();

        // Focus on input
        this.messageInput.focus();
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.autoResizeInput();

        // Show typing indicator
        this.showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (response.ok) {
                // Add AI response to chat
                this.addMessage(data.response, 'assistant');
            } else {
                // Show error message
                this.addMessage(data.error || 'An error occurred. Please try again.', 'assistant', true);
                this.showToast('Error: ' + (data.error || 'Failed to send message'), 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error. Please check your connection and try again.', 'assistant', true);
            this.showToast('Network error. Please check your connection.', 'error');
        } finally {
            this.hideTyping();
        }
    }

    addMessage(content, type, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message${isError ? ' error-message' : ''}`;

        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const avatarIcon = type === 'user' ? 'bi-person-fill' : 'bi-robot';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${this.escapeHtml(content)}</p>
                    <small class="message-time">${timeString}</small>
                </div>
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Add success animation for user messages
        if (type === 'user') {
            messageDiv.classList.add('success-animation');
        }
    }

    showTyping() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'flex';
        this.sendButton.disabled = true;
        this.sendButton.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
        this.sendButton.disabled = false;
        this.sendButton.innerHTML = '<i class="bi bi-send"></i>';
        this.messageInput.focus();
    }

    async clearChat() {
        if (!confirm('Are you sure you want to clear the chat history?')) {
            return;
        }

        try {
            const response = await fetch('/api/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                // Clear chat messages except welcome message
                const messages = this.chatMessages.querySelectorAll('.message');
                messages.forEach((message, index) => {
                    if (index > 0) { // Keep the welcome message (first message)
                        message.remove();
                    }
                });
                this.showToast('Chat history cleared', 'success');
            } else {
                this.showToast('Failed to clear chat history', 'error');
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
            this.showToast('Error clearing chat history', 'error');
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            if (response.ok) {
                const status = data.status === 'healthy' ? 'healthy' : 'unhealthy';
                this.updateStatusIndicator(status);
                
                const statusMessage = `
                    Status: ${data.status}
                    AWS Connected: ${data.aws_connected ? '✅' : '❌'}
                    LaunchDarkly Connected: ${data.launchdarkly_connected ? '✅' : '❌'}
                    Last Check: ${new Date(data.timestamp).toLocaleTimeString()}
                `;
                
                this.showToast(statusMessage, status === 'healthy' ? 'success' : 'warning');
            } else {
                this.updateStatusIndicator('error');
                this.showToast('Health check failed', 'error');
            }
        } catch (error) {
            console.error('Health check error:', error);
            this.updateStatusIndicator('error');
            this.showToast('Unable to perform health check', 'error');
        }
    }

    updateStatusIndicator(status) {
        this.statusIndicator.className = 'status-dot me-2';
        
        switch (status) {
            case 'healthy':
                this.statusIndicator.style.backgroundColor = '#28a745';
                break;
            case 'warning':
                this.statusIndicator.style.backgroundColor = '#ffc107';
                break;
            case 'error':
                this.statusIndicator.style.backgroundColor = '#dc3545';
                break;
            default:
                this.statusIndicator.style.backgroundColor = '#6c757d';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastMessage = document.getElementById('toast-message');
        const toastHeader = toast.querySelector('.toast-header strong');
        const toastIcon = toast.querySelector('.bi');

        // Set message
        toastMessage.textContent = message;

        // Set type-specific styling
        switch (type) {
            case 'success':
                toastHeader.textContent = 'Success';
                toastIcon.className = 'bi bi-check-circle me-2';
                toast.className = 'toast border-success';
                break;
            case 'error':
                toastHeader.textContent = 'Error';
                toastIcon.className = 'bi bi-exclamation-circle me-2';
                toast.className = 'toast border-danger';
                break;
            case 'warning':
                toastHeader.textContent = 'Warning';
                toastIcon.className = 'bi bi-exclamation-triangle me-2';
                toast.className = 'toast border-warning';
                break;
            default:
                toastHeader.textContent = 'Info';
                toastIcon.className = 'bi bi-info-circle me-2';
                toast.className = 'toast border-info';
        }

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    autoResizeInput() {
        const input = this.messageInput;
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chat app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

// Handle page visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Page became visible, check health
        setTimeout(() => {
            if (window.chatApp) {
                window.chatApp.checkHealth();
            }
        }, 1000);
    }
});

// Store app instance globally for debugging
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});