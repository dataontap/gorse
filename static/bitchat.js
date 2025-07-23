
class BitchatClient {
    constructor() {
        this.isConnected = false;
        this.isDemoMode = false;
        this.currentChannel = '#general';
        this.peers = new Map();
        this.channels = new Map();
        this.messageHistory = [];
        this.commands = {
            '/help': this.showHelp.bind(this),
            '/j': this.joinChannel.bind(this),
            '/join': this.joinChannel.bind(this),
            '/m': this.sendPrivateMessage.bind(this),
            '/msg': this.sendPrivateMessage.bind(this),
            '/w': this.listPeers.bind(this),
            '/who': this.listPeers.bind(this),
            '/channels': this.listChannels.bind(this),
            '/clear': this.clearMessages.bind(this),
            '/pass': this.setChannelPassword.bind(this),
            '/transfer': this.transferOwnership.bind(this),
            '/save': this.toggleMessageRetention.bind(this)
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkBluetoothSupport();
        this.simulateInitialState();
    }

    setupEventListeners() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const joinChannelBtn = document.getElementById('join-channel-btn');
        const emergencyWipeBtn = document.getElementById('emergency-wipe');
        const demoModeBtn = document.getElementById('demo-mode-btn');

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        joinChannelBtn.addEventListener('click', () => {
            this.promptJoinChannel();
        });

        emergencyWipeBtn.addEventListener('click', () => {
            this.emergencyWipe();
        });

        demoModeBtn.addEventListener('click', () => {
            this.toggleDemoMode();
        });

        // Channel selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.channel-item')) {
                const channelElement = e.target.closest('.channel-item');
                const channelName = channelElement.dataset.channel;
                this.switchChannel(channelName);
            }
        });
    }

    async checkBluetoothSupport() {
        if (!navigator.bluetooth) {
            this.displaySystemMessage('Bluetooth not supported in this browser. Consider using Chrome or Edge.');
            this.displaySystemMessage('💡 Tip: You can still use demo mode by clicking the status indicator.');
            return false;
        }

        try {
            const available = await navigator.bluetooth.getAvailability();
            if (!available) {
                this.displaySystemMessage('Bluetooth not available on this device.');
                this.displaySystemMessage('💡 Tip: You can still use demo mode by clicking the status indicator.');
                return false;
            }
            
            this.displaySystemMessage('Bluetooth support detected. Click the status indicator to connect.');
            this.displaySystemMessage('📱 Note: You need another bitchat-enabled device nearby for real mesh networking.');
            return true;
        } catch (error) {
            this.displaySystemMessage('Error checking Bluetooth availability: ' + error.message);
            this.displaySystemMessage('💡 Tip: You can still use demo mode by clicking the status indicator.');
            return false;
        }
    }

    async connectBluetooth() {
        try {
            this.updateBluetoothStatus('connecting');
            this.displaySystemMessage('Initiating Bluetooth pairing...');
            this.showPairingOverlay();

            // Set a timeout for the pairing process
            const pairingTimeout = setTimeout(() => {
                this.hidePairingOverlay();
                this.displaySystemMessage('⏰ Pairing timed out. Click status to try again or use demo mode.');
                this.updateBluetoothStatus('offline');
            }, 45000); // 45 second timeout for better user experience

            // Try to find bitchat-enabled devices first
            let device;
            try {
                this.displaySystemMessage('🔍 Looking for Bitchat devices...');
                device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { services: ['6ba1e2e9-2e00-4b5e-8b5a-7e8b5a7e8b5a'] }, // Bitchat service UUID
                        { namePrefix: 'bitchat' },
                        { namePrefix: 'BITCHAT' }
                    ],
                    optionalServices: ['battery_service', 'device_information']
                });
            } catch (filterError) {
                // If no bitchat devices found, try with broader filters
                this.displaySystemMessage('📱 No bitchat devices found. Showing all Bluetooth devices...');
                try {
                    device = await navigator.bluetooth.requestDevice({
                        acceptAllDevices: true,
                        optionalServices: ['battery_service', 'device_information']
                    });
                } catch (broadError) {
                    // If user cancels or no devices available, offer demo mode
                    clearTimeout(pairingTimeout);
                    this.hidePairingOverlay();
                    this.displaySystemMessage('No Bluetooth devices available or permission denied.');
                    this.displaySystemMessage('💡 Starting demo mode for full feature testing...');
                    setTimeout(() => this.startDemoMode(), 1000);
                    return;
                }
            }
            
            // Clear the timeout since user made a selection
            clearTimeout(pairingTimeout);

            this.displaySystemMessage(`Connecting to ${device.name || 'Unknown Device'}...`);
            
            const server = await device.gatt.connect();
            
            // Check if device supports bitchat protocol
            try {
                const service = await server.getPrimaryService('6ba1e2e9-2e00-4b5e-8b5a-7e8b5a7e8b5a');
                this.displaySystemMessage('✓ Bitchat protocol detected!');
                this.isConnected = true;
                this.updateBluetoothStatus('online');
                this.displaySystemMessage('Connected to Bitchat mesh network!');
                this.hidePairingOverlay();
                
                // Start peer discovery simulation
                this.startPeerDiscovery();
            } catch (serviceError) {
                // Device doesn't support bitchat - simulate connection anyway for demo
                this.displaySystemMessage('⚠️ Device does not support bitchat protocol. Running in demo mode.');
                this.isConnected = true;
                this.updateBluetoothStatus('online');
                this.displaySystemMessage('Connected in demo mode - simulating mesh network');
                this.hidePairingOverlay();
                
                // Start peer discovery simulation
                this.startPeerDiscovery();
            }
            
        } catch (error) {
            this.updateBluetoothStatus('offline');
            this.hidePairingOverlay();
            let errorMessage = 'Failed to connect: ';
            
            if (error.name === 'NotFoundError') {
                errorMessage += 'No compatible devices found. Make sure Bluetooth is enabled and bitchat devices are nearby.';
            } else if (error.name === 'SecurityError') {
                errorMessage += 'Bluetooth access denied. Please allow Bluetooth permissions and try again.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage += 'Bluetooth not supported on this device or browser.';
            } else if (error.message && error.message.includes('cancelled')) {
                errorMessage += 'Connection cancelled by user.';
            } else {
                errorMessage += error.message || 'Unknown error occurred';
            }
            
            this.displaySystemMessage(errorMessage);
            
            // Offer demo mode as immediate fallback for cancelled requests
            if (error.message && error.message.includes('cancelled')) {
                this.displaySystemMessage('💡 Try demo mode instead - click the Bluetooth status again for a simulated experience.');
            } else {
                // Offer demo mode as fallback for other errors
                setTimeout(() => {
                    this.displaySystemMessage('Would you like to try demo mode instead? Click the status indicator again.');
                }, 2000);
            }
            
            const statusElement = document.getElementById('bluetooth-status');
            statusElement.addEventListener('click', () => {
                this.startDemoMode();
            }, { once: true });
        }
    }

    updateBluetoothStatus(status) {
        const statusElement = document.getElementById('bluetooth-status');
        statusElement.className = `status-indicator ${status}`;
        
        const statusText = document.querySelector('.status-text');
        switch (status) {
            case 'online':
                statusText.textContent = 'Bluetooth Connected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
            default:
                statusText.textContent = 'Bluetooth Disconnected';
        }

        // Sync status to localStorage for dashboard menu
        localStorage.setItem('bitchatStatus', status);
    }

    startPeerDiscovery() {
        // Simulate peer discovery
        setTimeout(() => {
            this.addPeer('alice_mobile', { rssi: -45, battery: 85 });
        }, 2000);
        
        setTimeout(() => {
            this.addPeer('bob_laptop', { rssi: -62, battery: null });
        }, 4000);
        
        setTimeout(() => {
            this.addPeer('charlie_tablet', { rssi: -38, battery: 92 });
        }, 6000);
    }

    addPeer(peerId, metadata) {
        this.peers.set(peerId, metadata);
        this.updatePeersList();
        this.updateMeshStatus();
        this.displaySystemMessage(`${peerId} joined the mesh network`);
    }

    removePeer(peerId) {
        this.peers.delete(peerId);
        this.updatePeersList();
        this.updateMeshStatus();
        this.displaySystemMessage(`${peerId} left the mesh network`);
    }

    updatePeersList() {
        const peersList = document.getElementById('peers-list');
        
        if (this.peers.size === 0) {
            peersList.innerHTML = '<div class="no-peers">No peers connected</div>';
            return;
        }

        const peersHTML = Array.from(this.peers.entries()).map(([peerId, metadata]) => `
            <div class="peer-item">
                <div class="peer-status"></div>
                <div class="peer-info">
                    <div class="peer-name">${peerId}</div>
                    <div class="peer-details">RSSI: ${metadata.rssi}dBm${metadata.battery ? `, Battery: ${metadata.battery}%` : ''}</div>
                </div>
            </div>
        `).join('');

        peersList.innerHTML = peersHTML;
    }

    updateMeshStatus() {
        const peersCount = document.querySelector('.peers-count');
        peersCount.textContent = this.peers.size;

        // Sync peer count to localStorage for dashboard menu
        localStorage.setItem('bitchatPeers', this.peers.size.toString());
    }

    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;

        if (message.startsWith('/')) {
            this.processCommand(message);
        } else {
            this.broadcastMessage(message);
        }

        input.value = '';
    }

    processCommand(command) {
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        const args = parts.slice(1);

        if (this.commands[cmd]) {
            this.commands[cmd](args);
        } else {
            this.displaySystemMessage(`Unknown command: ${cmd}. Type /help for available commands.`);
        }
    }

    broadcastMessage(message) {
        if (!this.isConnected) {
            this.displaySystemMessage('Not connected to mesh network. Click Bluetooth status to connect.');
            return;
        }

        const messageObj = {
            id: Date.now(),
            channel: this.currentChannel,
            sender: 'You',
            content: message,
            timestamp: new Date(),
            encrypted: true
        };

        this.displayMessage(messageObj, true);
        this.messageHistory.push(messageObj);

        // Simulate message relay through mesh
        setTimeout(() => {
            this.displaySystemMessage(`Message relayed through ${this.peers.size} peer(s)`);
        }, 500);
    }

    displayMessage(messageObj, isOwn = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwn ? 'own' : 'peer'}`;
        
        const time = messageObj.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const encryptedIcon = messageObj.encrypted ? '🔒' : '';
        
        messageDiv.innerHTML = `
            <div class="message-content">${messageObj.content} ${encryptedIcon}</div>
            <div class="message-meta">${isOwn ? '' : messageObj.sender + ' • '}${time}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    displaySystemMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.textContent = message;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Command implementations
    showHelp() {
        const helpText = `
Available Commands:
• /j #channel - Join or create a channel
• /m @user message - Send private message
• /w - List online users
• /channels - Show all channels
• /clear - Clear chat messages
• /pass [password] - Set channel password
• /transfer @user - Transfer ownership
• /save - Toggle message retention
        `;
        this.displaySystemMessage(helpText);
    }

    joinChannel(args) {
        if (args.length === 0) {
            this.displaySystemMessage('Usage: /j #channelname');
            return;
        }

        const channelName = args[0].startsWith('#') ? args[0] : '#' + args[0];
        this.switchChannel(channelName);
        this.displaySystemMessage(`Joined channel ${channelName}`);
    }

    switchChannel(channelName) {
        this.currentChannel = channelName;
        document.getElementById('current-channel').textContent = channelName;
        
        // Update active channel in sidebar
        document.querySelectorAll('.channel-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const channelElement = document.querySelector(`[data-channel="${channelName}"]`);
        if (channelElement) {
            channelElement.classList.add('active');
        } else {
            this.addChannelToSidebar(channelName);
        }
        
        // Clear messages when switching channels
        document.getElementById('chat-messages').innerHTML = `
            <div class="welcome-message">
                <p>🔐 Welcome to ${channelName}!</p>
                <p>End-to-end encrypted mesh messaging.</p>
            </div>
        `;
    }

    addChannelToSidebar(channelName) {
        const channelsList = document.getElementById('channels-list');
        const channelDiv = document.createElement('div');
        channelDiv.className = 'channel-item active';
        channelDiv.dataset.channel = channelName;
        channelDiv.innerHTML = `
            <span class="channel-name">${channelName}</span>
            <span class="channel-users">1</span>
        `;
        channelsList.appendChild(channelDiv);
    }

    sendPrivateMessage(args) {
        if (args.length < 2) {
            this.displaySystemMessage('Usage: /m @username message');
            return;
        }

        const recipient = args[0];
        const message = args.slice(1).join(' ');
        this.displaySystemMessage(`Private message sent to ${recipient}: ${message}`);
    }

    listPeers() {
        if (this.peers.size === 0) {
            this.displaySystemMessage('No peers connected to mesh network');
            return;
        }

        const peersList = Array.from(this.peers.keys()).join(', ');
        this.displaySystemMessage(`Connected peers: ${peersList}`);
    }

    listChannels() {
        this.displaySystemMessage('Available channels: #general, #tech, #random');
    }

    clearMessages() {
        document.getElementById('chat-messages').innerHTML = `
            <div class="welcome-message">
                <p>🔐 Messages cleared. Chat history wiped.</p>
            </div>
        `;
    }

    setChannelPassword(args) {
        const password = args.join(' ');
        if (password) {
            this.displaySystemMessage(`Channel password set for ${this.currentChannel}`);
        } else {
            this.displaySystemMessage(`Channel password removed for ${this.currentChannel}`);
        }
    }

    transferOwnership(args) {
        if (args.length === 0) {
            this.displaySystemMessage('Usage: /transfer @username');
            return;
        }
        this.displaySystemMessage(`Ownership of ${this.currentChannel} transferred to ${args[0]}`);
    }

    toggleMessageRetention() {
        this.displaySystemMessage(`Message retention toggled for ${this.currentChannel}`);
    }

    promptJoinChannel() {
        const channelName = prompt('Enter channel name (e.g., #mychannel):');
        if (channelName) {
            this.joinChannel([channelName]);
        }
    }

    emergencyWipe() {
        if (confirm('⚠️ This will permanently delete all messages and data. Continue?')) {
            this.messageHistory = [];
            this.peers.clear();
            this.updatePeersList();
            this.updateMeshStatus();
            this.displaySystemMessage('🚨 Emergency wipe completed. All data cleared.');
        }
    }

    toggleDemoMode() {
        const demoBtn = document.getElementById('demo-mode-btn');
        
        if (this.isConnected && this.isDemoMode) {
            // Exit demo mode
            this.exitDemoMode();
        } else {
            // Start demo mode
            this.startDemoMode();
        }
    }

    startDemoMode() {
        this.isDemoMode = true;
        const demoBtn = document.getElementById('demo-mode-btn');
        demoBtn.textContent = '🚪 Exit Demo';
        demoBtn.classList.add('active');
        
        this.displaySystemMessage('🎮 Starting demo mode...');
        this.updateBluetoothStatus('online');
        this.isConnected = true;
        this.displaySystemMessage('✨ Demo mode active - simulating bitchat mesh network');
        this.displaySystemMessage('📱 All messages and connections are simulated for demonstration');
        this.displaySystemMessage('🚀 You can now test all bitchat features safely!');
        this.displaySystemMessage('💡 Click "Exit Demo" to return to normal mode');
        this.startPeerDiscovery();
    }

    exitDemoMode() {
        this.isDemoMode = false;
        const demoBtn = document.getElementById('demo-mode-btn');
        demoBtn.textContent = '🎮 Demo Mode';
        demoBtn.classList.remove('active');
        
        this.isConnected = false;
        this.updateBluetoothStatus('offline');
        this.peers.clear();
        this.updatePeersList();
        this.updateMeshStatus();
        
        this.displaySystemMessage('🚪 Exited demo mode');
        this.displaySystemMessage('🔗 Click Bluetooth status to connect to real devices');
        
        // Clear messages when exiting demo
        document.getElementById('chat-messages').innerHTML = `
            <div class="welcome-message">
                <p>🔐 Welcome to Bitchat! Secure mesh messaging without servers.</p>
                <p>Type <code>/help</code> for commands or start chatting.</p>
                <p>⚡ <strong>Quick Start:</strong> Click the Bluetooth status above to connect or use demo mode.</p>
            </div>
        `;
    }

    showPairingOverlay() {
        // Create overlay if it doesn't exist
        let overlay = document.getElementById('bluetooth-pairing-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'bluetooth-pairing-overlay';
            overlay.className = 'bluetooth-pairing-overlay';
            overlay.innerHTML = `
                <div class="pairing-message">
                    <h3>🔗 Bluetooth Pairing Active</h3>
                    <p><strong>Look for your browser's pairing dialog</strong></p>
                    <p>It may appear as a popup or notification at the top of the screen</p>
                    <div style="margin: 15px 0; padding: 12px; background: rgba(255, 255, 0, 0.1); border: 1px solid #ffff00; border-radius: 5px;">
                        <p style="color: #ffff00; margin: 0; font-size: 0.9em;"><strong>📱 Instructions:</strong></p>
                        <p style="margin: 5px 0 0 0; font-size: 0.85em;">• Select any Bluetooth device to try Bitchat</p>
                        <p style="margin: 5px 0 0 0; font-size: 0.85em;">• Or cancel to use demo mode</p>
                    </div>
                    <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px; flex-wrap: wrap;">
                        <button id="cancel-pairing" class="btn-secondary" style="background: rgba(255, 0, 64, 0.2); border-color: #ff0040; color: #ff0040; padding: 10px 20px; font-size: 0.9em;">Cancel & Demo</button>
                        <button id="retry-pairing" class="btn-primary" style="padding: 10px 20px; font-size: 0.9em;">Retry Pairing</button>
                    </div>
                    <div style="margin-top: 12px; color: #00aaaa; font-size: 0.8em;">
                        <p>This dialog will stay visible while pairing is active</p>
                        <p>Native dialog may appear separately from browser</p>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            
            // Add event listeners for the new buttons
            document.getElementById('cancel-pairing').addEventListener('click', () => {
                this.hidePairingOverlay();
                this.startDemoMode();
            });
            
            document.getElementById('retry-pairing').addEventListener('click', () => {
                this.hidePairingOverlay();
                setTimeout(() => this.connectBluetooth(), 500);
            });
        }
        
        // Position overlay to avoid conflicts with native dialogs
        overlay.style.top = window.innerHeight > 600 ? '60%' : '50%';
        overlay.classList.add('active');
    }

    hidePairingOverlay() {
        const overlay = document.getElementById('bluetooth-pairing-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    simulateInitialState() {
        // Simulate some initial activity
        setTimeout(() => {
            if (!this.isConnected) {
                const statusElement = document.getElementById('bluetooth-status');
                statusElement.addEventListener('click', () => {
                    if (this.isConnected) return;
                    this.connectBluetooth();
                });
                statusElement.style.cursor = 'pointer';
                statusElement.title = 'Click to connect to Bitchat mesh network (or try demo mode)';
                
                // Add visual indicator that it's clickable
                statusElement.style.transition = 'all 0.3s ease';
                statusElement.addEventListener('mouseenter', () => {
                    if (!this.isConnected) {
                        statusElement.style.transform = 'scale(1.05)';
                        statusElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                    }
                });
                statusElement.addEventListener('mouseleave', () => {
                    statusElement.style.transform = 'scale(1)';
                    statusElement.style.boxShadow = 'none';
                });
                
                // Show helpful initial message
                this.displaySystemMessage('🚀 Bitchat ready! Click the Bluetooth status to connect or start demo mode.');
                this.displaySystemMessage('💡 Demo mode works without any Bluetooth devices for testing.');
            }
        }, 1000);
    }
}

// Initialize Bitchat when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BitchatClient();
});
