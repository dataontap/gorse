
// Help Desk Client-Side Functions
class HelpDeskClient {
    constructor() {
        this.currentSession = null;
        this.isAIEnabled = true;
        this.sessionStartTime = null;
    }

    async startHelpSession() {
        try {
            const userData = this.getCurrentUserData();
            
            const response = await fetch('/api/help/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId: userData.userId,
                    firebaseUid: userData.firebaseUid,
                    pageUrl: window.location.href
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.currentSession = {
                    sessionId: result.session_id,
                    helpSessionId: result.help_session_id,
                    jiraTicket: result.jira_ticket
                };
                this.sessionStartTime = new Date();
                console.log('Help session started:', this.currentSession);
                
                // Show Jira ticket info if available
                if (result.jira_ticket) {
                    this.showJiraTicketInfo(result.jira_ticket);
                }
                
                return this.currentSession;
            } else {
                console.error('Failed to start help session:', result.message);
                return null;
            }
        } catch (error) {
            console.error('Error starting help session:', error);
            return null;
        }
    }

    async endHelpSession() {
        if (!this.currentSession) return;

        try {
            const response = await fetch('/api/help/end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.currentSession.sessionId
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                console.log('Help session ended:', result);
                this.showSessionSummary(result);
                this.currentSession = null;
                this.sessionStartTime = null;
            } else {
                console.error('Failed to end help session:', result.message);
            }
        } catch (error) {
            console.error('Error ending help session:', error);
        }
    }

    async trackInteraction(type, data = {}) {
        if (!this.currentSession) return;

        try {
            const response = await fetch('/api/help/interact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.currentSession.sessionId,
                    type: type,
                    ...data
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                // Handle toggle detection
                if (result.is_toggle) {
                    this.showToggleWarning(result.click_count);
                } else if (result.click_count > 1) {
                    this.showGenuineHelpOptions();
                }
            }
        } catch (error) {
            console.error('Error tracking interaction:', error);
        }
    }

    async getAIAssistance(query) {
        try {
            const userData = this.getCurrentUserData();
            
            const response = await fetch('/api/help/ai-assist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    sessionId: this.currentSession?.sessionId,
                    userId: userData.userId,
                    firebaseUid: userData.firebaseUid,
                    pageUrl: window.location.href
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                return result.response;
            } else {
                return result.response || 'Sorry, I could not process your request right now.';
            }
        } catch (error) {
            console.error('Error getting AI assistance:', error);
            return 'Sorry, there was an error processing your request.';
        }
    }

