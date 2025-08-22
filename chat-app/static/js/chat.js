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
        this.messageCount = 0;
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

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeInput());

        // Check initial health status
        this.checkHealth();

        // Focus on input
        this.messageInput.focus();

        // Initialize message counter
        this.messageCount = this.chatMessages.querySelectorAll('.message').length;
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
                // Add AI response to chat with formatting
                this.addMessage(data.response, 'assistant');
                this.showToast('Response received successfully', 'success');
            } else {
                // Show error message
                this.addMessage(data.error || 'An error occurred. Please try again.', 'assistant', true);
                this.showToast('Error: ' + (data.error || 'Failed to send message'), 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(
                'I apologize, but I encountered a connection error. Please check your internet connection and try again.', 
                'assistant', 
                true
            );
            this.showToast('Network error. Please check your connection.', 'error');
        } finally {
            this.hideTyping();
        }
    }

    addMessage(content, type, isError = false) {
        this.messageCount++;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message${isError ? ' error-message' : ''}`;
        messageDiv.setAttribute('data-message-id', this.messageCount);

        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const avatarIcon = type === 'user' ? 'bi-person-fill' : 'bi-robot';
        
        // Format the content based on type
        const formattedContent = type === 'assistant' ? this.formatMessage(content) : this.escapeHtml(content);

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    ${formattedContent}
                    <small class="message-time">${timeString}</small>
                </div>
            </div>
        `;

        // Add message with animation
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Add success animation for user messages
        if (type === 'user') {
            setTimeout(() => messageDiv.classList.add('success-animation'), 100);
        }

        // Auto-scroll if user is near bottom
        this.autoScroll();
    }

    formatMessage(content) {
        // Enhanced markdown-like formatting for AI responses
        let formatted = this.escapeHtml(content);

        // Code blocks (```code```)
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code (`code`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold (**text**)
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic (*text*)
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Headers (## Header)
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        
        // Lists
        formatted = formatted.replace(/^\* (.*$)/gm, '<li>$1</li>');
        formatted = formatted.replace(/^- (.*$)/gm, '<li>$1</li>');
        formatted = formatted.replace(/^(\d+)\. (.*$)/gm, '<li>$1. $2</li>');
        
        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*<\/li>)/gs, (match) => {
            if (!match.includes('<ul>') && !match.includes('<ol>')) {
                return '<ul>' + match + '</ul>';
            }
            return match;
        });
        
        // Line breaks
        formatted = formatted.replace(/\n\n/g, '</p><p>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraphs if not already wrapped
        if (!formatted.includes('<p>') && !formatted.includes('<h') && !formatted.includes('<ul>') && !formatted.includes('<pre>')) {
            formatted = '<p>' + formatted + '</p>';
        }

        return formatted;
    }

    showTyping() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'flex';
        this.sendButton.disabled = true;
        this.sendButton.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
        this.sendButton.disabled = false;
        this.sendButton.innerHTML = '<i class="bi bi-send-fill"></i>';
        this.messageInput.focus();
    }

    async clearChat() {
        const confirmMessage = `Are you sure you want to clear the chat history?\n\nThis will remove ${this.messageCount} messages and cannot be undone.`;
        
        if (!confirm(confirmMessage)) {
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
                        message.style.animation = 'fadeOut 0.3s ease-out';
                        setTimeout(() => message.remove(), 300);
                    }
                });
                
                this.messageCount = 1; // Reset to just the welcome message
                this.showToast('Chat history cleared successfully', 'success');
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
                const isHealthy = data.status === 'healthy' && data.aws_connected && data.launchdarkly_connected;
                const status = isHealthy ? 'healthy' : (data.aws_connected && data.launchdarkly_connected ? 'warning' : 'error');
                
                this.updateStatusIndicator(status);
                
                const statusMessage = `
🔍 System Health Check Results:

✅ Overall Status: ${data.status}
${data.aws_connected ? '✅' : '❌'} AWS Bedrock: ${data.aws_connected ? 'Connected' : 'Disconnected'}
${data.launchdarkly_connected ? '✅' : '❌'} LaunchDarkly: ${data.launchdarkly_connected ? 'Connected' : 'Disconnected'}

🕒 Last Check: ${new Date(data.timestamp).toLocaleString()}
                `.trim();
                
                this.showToast(statusMessage, isHealthy ? 'success' : 'warning');
            } else {
                this.updateStatusIndicator('error');
                this.showToast('Health check failed - Unable to reach server', 'error');
            }
        } catch (error) {
            console.error('Health check error:', error);
            this.updateStatusIndicator('error');
            this.showToast('Unable to perform health check - Network error', 'error');
        }
    }

    updateStatusIndicator(status) {
        this.statusIndicator.className = `status-dot me-3 status-${status}`;
        
        // Remove existing animation classes and add pulse for updates
        this.statusIndicator.style.animation = 'none';
        setTimeout(() => {
            this.statusIndicator.style.animation = 'pulse 2s infinite';
        }, 100);
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastMessage = document.getElementById('toast-message');
        const toastHeader = toast.querySelector('.toast-header strong');
        const toastIcon = toast.querySelector('.bi');

        // Set message with proper formatting for multiline
        if (message.includes('\n')) {
            toastMessage.innerHTML = message.split('\n').map(line => 
                line.trim() ? `<div>${this.escapeHtml(line)}</div>` : '<div style="height: 0.5rem;"></div>'
            ).join('');
        } else {
            toastMessage.textContent = message;
        }

        // Set type-specific styling with better icons and colors
        switch (type) {
            case 'success':
                toastHeader.textContent = 'Success';
                toastIcon.className = 'bi bi-check-circle-fill me-2 text-success';
                toast.className = 'toast border-success';
                break;
            case 'error':
                toastHeader.textContent = 'Error';
                toastIcon.className = 'bi bi-exclamation-triangle-fill me-2 text-danger';
                toast.className = 'toast border-danger';
                break;
            case 'warning':
                toastHeader.textContent = 'Warning';
                toastIcon.className = 'bi bi-exclamation-circle-fill me-2 text-warning';
                toast.className = 'toast border-warning';
                break;
            default:
                toastHeader.textContent = 'Information';
                toastIcon.className = 'bi bi-info-circle-fill me-2 text-info';
                toast.className = 'toast border-info';
        }

        // Show toast with longer delay for health checks
        const bsToast = new bootstrap.Toast(toast, {
            delay: type === 'warning' || type === 'error' ? 8000 : 4000
        });
        bsToast.show();
    }

    autoResizeInput() {
        const input = this.messageInput;
        input.style.height = 'auto';
        const newHeight = Math.min(Math.max(input.scrollHeight, 56), 150);
        input.style.height = newHeight + 'px';
        
        // Adjust parent container if needed
        const container = input.closest('.input-group');
        container.style.alignItems = newHeight > 56 ? 'flex-end' : 'stretch';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    autoScroll() {
        const scrollContainer = this.chatMessages;
        const isNearBottom = scrollContainer.scrollTop + scrollContainer.clientHeight >= scrollContainer.scrollHeight - 100;
        
        if (isNearBottom) {
            this.scrollToBottom();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chat app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});

// Handle page visibility change for better UX
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.chatApp) {
        // Page became visible, check health after a delay
        setTimeout(() => {
            window.chatApp.checkHealth();
        }, 1000);
    }
});

// Add fade out animation for better UX
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
    
    .fade-out { animation: fadeOut 0.3s ease-out; }
`;
document.head.appendChild(style);