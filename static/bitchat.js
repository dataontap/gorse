
class BitchatClient {
    constructor() {
        this.isConnected = false;
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
            return false;
        }

        try {
            const available = await navigator.bluetooth.getAvailability();
            if (!available) {
                this.displaySystemMessage('Bluetooth not available on this device.');
                return false;
            }
            
            this.displaySystemMessage('Bluetooth support detected. Click to connect when ready.');
            return true;
        } catch (error) {
            this.displaySystemMessage('Error checking Bluetooth availability: ' + error.message);
            return false;
        }
    }

    async connectBluetooth() {
        try {
            this.updateBluetoothStatus('connecting');
            this.displaySystemMessage('Requesting Bluetooth device...');

            const device = await navigator.bluetooth.requestDevice({
                filters: [{ services: ['6ba1e2e9-2e00-4b5e-8b5a-7e8b5a7e8b5a'] }], // Bitchat service UUID
                optionalServices: ['battery_service']
            });

            this.displaySystemMessage(`Connecting to ${device.name}...`);
            
            const server = await device.gatt.connect();
            this.isConnected = true;
            this.updateBluetoothStatus('online');
            this.displaySystemMessage('Connected to Bitchat mesh network!');
            
            // Start peer discovery simulation
            this.startPeerDiscovery();
            
        } catch (error) {
            this.updateBluetoothStatus('offline');
            this.displaySystemMessage('Failed to connect: ' + error.message);
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

    simulateInitialState() {
        // Simulate some initial activity
        setTimeout(() => {
            if (!this.isConnected) {
                const statusElement = document.getElementById('bluetooth-status');
                statusElement.addEventListener('click', () => {
                    this.connectBluetooth();
                });
                statusElement.style.cursor = 'pointer';
                statusElement.title = 'Click to connect to Bitchat mesh network';
            }
        }, 1000);
    }
}

// Initialize Bitchat when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BitchatClient();
});
