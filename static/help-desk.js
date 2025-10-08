// Help Desk Client-Side Functions - ES5 Compatible
function HelpDeskClient() {
    this.currentSession = null;
    this.isAIEnabled = true;
    this.sessionStartTime = null;
    this.statusPollInterval = null;
    this.timerInterval = null;
    this.ticketPopupElement = null;
}

HelpDeskClient.prototype.startHelpSession = function() {
    var self = this;
    var userData = this.getCurrentUserData();
    
    // Get browser's local timestamp with timezone
    var now = new Date();
    var browserTimestamp = now.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZoneName: 'short'
    });

    return fetch('/api/help/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            userId: userData.userId,
            firebaseUid: userData.firebaseUid,
            pageUrl: window.location.href,
            browserTimestamp: browserTimestamp
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            self.currentSession = {
                sessionId: result.session_id,
                helpSessionId: result.help_session_id,
                jiraTicket: result.jira_ticket
            };

            // Set session start time from existing session or use current time
            if (result.existing && result.jira_ticket) {
                // For existing sessions, use the original ticket start time
                var existingStartTime = new Date(result.jira_ticket.started_at || result.started_at || Date.now());
                self.sessionStartTime = existingStartTime;
                console.log('Reopened existing help ticket:', result.jira_ticket.key, 'Started at:', existingStartTime);
            } else {
                self.sessionStartTime = new Date();
                console.log('Created new help session:', self.currentSession);
            }

            if (result.jira_ticket) {
                self.showJiraTicketInfo(result.jira_ticket, result.existing);
            }

            return self.currentSession;
        } else {
            console.error('Failed to start help session:', result.message);
            return null;
        }
    })
    .catch(function(error) {
        console.error('Error starting help session:', error);
        return null;
    });
};

HelpDeskClient.prototype.endHelpSession = function() {
    var self = this;
    if (!this.currentSession) return Promise.resolve();

    return fetch('/api/help/end', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: this.currentSession.sessionId
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            console.log('Help session ended:', result);
            self.showSessionSummary(result);
            self.currentSession = null;
            self.sessionStartTime = null;
        } else {
            console.error('Failed to end help session:', result.message);
        }
    })
    .catch(function(error) {
        console.error('Error ending help session:', error);
    });
};

HelpDeskClient.prototype.trackInteraction = function(type, data) {
    var self = this;
    if (!this.currentSession) return Promise.resolve();

    data = data || {};

    return fetch('/api/help/interact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: this.currentSession.sessionId,
            type: type,
            data: data
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            if (result.is_toggle) {
                self.showToggleWarning(result.click_count);
            } else if (result.click_count > 1) {
                self.showGenuineHelpOptions();
            }
        }
    })
    .catch(function(error) {
        console.error('Error tracking interaction:', error);
    });
};

HelpDeskClient.prototype.getAIAssistance = function(query) {
    var self = this;
    var userData = this.getCurrentUserData();

    return fetch('/api/help/ai-assist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            sessionId: this.currentSession && this.currentSession.sessionId,
            userId: userData.userId,
            firebaseUid: userData.firebaseUid,
            pageUrl: window.location.href
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            return result.response;
        } else {
            return result.response || 'Sorry, I could not process your request right now.';
        }
    })
    .catch(function(error) {
        console.error('Error getting AI assistance:', error);
        return 'Sorry, there was an error processing your request.';
    });
};

