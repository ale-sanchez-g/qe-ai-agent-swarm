// Chat Application JavaScript

class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.clearChatButton = document.getElementById('clear-chat');
        this.healthCheckButton = document.getElementById('health-check');
        this.debugConfigButton = document.getElementById('debug-config');
        this.logoutButton = document.getElementById('logout-button');
        this.statusIndicator = document.getElementById('status-indicator');
        
        // Mobile menu elements
        this.mobileStatusIndicator = document.getElementById('mobile-status-indicator');
        this.mobileClearChatButton = document.getElementById('mobile-clear-chat');
        this.mobileHealthCheckButton = document.getElementById('mobile-health-check');
        this.mobileDebugConfigButton = document.getElementById('mobile-debug-config');
        this.mobileLogoutButton = document.getElementById('mobile-logout-button');
        this.mobileStatusText = document.querySelector('.mobile-status-text');
        
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

        if (this.clearChatButton) {
            this.clearChatButton.addEventListener('click', () => this.clearChat());
        }
        
        if (this.healthCheckButton) {
            this.healthCheckButton.addEventListener('click', () => this.checkHealth());
        }
        
        // Debug config button might not exist if feature flag is disabled
        if (this.debugConfigButton) {
            this.debugConfigButton.addEventListener('click', () => this.debugConfig());
        }
        
        if (this.logoutButton) {
            this.logoutButton.addEventListener('click', () => this.logout());
        }

        // Mobile menu event listeners
        if (this.mobileClearChatButton) {
            this.mobileClearChatButton.addEventListener('click', () => this.clearChat());
        }
        if (this.mobileHealthCheckButton) {
            this.mobileHealthCheckButton.addEventListener('click', () => this.checkHealth());
        }
        
        // Mobile debug config button might not exist if feature flag is disabled
        if (this.mobileDebugConfigButton) {
            this.mobileDebugConfigButton.addEventListener('click', () => this.debugConfig());
        }
        
        if (this.mobileLogoutButton) {
            this.mobileLogoutButton.addEventListener('click', () => this.logout());
        }

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeInput());

        // Mobile keyboard handling
        this.setupMobileKeyboardHandling();

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
                // Handle authentication errors
                if (response.status === 401) {
                    this.showToast('Session expired. Please login again.', 'error');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    return;
                }
                
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
        
        // Format the content based on type and detect knowledge sources
        let formattedContent;
        let hasKnowledgeContent = false;
        
        if (type === 'assistant') {
            formattedContent = this.formatMessage(content);
            hasKnowledgeContent = this.detectKnowledgeContent(content);
        } else {
            formattedContent = this.escapeHtml(content);
        }

        // Add knowledge indicator if content includes official documentation
        const knowledgeIndicator = hasKnowledgeContent ? 
            '<div class="knowledge-indicator"><i class="bi bi-file-text"></i> Contains official company information</div>' : '';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                ${knowledgeIndicator}
                <div class="message-bubble${hasKnowledgeContent ? ' has-knowledge' : ''}">
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

    detectKnowledgeContent(content) {
        // Check for indicators that the content includes official documentation
        const knowledgeIndicators = [
            '📚 OFFICIAL PRODUCT INFORMATION',
            '📋 SOURCE:',
            '💼 *This information is from official company sources',
            'According to our official product documentation',
            'Our company\'s official information states',
            'from official company sources'
        ];
        
        return knowledgeIndicators.some(indicator => content.includes(indicator));
    }

    formatMessage(content) {
        // Enhanced markdown-like formatting for AI responses
        let formatted = this.escapeHtml(content);

        // Knowledge source indicators with special styling - fix regex patterns
        formatted = formatted.replace(/📚 OFFICIAL PRODUCT INFORMATION[^:]*:/g, 
            '<div class="official-info-header"><i class="bi bi-file-earmark-check"></i> $&</div>');
        
        formatted = formatted.replace(/📋 SOURCE: ([^\n\r]+)/g, 
            '<div class="source-attribution"><i class="bi bi-building"></i> <strong>Source:</strong> $1</div>');
        
        formatted = formatted.replace(/💼 \*([^*]+)\*/g, 
            '<div class="company-disclaimer"><i class="bi bi-shield-check"></i> $&</div>');
        
        formatted = formatted.replace(/🤖 \*([^*]+)\*/g, 
            '<div class="ai-disclaimer"><i class="bi bi-robot"></i> $&</div>');

        // Code blocks (```code```)
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code (`code`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold (**text**)
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic (*text*) - but avoid conflict with disclaimers
        formatted = formatted.replace(/(?<!💼 )\*([^*🤖💼]+)\*(?!\*)/g, '<em>$1</em>');
        
        // Headers (## Header)
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        
        // Lists - improved pattern
        formatted = formatted.replace(/^[\s]*[\*\-] (.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^[\s]*(\d+)\. (.+)$/gm, '<li class="numbered">$1. $2</li>');
        
        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li(?:\s+class="[^"]*")?>[^<]*<\/li>(?:\s*<li(?:\s+class="[^"]*")?>[^<]*<\/li>)*)/g, '<ul>$1</ul>');
        
        // Line breaks - preserve structure better
        formatted = formatted.replace(/\n\s*\n/g, '</p><p>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraphs if not already wrapped
        if (!formatted.includes('<p>') && !formatted.includes('<h') && !formatted.includes('<ul>') && !formatted.includes('<pre>') && !formatted.includes('<div class=')) {
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
                if (response.status === 401) {
                    this.showToast('Session expired. Please login again.', 'error');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    return;
                }
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

    async logout() {
        if (!confirm('Are you sure you want to logout? This will clear your chat history and return you to the login page.')) {
            return;
        }

        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.showToast('Logging out...', 'info');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                this.showToast('Logout failed. Redirecting anyway...', 'warning');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            }
        } catch (error) {
            console.error('Logout error:', error);
            this.showToast('Network error during logout. Redirecting...', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
    }

    async debugConfig() {
        try {
            const response = await fetch('/api/debug');
            const data = await response.json();

            if (response.ok) {
                const debugInfo = `
🔍 Debug Configuration Information:

📋 LaunchDarkly Configuration:
• AI Config Key: ${data.ai_config_key}
• Config Enabled: ${data.config_enabled}
• Model: ${data.config_model || 'None'}
• Provider: ${data.config_provider || 'None'}
• Using Fallback: ${data.using_fallback}
• SDK Initialized: ${data.sdk_initialized}

� Feature Flags:
• Show Debug Config: ${data.feature_flags?.show_debug_config !== undefined ? data.feature_flags.show_debug_config : 'Unknown'}

�👤 User Context:
• User ID: ${data.user_context?.key || 'Unknown'}
• Name: ${data.user_context?.name || 'Unknown'}
• Kind: ${data.user_context?.kind || 'Unknown'}

🌐 Browser Details:
• Browser: ${data.session_info?.browser_details?.browserName || 'Unknown'} ${data.session_info?.browser_details?.browserVersion || ''}
• Platform: ${data.session_info?.browser_details?.platform || 'Unknown'}
• Device: ${data.session_info?.browser_details?.deviceType || 'Unknown'}
• Resolution: ${data.session_info?.browser_details?.screenResolution || 'Unknown'}
• Language: ${data.session_info?.browser_details?.language || 'Unknown'}
• Timezone: ${data.session_info?.browser_details?.timezone || 'Unknown'}

⚙️ Environment:
• LD SDK Key: ${data.environment_vars?.LAUNCHDARKLY_SDK_KEY || 'Not Set'}
• AI Config Key: ${data.environment_vars?.LAUNCHDARKLY_AI_CONFIG_KEY || 'Not Set'}

📅 Session Info:
• Session Start: ${data.session_info?.session_start || 'Unknown'}
                `.trim();
                
                this.showToast(debugInfo, 'info');
            } else {
                if (response.status === 401) {
                    this.showToast('Session expired. Please login again.', 'error');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    return;
                }
                this.showToast('Debug check failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Debug check error:', error);
            this.showToast('Unable to perform debug check - Network error', 'error');
        }
    }

    updateStatusIndicator(status) {
        this.statusIndicator.className = `status-dot me-3 status-${status}`;
        
        // Update mobile status indicator
        if (this.mobileStatusIndicator) {
            this.mobileStatusIndicator.className = `status-dot me-2 status-${status}`;
        }
        
        // Update mobile status text
        if (this.mobileStatusText) {
            const statusText = {
                'healthy': 'System Healthy',
                'warning': 'System Warning',
                'error': 'System Error'
            };
            this.mobileStatusText.textContent = statusText[status] || 'System Ready';
        }
        
        // Remove existing animation classes and add pulse for updates
        this.statusIndicator.style.animation = 'none';
        if (this.mobileStatusIndicator) {
            this.mobileStatusIndicator.style.animation = 'none';
        }
        setTimeout(() => {
            this.statusIndicator.style.animation = 'pulse 2s infinite';
            if (this.mobileStatusIndicator) {
                this.mobileStatusIndicator.style.animation = 'pulse 2s infinite';
            }
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

        // Show toast with longer delay for health checks and debug info
        const bsToast = new bootstrap.Toast(toast, {
            delay: type === 'warning' || type === 'error' || type === 'info' ? 12000 : 4000
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

    setupMobileKeyboardHandling() {
        // Handle mobile viewport changes and keyboard behavior
        let initialViewportHeight = window.innerHeight;
        let isKeyboardOpen = false;

        // Detect mobile devices
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        
        if (!isMobile) return;

        // Handle viewport resize (keyboard open/close)
        const handleViewportChange = () => {
            const currentHeight = window.innerHeight;
            const heightDifference = initialViewportHeight - currentHeight;
            
            // If height decreased significantly, keyboard is likely open
            if (heightDifference > 150 && !isKeyboardOpen) {
                isKeyboardOpen = true;
                document.body.classList.add('keyboard-open');
                
                // Ensure input stays visible when keyboard opens
                setTimeout(() => {
                    this.messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
                
            } else if (heightDifference < 50 && isKeyboardOpen) {
                isKeyboardOpen = false;
                document.body.classList.remove('keyboard-open');
                
                // Reset scroll position when keyboard closes
                setTimeout(() => {
                    this.scrollToBottom();
                }, 100);
            }
        };

        // Listen for viewport changes
        window.addEventListener('resize', handleViewportChange);
        
        // Handle focus/blur events for better UX
        this.messageInput.addEventListener('focus', () => {
            // Small delay to allow for keyboard animation
            setTimeout(() => {
                if (window.innerHeight < initialViewportHeight - 100) {
                    this.messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 300);
        });

        this.messageInput.addEventListener('blur', () => {
            // Reset body position when input loses focus
            setTimeout(() => {
                if (!isKeyboardOpen) {
                    document.body.classList.remove('keyboard-open');
                }
            }, 100);
        });

        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                initialViewportHeight = window.innerHeight;
                isKeyboardOpen = false;
                document.body.classList.remove('keyboard-open');
                this.scrollToBottom();
            }, 500);
        });

        // Visual viewport API support (more accurate for iOS)
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', () => {
                const heightDifference = window.innerHeight - window.visualViewport.height;
                
                if (heightDifference > 150 && !isKeyboardOpen) {
                    isKeyboardOpen = true;
                    document.body.classList.add('keyboard-open');
                } else if (heightDifference < 50 && isKeyboardOpen) {
                    isKeyboardOpen = false;
                    document.body.classList.remove('keyboard-open');
                }
            });
        }
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