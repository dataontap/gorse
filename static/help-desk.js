
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