HelpDeskClient.prototype.startGeminiLive = function() {
    var self = this;

    if (!this.currentSession) {
        alert('Please start a help session first');
        return Promise.resolve();
    }

    var userData = this.getCurrentUserData();

    return fetch('/api/help/gemini-token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: this.currentSession.sessionId
        })
    })
    .then(function(tokenResponse) {
        return tokenResponse.json();
    })
    .then(function(tokenResult) {
        if (tokenResult.status !== 'success') {
            throw new Error(tokenResult.message || 'Failed to get ephemeral token');
        }

        return fetch('/api/help/gemini-live-start', {
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
    })
    .then(function(liveResponse) {
        return liveResponse.json();
    })
    .then(function(liveResult) {
        if (liveResult.status === 'success') {
            self.initializeGeminiWebSocket(liveResult.ws_url, liveResult.config);
            self.showGeminiLiveInterface();
        } else {
            throw new Error(liveResult.message || 'Failed to start live session');
        }
    })
    .catch(function(error) {
        console.error('Error starting Gemini Live:', error);
        alert('Failed to start live conversation: ' + error.message);
    });
};

HelpDeskClient.prototype.initializeGeminiWebSocket = function(wsUrl, config) {
    var self = this;

    try {
        this.geminiWebSocket = new WebSocket(wsUrl);

        this.geminiWebSocket.onopen = function() {
            console.log('Gemini Live WebSocket connected');
            self.geminiWebSocket.send(JSON.stringify(config));
            self.updateGeminiStatus('Connected', 'success');
        };

        this.geminiWebSocket.onmessage = function(event) {
            try {
                var data = JSON.parse(event.data);
                self.handleGeminiMessage(data);
            } catch (e) {
                console.error('Error parsing Gemini message:', e);
            }
        };

        this.geminiWebSocket.onclose = function() {
            console.log('Gemini Live WebSocket disconnected');
            self.updateGeminiStatus('Disconnected', 'error');
        };

        this.geminiWebSocket.onerror = function(error) {
            console.error('Gemini WebSocket error:', error);
            self.updateGeminiStatus('Connection Error', 'error');
        };

    } catch (error) {
        console.error('Error initializing Gemini WebSocket:', error);
    }
};

HelpDeskClient.prototype.handleGeminiMessage = function(data) {
    console.log('Gemini message:', data);
    var self = this;

    if (data.serverContent && data.serverContent.modelTurn) {
        var parts = data.serverContent.modelTurn.parts;
        if (parts && parts.length > 0) {
            var text = parts[0].text;
            if (text) {
                self.displayGeminiResponse(text);
            }
        }
    }
};

HelpDeskClient.prototype.sendGeminiMessage = function(text) {
    if (this.geminiWebSocket && this.geminiWebSocket.readyState === WebSocket.OPEN) {
        var message = {
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
};

HelpDeskClient.prototype.showGeminiLiveInterface = function() {
    var self = this;
    var helpSection = document.querySelector('.help-section');
    if (helpSection) {
        var liveInterface = document.createElement('div');
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

        var existingInterface = helpSection.querySelector('.gemini-live-interface');
        if (existingInterface) {
            existingInterface.remove();
        }

        helpSection.appendChild(liveInterface);

        var input = document.getElementById('geminiMessageInput');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    self.sendGeminiMessageFromInput();
                }
            });
        }
    }
};

HelpDeskClient.prototype.sendGeminiMessageFromInput = function() {
    var input = document.getElementById('geminiMessageInput');
    if (input && input.value.trim()) {
        this.sendGeminiMessage(input.value.trim());
        input.value = '';
    }
};

HelpDeskClient.prototype.displayUserMessage = function(text) {
    var display = document.getElementById('conversationDisplay');
    if (display) {
        var messageDiv = document.createElement('div');
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
};

HelpDeskClient.prototype.displayGeminiResponse = function(text) {
    var display = document.getElementById('conversationDisplay');
    if (display) {
        var messageDiv = document.createElement('div');
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
};

HelpDeskClient.prototype.updateGeminiStatus = function(status, type) {
    var statusElement = document.getElementById('geminiStatus');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `status-indicator status-${type}`;
    }
};

HelpDeskClient.prototype.endGeminiLive = function() {
    if (this.geminiWebSocket) {
        this.geminiWebSocket.close();
        this.geminiWebSocket = null;
    }

    var liveInterface = document.querySelector('.gemini-live-interface');
    if (liveInterface) {
        liveInterface.remove();
    }

    if (this.currentSession) {
        this.trackInteraction('gemini_live_end');
    }
};

HelpDeskClient.prototype.startVoiceInput = function() {
    alert('Voice input feature coming soon!');
};

HelpDeskClient.prototype.requestCallback = function(phoneNumber, preferredTime) {
    var self = this;
    if (!this.currentSession) {
        alert('Please start a help session first');
        return Promise.resolve();
    }

    return fetch('/api/help/request-callback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: this.currentSession.sessionId,
            phoneNumber: phoneNumber,
            preferredTime: preferredTime
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            self.showCallbackConfirmation();
        } else {
            alert('Failed to request callback: ' + result.message);
        }
    })
    .catch(function(error) {
        console.error('Error requesting callback:', error);
        alert('Error requesting callback');
    });
};

HelpDeskClient.prototype.getCurrentUserData = function() {
    // Get Firebase UID from localStorage
    var firebaseUid = null;
    try {
        var currentUserData = JSON.parse(localStorage.getItem('currentUser') || 'null');
        if (currentUserData && currentUserData.uid) {
            firebaseUid = currentUserData.uid;
        }
    } catch (e) {
        console.error('Error getting current user data:', e);
    }

    return {
        userId: window.currentUser && window.currentUser.userId || '1',
        firebaseUid: firebaseUid
    };
};