    async startGeminiLive() {
        try {
            if (!this.currentSession) {
                alert('Please start a help session first');
                return;
            }

            const userData = this.getCurrentUserData();

            // First, get ephemeral token
            const tokenResponse = await fetch('/api/help/gemini-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.currentSession.sessionId
                })
            });

            const tokenResult = await tokenResponse.json();
            
            if (tokenResult.status !== 'success') {
                throw new Error(tokenResult.message || 'Failed to get ephemeral token');
            }

            // Start live session
            const liveResponse = await fetch('/api/help/gemini-live-start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.currentSession.sessionId,
                    ephemeralToken: tokenResult.token,
                    userId: userData.userId,
                    firebaseUid: userData.firebaseUid,
                    pageUrl: window.location.href
                })
            });

            const liveResult = await liveResponse.json();
            
            if (liveResult.status === 'success') {
                this.initializeGeminiWebSocket(liveResult.ws_url, liveResult.config);
                this.showGeminiLiveInterface();
            } else {
                throw new Error(liveResult.message || 'Failed to start live session');
            }

        } catch (error) {
            console.error('Error starting Gemini Live:', error);
            alert('Failed to start live conversation: ' + error.message);
        }
    }

    initializeGeminiWebSocket(wsUrl, config) {
        try {
            this.geminiWebSocket = new WebSocket(wsUrl);
            
            this.geminiWebSocket.onopen = () => {
                console.log('Gemini Live WebSocket connected');
                // Send initial configuration
                this.geminiWebSocket.send(JSON.stringify(config));
                this.updateGeminiStatus('Connected', 'success');
            };

            this.geminiWebSocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleGeminiMessage(data);
                } catch (e) {
                    console.error('Error parsing Gemini message:', e);
                }
            };

            this.geminiWebSocket.onclose = () => {
                console.log('Gemini Live WebSocket disconnected');
                this.updateGeminiStatus('Disconnected', 'error');
            };

            this.geminiWebSocket.onerror = (error) => {
                console.error('Gemini WebSocket error:', error);
                this.updateGeminiStatus('Connection Error', 'error');
            };

        } catch (error) {
            console.error('Error initializing Gemini WebSocket:', error);
        }
    }

    handleGeminiMessage(data) {
        console.log('Gemini message:', data);
        
        if (data.serverContent && data.serverContent.modelTurn) {
            const parts = data.serverContent.modelTurn.parts;
            if (parts && parts.length > 0) {
                const text = parts[0].text;
                if (text) {
                    this.displayGeminiResponse(text);
                }
            }
        }
    }

    sendGeminiMessage(text) {
        if (this.geminiWebSocket && this.geminiWebSocket.readyState === WebSocket.OPEN) {
            const message = {
                clientContent: {
                    turns: [{
                        role: "user",
                        parts: [{ text: text }]
                    }]
                }
            };
            
            this.geminiWebSocket.send(JSON.stringify(message));
            this.displayUserMessage(text);
        } else {
            alert('Gemini Live is not connected. Please start a new session.');
        }
    }

    showGeminiLiveInterface() {
        const helpSection = document.querySelector('.help-section');
        if (helpSection) {
            const liveInterface = document.createElement('div');
            liveInterface.className = 'gemini-live-interface';
            liveInterface.innerHTML = `
                <div class="gemini-live-container">
                    <div class="gemini-header">
                        <h4><i class="fas fa-microphone"></i> Gemini Live Conversation</h4>
                        <span id="geminiStatus" class="status-indicator">Connecting...</span>
                    </div>
                    
                    <div class="conversation-display" id="conversationDisplay">
                        <div class="welcome-message">
                            <i class="fas fa-robot"></i>
                            <p>Hello! I'm your Gemini AI assistant. How can I help you today?</p>
                        </div>
                    </div>
                    
                    <div class="message-input-section">
                        <div class="input-group">
                            <input type="text" id="geminiMessageInput" placeholder="Type your message..." />
                            <button onclick="helpDesk.sendGeminiMessageFromInput()" class="btn-send">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                        <div class="live-controls">
                            <button onclick="helpDesk.startVoiceInput()" class="btn-voice" title="Voice Input">
                                <i class="fas fa-microphone"></i>
                            </button>
                            <button onclick="helpDesk.endGeminiLive()" class="btn-end">End Conversation</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing interfaces
            const existingInterface = helpSection.querySelector('.gemini-live-interface');
            if (existingInterface) {
                existingInterface.remove();
            }
            
            helpSection.appendChild(liveInterface);

            // Add enter key listener
            const input = document.getElementById('geminiMessageInput');
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendGeminiMessageFromInput();
                    }
                });
            }
        }
    }

    sendGeminiMessageFromInput() {
        const input = document.getElementById('geminiMessageInput');
        if (input && input.value.trim()) {
            this.sendGeminiMessage(input.value.trim());
            input.value = '';
        }
    }

    displayUserMessage(text) {
        const display = document.getElementById('conversationDisplay');
        if (display) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'user-message';
            messageDiv.innerHTML = `
                <div class="message-bubble user-bubble">
                    <i class="fas fa-user"></i>
                    <span>${text}</span>
                </div>
            `;
            display.appendChild(messageDiv);
            display.scrollTop = display.scrollHeight;
        }
    }

    displayGeminiResponse(text) {
        const display = document.getElementById('conversationDisplay');
        if (display) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'ai-message';
            messageDiv.innerHTML = `
                <div class="message-bubble ai-bubble">
                    <i class="fas fa-robot"></i>
                    <span>${text}</span>
                </div>
            `;
            display.appendChild(messageDiv);
            display.scrollTop = display.scrollHeight;
        }
    }

    updateGeminiStatus(status, type) {
        const statusElement = document.getElementById('geminiStatus');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `status-indicator status-${type}`;
        }
    }

    endGeminiLive() {
        if (this.geminiWebSocket) {
            this.geminiWebSocket.close();
            this.geminiWebSocket = null;
        }
        
        const liveInterface = document.querySelector('.gemini-live-interface');
        if (liveInterface) {
            liveInterface.remove();
        }
        
        // Track end of live session
        if (this.currentSession) {
            this.trackInteraction('gemini_live_end');
        }
    }

    startVoiceInput() {
        // Placeholder for voice input functionality
        alert('Voice input feature coming soon!');
    }

    async requestCallback(phoneNumber, preferredTime = null) {
        if (!this.currentSession) {
            alert('Please start a help session first');
            return;
        }

        try {
            const response = await fetch('/api/help/request-callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.currentSession.sessionId,
                    phoneNumber: phoneNumber,
                    preferredTime: preferredTime
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showCallbackConfirmation();
            } else {
                alert('Failed to request callback: ' + result.message);
            }
        } catch (error) {
            console.error('Error requesting callback:', error);
            alert('Error requesting callback');
        }
    }

    getCurrentUserData() {
        // Get user data from Firebase or local storage
        return {
            userId: window.currentUser?.userId || localStorage.getItem('userId') || '1',
            firebaseUid: window.currentUser?.firebaseUid || localStorage.getItem('firebaseUid')
        };
    }

    showJiraTicketInfo(jiraTicket) {
        const helpSection = document.querySelector('.help-section');
        if (helpSection) {
            const ticketInfo = document.createElement('div');
            ticketInfo.className = 'jira-ticket-info';
            ticketInfo.innerHTML = `
                <div class="ticket-badge">
                    <i class="fas fa-ticket-alt"></i>
                    <span>Ticket: ${jiraTicket.key}</span>
                    <a href="${jiraTicket.url}" target="_blank" class="ticket-link">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            `;
            helpSection.appendChild(ticketInfo);
        }
    }

    showToggleWarning(clickCount) {
        const helpSection = document.querySelector('.help-section');
        if (helpSection && clickCount > 3) {
            const warning = document.createElement('div');
            warning.className = 'toggle-warning';
            warning.innerHTML = `
                <div class="warning-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>We noticed you're clicking frequently. Do you need actual help?</span>
                    <button onclick="helpDesk.showGenuineHelpOptions()" class="btn-yes">Yes, I need help</button>
                    <button onclick="helpDesk.endHelpSession()" class="btn-no">No, just browsing</button>
                </div>
            `;
            
            // Remove existing warnings
            const existingWarning = helpSection.querySelector('.toggle-warning');
            if (existingWarning) {
                existingWarning.remove();
            }
            
            helpSection.appendChild(warning);
        }
    }

    showGenuineHelpOptions() {
        const helpSection = document.querySelector('.help-section');
        if (helpSection) {
            const options = document.createElement('div');
            options.className = 'help-options';
            options.innerHTML = `
                <div class="help-options-container">
                    <h4>How can we help you?</h4>
                    
                    <div class="ai-chat-section">
                        <label>Ask our AI assistant:</label>
                        <div class="ai-input-group">
                            <input type="text" id="aiQuery" placeholder="Type your question here..." />
                            <button onclick="helpDesk.handleAIQuery()" class="btn-ai">Ask AI</button>
                        </div>
                        <div id="aiResponse" class="ai-response"></div>
                    </div>
                    
                    <div class="callback-section">
                        <label>Request a callback:</label>
                        <div class="callback-input-group">
                            <input type="tel" id="callbackPhone" placeholder="Your phone number" />
                            <input type="datetime-local" id="preferredTime" />
                            <button onclick="helpDesk.handleCallbackRequest()" class="btn-callback">Request Callback</button>
                        </div>
                    </div>
                    
                    <div class="live-ai-section">
                        <button onclick="helpDesk.startGeminiLive()" class="btn-gemini-live">
                            <i class="fas fa-comments"></i> Start Live AI Conversation
                        </button>
                        <p class="gemini-note">Real-time conversation with Gemini AI using secure ephemeral tokens</p>
                    </div>
                    
                    <div class="quick-actions">
                        <button onclick="helpDesk.handleQuickAction('account')" class="quick-btn">Account Issues</button>
                        <button onclick="helpDesk.handleQuickAction('data')" class="quick-btn">Data Problems</button>
                        <button onclick="helpDesk.handleQuickAction('billing')" class="quick-btn">Billing Questions</button>
                        <button onclick="helpDesk.handleQuickAction('technical')" class="quick-btn">Technical Support</button>
                    </div>
                </div>
            `;
            
            // Remove existing options
            const existingOptions = helpSection.querySelector('.help-options');
            if (existingOptions) {
                existingOptions.remove();
            }
            
            helpSection.appendChild(options);
        }
    }

    async handleAIQuery() {
        const queryInput = document.getElementById('aiQuery');
        const responseDiv = document.getElementById('aiResponse');
        
        if (!queryInput || !queryInput.value.trim()) return;
        
        const query = queryInput.value.trim();
        responseDiv.innerHTML = '<div class="loading">Getting AI response...</div>';
        
        const response = await this.getAIAssistance(query);
        
        responseDiv.innerHTML = `
            <div class="ai-response-content">
                <strong>AI Assistant:</strong>
                <p>${response}</p>
                <div class="response-actions">
                    <button onclick="helpDesk.rateResponse(true)" class="btn-helpful">Helpful</button>
                    <button onclick="helpDesk.rateResponse(false)" class="btn-not-helpful">Not Helpful</button>
                </div>
            </div>
        `;
        
        queryInput.value = '';
    }

    handleCallbackRequest() {
        const phoneInput = document.getElementById('callbackPhone');
        const timeInput = document.getElementById('preferredTime');
        
        if (!phoneInput || !phoneInput.value.trim()) {
            alert('Please enter your phone number');
            return;
        }
        
        this.requestCallback(phoneInput.value.trim(), timeInput.value);
    }

    async handleQuickAction(category) {
        const queries = {
            'account': 'I need help with my account settings and profile',
            'data': 'I am having problems with my mobile data connection',
            'billing': 'I have questions about my bill and payments',
            'technical': 'I need technical support for my device or service'
        };
        
        const query = queries[category];
        if (query) {
            // Set the query in the input and trigger AI response
            const queryInput = document.getElementById('aiQuery');
            if (queryInput) {
                queryInput.value = query;
                await this.handleAIQuery();
            }
        }
    }

    rateResponse(isHelpful) {
        this.trackInteraction('ai_rating', { helpful: isHelpful });
        
        const ratingMessage = isHelpful ? 
            'Thank you for your feedback!' : 
            'Thanks for the feedback. Would you like to request a callback for more personalized help?';
            
        alert(ratingMessage);
    }

    showCallbackConfirmation() {
        alert('Callback requested successfully! We will contact you within 24 hours.');
    }

    showSessionSummary(sessionData) {
        const duration = Math.floor(sessionData.duration_seconds / 60);
        const message = `
Help session completed:
• Duration: ${duration} minutes
• Total interactions: ${sessionData.total_clicks}
• Support ticket created for follow-up

Thank you for using our help service!
        `;
        alert(message);
    }
}

// Initialize help desk client
const helpDesk = new HelpDeskClient();

// Global functions for help session management
async function startHelpSession() {
    return await helpDesk.startHelpSession();
}

async function endHelpSession() {
    return await helpDesk.endHelpSession();
}

async function trackHelpInteraction(type, data) {
    return await helpDesk.trackInteraction(type, data);
}

// Update the existing help toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Enhanced help section integration
    const helpToggle = document.getElementById('helpToggle');
    if (helpToggle) {
        helpToggle.addEventListener('click', function() {
            // Track the interaction
            setTimeout(() => {
                if (helpDesk.currentSession) {
                    helpDesk.trackInteraction('help_toggle');
                }
            }, 100);
        });
    }
});
