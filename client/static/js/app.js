class ChatbotApp {
    constructor() {
        this.ws = null;
        this.token = null;
        this.userName = '';
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.initializeElements();
        this.bindEvents();
        this.testBackendConnection();
    }

    initializeElements() {
        this.loginContainer = document.getElementById('loginContainer');
        this.chatContainer = document.getElementById('chatContainer');
        this.loginForm = document.getElementById('loginForm');
        this.userNameInput = document.getElementById('userName');
        this.loginError = document.getElementById('loginError');
        this.userDisplayName = document.getElementById('userDisplayName');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.statusDot = this.connectionStatus.querySelector('.status-dot');
        this.statusText = this.connectionStatus.querySelector('.status-text');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.sendBtn = document.getElementById('sendBtn');
    }

    bindEvents() {
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.messageForm.addEventListener('submit', (e) => this.handleSendMessage(e));
        this.refreshBtn.addEventListener('click', () => this.refreshChat());
        this.logoutBtn.addEventListener('click', () => this.logout());
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });

        // Handle Enter key in message input
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage(e);
            }
        });
    }

    async testBackendConnection() {
        try {
            const response = await fetch('/test_backend');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateConnectionStatus(true);
            } else {
                this.updateConnectionStatus(false, 'Backend error');
            }
        } catch (error) {
            this.updateConnectionStatus(false, 'Cannot connect to backend');
        }
    }

    updateConnectionStatus(connected, message = '') {
        this.isConnected = connected;
        
        if (connected) {
            this.statusDot.classList.add('connected');
            this.statusText.textContent = 'Connected';
            if (this.sendBtn) this.sendBtn.disabled = false;
        } else {
            this.statusDot.classList.remove('connected');
            this.statusText.textContent = message || 'Disconnected';
            if (this.sendBtn) this.sendBtn.disabled = true;
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const name = this.userNameInput.value.trim();
        if (!name) {
            this.showError('Please enter your name');
            return;
        }

        this.showLoading(true);
        this.clearError();

        try {
            const response = await fetch('/get_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name })
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.token;
                this.userName = data.name;
                this.userDisplayName.textContent = this.userName;
                this.initializeWebSocket();
                this.showChatInterface();
            } else {
                this.showError(data.error || 'Failed to get token');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    initializeWebSocket() {
        if (!this.token) {
            console.error('No token available for WebSocket connection');
            return;
        }

        const wsUrl = `ws://127.0.0.1:3500/chat?token=${this.token}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0;
                // start a lightweight heartbeat to keep connection alive
                this.startHeartbeat();
            };

            this.ws.onmessage = (event) => {
                this.handleBotMessage(event.data);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.updateConnectionStatus(false, 'Disconnected');
                this.hideTypingIndicator();
                this.stopHeartbeat();
                
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.attemptReconnect();
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false, 'Connection error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus(false, 'Connection failed');
        }

        // Add a connection timeout to surface clear failure
        clearTimeout(this.wsConnectTimer);
        this.wsConnectTimer = setTimeout(() => {
            if (!this.isConnected) {
                this.addMessage('Unable to connect to server. Please verify backend is running on ws://localhost:3500 and try again.', 'bot');
            }
        }, 6000);
    }

    startHeartbeat() {
        if (this.heartbeatTimer) return;
        this.heartbeatTimer = setInterval(() => {
            try {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send('\u200b'); // zero-width space as ping
                }
            } catch (_) {}
        }, 30000); // 30s
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    attemptReconnect() {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.initializeWebSocket();
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    handleSendMessage(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.addMessage('Not connected to server. Please wait or refresh.', 'bot');
            return;
        }

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Send message to backend
        this.ws.send(message);
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();
    }

    handleBotMessage(message) {
        this.hideTypingIndicator();
        this.addMessage(message, 'bot');
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        // Clean up markdown formatting and preserve line breaks for readability
        let cleanContent = content
            .replace(/\*\*(.*?)\*\*/g, '$1')  // Remove bold **text**
            .replace(/\*(.*?)\*/g, '$1')      // Remove italic *text*
            .replace(/#{1,6}\s*/g, '')        // Remove headers ###
            .replace(/^\s*[-*]\s*/gm, '• ')   // Convert bullet points to simple bullets
            .replace(/\n/g, '<br>');          // Convert line breaks to HTML
        messageContent.innerHTML = cleanContent;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageContent.appendChild(messageTime);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    showChatInterface() {
        this.loginContainer.style.display = 'none';
        this.chatContainer.style.display = 'flex';
        this.messageInput.focus();
    }

    showError(message) {
        this.loginError.textContent = message;
    }

    clearError() {
        this.loginError.textContent = '';
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    async refreshChat() {
        if (!this.token) return;
        
        this.showLoading(true);
        
        try {
            const response = await fetch('/refresh_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: this.token })
            });

            const data = await response.json();

            if (response.ok) {
                // Clear current messages
                this.messagesContainer.innerHTML = '';
                
                // Add welcome message back
                const welcomeMessage = document.createElement('div');
                welcomeMessage.className = 'welcome-message';
                welcomeMessage.innerHTML = `
                    <i class="fas fa-robot"></i>
                    <p>Hello! I'm your AI assistant. How can I help you today?</p>
                `;
                this.messagesContainer.appendChild(welcomeMessage);
                
                // Reconnect WebSocket
                if (this.ws) {
                    this.ws.close();
                }
                this.initializeWebSocket();
            } else {
                this.showError('Failed to refresh chat');
            }
        } catch (error) {
            this.showError('Network error during refresh');
        } finally {
            this.showLoading(false);
        }
    }

    logout() {
        // Close WebSocket connection
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        // Reset state
        this.token = null;
        this.userName = '';
        this.userNameInput.value = '';
        
        // Clear messages
        this.messagesContainer.innerHTML = '';
        
        // Show login interface
        this.chatContainer.style.display = 'none';
        this.loginContainer.style.display = 'flex';
        this.userNameInput.focus();
        
        // Clear any errors
        this.clearError();
        
        // Update connection status
        this.updateConnectionStatus(false, 'Disconnected');
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatbotApp();
});