HelpDeskClient.prototype.showJiraTicketInfo = function(jiraTicket, isExisting) {
    var self = this;
    
    // Use the actual JIRA status from the ticket object
    var status = jiraTicket.status || jiraTicket.jira_ticket_status || 'Need Help';
    
    // Format the original submission time
    var submissionTime = 'Unknown';
    if (jiraTicket.started_at) {
        var startDate = new Date(jiraTicket.started_at);
        submissionTime = startDate.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }

    var ticketPopup = document.createElement('div');
    ticketPopup.className = 'ticket-popup-overlay';
    ticketPopup.id = 'ticketPopup';

    ticketPopup.innerHTML = `
        <div class="ticket-popup-content">
            <div class="ticket-popup-header">
                <div class="ticket-header-info">
                    <i class="fas fa-ticket-alt"></i>
                    <h3>Support Ticket${isExisting ? ' (Existing)' : ''}</h3>
                </div>
                <button class="ticket-close-btn" onclick="helpDesk.closeTicketPopup()">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="ticket-popup-body">
                <div class="ticket-main-info">
                    <div class="ticket-number">
                        <label>Ticket:</label>
                        <span class="ticket-key">${jiraTicket.key}</span>
                    </div>

                    <div class="ticket-status-container">
                        <label>Status:</label>
                        <span class="status-badge status-${self.getStatusClass(status)}" id="ticketStatusBadge">
                            ${status}
                        </span>
                    </div>

                    <div class="ticket-submission-time">
                        <label>Submitted:</label>
                        <span class="submission-time">${submissionTime}</span>
                    </div>

                    <div class="ticket-timer">
                        <label>Elapsed Time:</label>
                        <span class="timer-display" id="ticketTimer">00:00</span>
                    </div>

                    <div class="ticket-actions">
                        <a href="${jiraTicket.url}" target="_blank" class="btn-view-jira">
                            <i class="fas fa-external-link-alt"></i> View in JIRA
                        </a>
                        <button class="btn-close-ticket" onclick="helpDesk.closeTicket()">
                            <i class="fas fa-times-circle"></i> Close Ticket
                        </button>
                    </div>
                </div>

                <div class="context-submission-form">
                    <h4>Provide Additional Context</h4>

                    <div class="form-group">
                        <label for="contextCategory">Category:</label>
                        <select id="contextCategory" class="form-control">
                            <option value="">Select a category...</option>
                            <option value="Technical Issue">Technical Issue</option>
                            <option value="Billing Question">Billing Question</option>
                            <option value="Account Problem">Account Problem</option>
                            <option value="Feature Request">Feature Request</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="contextDescription">Description:</label>
                        <textarea id="contextDescription" class="form-control" rows="4" 
                                  placeholder="Please describe your issue in detail..."></textarea>
                    </div>

                    <button class="btn-submit-context" onclick="helpDesk.submitTicketContext()">
                        <i class="fas fa-paper-plane"></i> Submit Context
                    </button>

                    <div id="contextMessage" class="context-message"></div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(ticketPopup);
    this.ticketPopupElement = ticketPopup;

    setTimeout(function() {
        ticketPopup.classList.add('show');
    }, 10);

    this.startTicketTimer();
    this.startStatusPolling();
};

HelpDeskClient.prototype.showToggleWarning = function(clickCount) {
    var self = this;
    var helpSection = document.querySelector('.help-section');
    if (helpSection && clickCount > 3) {
        var warning = document.createElement('div');
        warning.className = 'toggle-warning';
        warning.innerHTML = `
            <div class="warning-message">
                <i class="fas fa-exclamation-triangle"></i>
                <span>We noticed you're clicking frequently. Do you need actual help?</span>
                <button onclick="helpDesk.showGenuineHelpOptions()" class="btn-yes">Yes, I need help</button>
                <button onclick="helpDesk.endHelpSession()" class="btn-no">No, just browsing</button>
            </div>
        `;

        var existingWarning = helpSection.querySelector('.toggle-warning');
        if (existingWarning) {
            existingWarning.remove();
        }

        helpSection.appendChild(warning);
    }
};

HelpDeskClient.prototype.showGenuineHelpOptions = function() {
    var self = this;
    var helpSection = document.querySelector('.help-section');
    if (helpSection) {
        var options = document.createElement('div');
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

        var existingOptions = helpSection.querySelector('.help-options');
        if (existingOptions) {
            existingOptions.remove();
        }

        helpSection.appendChild(options);
    }
};

HelpDeskClient.prototype.handleAIQuery = function() {
    var self = this;
    var queryInput = document.getElementById('aiQuery');
    var responseDiv = document.getElementById('aiResponse');

    if (!queryInput || !queryInput.value.trim()) return;

    var query = queryInput.value.trim();
    responseDiv.innerHTML = '<div class="loading">Getting AI response...</div>';

    this.getAIAssistance(query)
    .then(function(response) {
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
    })
    .catch(function(error) {
        console.error('Error in handleAIQuery:', error);
        responseDiv.innerHTML = '<div class="error">Error getting AI response.</div>';
    });
};

HelpDeskClient.prototype.handleCallbackRequest = function() {
    var phoneInput = document.getElementById('callbackPhone');
    var timeInput = document.getElementById('preferredTime');

    if (!phoneInput || !phoneInput.value.trim()) {
        alert('Please enter your phone number');
        return;
    }

    this.requestCallback(phoneInput.value.trim(), timeInput.value);
};

HelpDeskClient.prototype.handleQuickAction = function(category) {
    var self = this;
    var queries = {
        'account': 'I need help with my account settings and profile',
        'data': 'I am having problems with my mobile data connection',
        'billing': 'I have questions about my bill and payments',
        'technical': 'I need technical support for my device or service'
    };

    var query = queries[category];
    if (query) {
        var queryInput = document.getElementById('aiQuery');
        if (queryInput) {
            queryInput.value = query;
            this.handleAIQuery();
        }
    }
};

HelpDeskClient.prototype.rateResponse = function(isHelpful) {
    this.trackInteraction('ai_rating', { helpful: isHelpful });

    var ratingMessage = isHelpful ?
        'Thank you for your feedback!' :
        'Thanks for the feedback. Would you like to request a callback for more personalized help?';

    alert(ratingMessage);
};

HelpDeskClient.prototype.showCallbackConfirmation = function() {
    alert('Callback requested successfully! We will contact you within 24 hours.');
};

HelpDeskClient.prototype.showSessionSummary = function(sessionData) {
    var duration = Math.floor(sessionData.duration_seconds / 60);
    var message = `
Help session completed:
• Duration: ${duration} minutes
• Total interactions: ${sessionData.total_clicks}
• Support ticket created for follow-up

Thank you for using our help service!
    `;
    alert(message);
};

HelpDeskClient.prototype.getStatusClass = function(status) {
    var statusMap = {
        'TO DO': 'to-do',
        'To Do': 'to-do',
        'IN PROGRESS': 'in-progress',
        'In Progress': 'in-progress',
        'PENDING': 'pending',
        'Pending': 'pending',
        'DONE': 'done',
        'Done': 'done',
        'Need Help': 'to-do',
        'User_Closed': 'done',
        'Resolved': 'done',
        'Escalated': 'escalated',
        'Escalated_L1': 'escalated',
        'Escalated_L2': 'escalated',
        'Escalated_L3': 'escalated'
    };
    return statusMap[status] || 'to-do';
};

HelpDeskClient.prototype.startTicketTimer = function() {
    var self = this;
    if (this.timerInterval) {
        clearInterval(this.timerInterval);
    }

    this.timerInterval = setInterval(function() {
        if (!self.sessionStartTime) return;

        var now = new Date();
        var elapsed = Math.floor((now - self.sessionStartTime) / 1000);

        var hours = Math.floor(elapsed / 3600);
        var minutes = Math.floor((elapsed % 3600) / 60);
        var seconds = elapsed % 60;

        var timerDisplay = document.getElementById('ticketTimer');
        if (timerDisplay) {
            if (hours > 0) {
                timerDisplay.textContent = 
                    String(hours).padStart(2, '0') + ':' + 
                    String(minutes).padStart(2, '0') + ':' + 
                    String(seconds).padStart(2, '0');
            } else {
                timerDisplay.textContent = 
                    String(minutes).padStart(2, '0') + ':' + 
                    String(seconds).padStart(2, '0');
            }
        }
    }, 1000);
};

HelpDeskClient.prototype.startStatusPolling = function() {
    var self = this;
    if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval);
    }

    this.statusPollInterval = setInterval(function() {
        self.checkTicketStatus();
    }, 30000);
};

HelpDeskClient.prototype.checkTicketStatus = function() {
    var self = this;
    var userData = JSON.parse(localStorage.getItem('currentUser') || '{}');
    var firebaseUid = userData.uid;

    if (!firebaseUid) return;

    fetch('/api/help/user-open-ticket?firebaseUid=' + firebaseUid)
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success' && result.has_open_ticket) {
            // Update current session with open ticket data
            self.currentSession = {
                sessionId: result.ticket.session_id,
                helpSessionId: result.ticket.help_session_id,
                jiraTicket: result.ticket.jira_ticket
            };

            if (result.ticket.jira_ticket_status) {
                self.updateStatusBadge(result.ticket.jira_ticket_status);

                // Stop polling for completed statuses
                if (result.ticket.jira_ticket_status === 'DONE' ||
                    result.ticket.jira_ticket_status === 'Done' ||
                    result.ticket.jira_ticket_status === 'Resolved' || 
                    result.ticket.jira_ticket_status === 'User_Closed') {
                    self.stopPolling();
                }
            }
        } else if (result.status === 'success' && !result.has_open_ticket) {
            // No open ticket, stop polling
            self.stopPolling();
            self.currentSession = null;
        }
    })
    .catch(function(error) {
        console.error('Error checking ticket status:', error);
    });
};

HelpDeskClient.prototype.updateStatusBadge = function(newStatus) {
    var statusBadge = document.getElementById('ticketStatusBadge');
    if (statusBadge && statusBadge.textContent !== newStatus) {
        statusBadge.textContent = newStatus;
        statusBadge.className = 'status-badge status-' + this.getStatusClass(newStatus);
    }
};

HelpDeskClient.prototype.stopPolling = function() {
    if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval);
        this.statusPollInterval = null;
    }

    if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
    }
};

HelpDeskClient.prototype.submitTicketContext = function() {
    var self = this;
    var category = document.getElementById('contextCategory');
    var description = document.getElementById('contextDescription');
    var messageDiv = document.getElementById('contextMessage');

    if (!category || !category.value) {
        messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Please select a category</div>';
        return;
    }

    if (!description || !description.value.trim()) {
        messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Please provide a description</div>';
        return;
    }

    if (!this.currentSession) {
        messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> No active session</div>';
        return;
    }

    messageDiv.innerHTML = '<div class="loading-message"><i class="fas fa-spinner fa-spin"></i> Submitting...</div>';

    fetch('/api/help/update-context', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: this.currentSession.sessionId,
            category: category.value,
            description: description.value.trim()
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.status === 'success') {
            messageDiv.innerHTML = '<div class="success-message"><i class="fas fa-check-circle"></i> Context submitted successfully!</div>';
            category.value = '';
            description.value = '';

            setTimeout(function() {
                messageDiv.innerHTML = '';
            }, 3000);
        } else {
            messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> ' + (result.message || 'Failed to submit context') + '</div>';
        }
    })
    .catch(function(error) {
        console.error('Error submitting context:', error);
        messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Error submitting context</div>';
    });
};

HelpDeskClient.prototype.closeTicketPopup = function() {
    // Just hide the popup without closing the ticket
    this.removeTicketPopup();
};

HelpDeskClient.prototype.closeTicket = function() {
    var self = this;

    if (!this.currentSession) {
        this.removeTicketPopup();
        return;
    }

    var confirmed = confirm('This will mark your support ticket as "User_Closed". Are you sure?');

    if (confirmed) {
        fetch('/api/help/update-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: this.currentSession.sessionId,
                status: 'User_Closed'
            })
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(result) {
            if (result.status === 'success') {
                console.log('Ticket marked as User_Closed');
            }
            self.stopPolling();
            self.removeTicketPopup();
            self.currentSession = null;
        })
        .catch(function(error) {
            console.error('Error updating ticket status:', error);
            self.stopPolling();
            self.removeTicketPopup();
            self.currentSession = null;
        });
    }
};

HelpDeskClient.prototype.removeTicketPopup = function() {
    if (this.ticketPopupElement) {
        this.ticketPopupElement.classList.remove('show');
        var element = this.ticketPopupElement;
        setTimeout(function() {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 300);
        this.ticketPopupElement = null;
    }

    this.stopPolling();
};

// Initialize help desk client
var helpDesk = new HelpDeskClient();

// Global functions for help session management
function startHelpSession() {
    return helpDesk.startHelpSession();
}

function endHelpSession() {
    return helpDesk.endHelpSession();
}

function trackHelpInteraction(type, data) {
    return helpDesk.trackInteraction(type, data);
}

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    var helpToggle = document.getElementById('helpToggle');
    if (helpToggle) {
        helpToggle.addEventListener('click', function() {
            setTimeout(function() {
                if (helpDesk.currentSession) {
                    helpDesk.trackInteraction('help_toggle');
                }
            }, 100);
        });
    }
});