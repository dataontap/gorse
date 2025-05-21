document.addEventListener('DOMContentLoaded', function() {
    const connectMetamaskBtn = document.getElementById('connectMetamask');
    const connectWalletConnectBtn = document.getElementById('connectWalletConnect');
    const createTestWalletBtn = document.getElementById('createTestWallet');
    const disconnectWalletBtn = document.getElementById('disconnectWallet');
    const walletStatus = document.getElementById('walletStatus');
    const connectedAddress = document.getElementById('connectedAddress');
    const contractAddress = document.getElementById('contractAddress');
    const claimFoundingToken = document.getElementById('claimFoundingToken');
    const foundingClaimStatus = document.getElementById('foundingClaimStatus');
    const balanceAmount = document.querySelector('.balance-amount');
    const valueAmount = document.querySelector('.value-amount');
    const tokenTransactionsList = document.getElementById('tokenTransactionsList');

    // Get the token value pill in the header if it exists
    const tokenValuePill = document.querySelector('.token-value-pill');

    // Initialize price update timer
    let priceUpdateTimer = null;
    let currentTokenPrice = 1.0; // Default price

    // Add refresh button to wallet section
    const walletSection = document.querySelector('.token-stats');
    if (walletSection) {
        const refreshButton = document.createElement('button');
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.className = 'btn btn-sm btn-outline-secondary token-refresh-btn';
        refreshButton.title = 'Refresh balance';
        refreshButton.onclick = function() {
            const savedAddress = localStorage.getItem('walletAddress');
            if (savedAddress) {
                refreshButton.classList.add('rotating');
                fetchBalance(savedAddress).then(() => {
                    setTimeout(() => refreshButton.classList.remove('rotating'), 1000);
                });
            } else {
                showAlert('Error', 'No wallet connected', 'danger');
            }
        };
        walletSection.appendChild(refreshButton);

        // Add some CSS for the refresh button and animations
        const style = document.createElement('style');
        style.textContent = `
            .token-refresh-btn {
                position: absolute;
                right: 10px;
                top: 10px;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .rotating {
                animation: rotate 1s linear infinite;
            }
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            .token-stats {
                position: relative;
            }
            .token-value-pill {
                background-color: #f0f0f0;
                border-radius: 20px;
                padding: 4px 12px;
                display: inline-flex;
                align-items: center;
                font-weight: 500;
                transition: background-color 0.3s, transform 0.2s;
            }
            .token-value-pill.updating {
                animation: pulse 1s ease-in-out;
            }
            @keyframes pulse {
                0% { background-color: #f0f0f0; transform: scale(1); }
                50% { background-color: #e0f7fa; transform: scale(1.05); }
                100% { background-color: #f0f0f0; transform: scale(1); }
            }
            .sparkle {
                position: absolute;
                pointer-events: none;
                background-image: radial-gradient(circle, #fff 10%, transparent 60%);
                border-radius: 50%;
                opacity: 0;
                animation: sparkle 0.8s ease-in-out forwards;
            }
            @keyframes sparkle {
                0% { transform: scale(0); opacity: 0; }
                50% { opacity: 0.8; }
                100% { transform: scale(1.5); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    // Set contract address
    const TOKEN_CONTRACT = localStorage.getItem('tokenContract') || '0x0000000000000000000000000000000000000000';
    contractAddress.textContent = TOKEN_CONTRACT;

    // Token ABI - simplified for common functions
    const TOKEN_ABI = [
        {
            "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }
    ];

    // Check for existing connection
    checkConnection();

    // Connect MetaMask
    connectMetamaskBtn.addEventListener('click', connectMetaMask);

    // WalletConnect functionality would be added here
    connectWalletConnectBtn.addEventListener('click', function() {
        alert('WalletConnect integration coming soon!');
    });
    
    // Create Test Wallet Button
    if (createTestWalletBtn) {
        createTestWalletBtn.addEventListener('click', createTestWallet);
    }

    // Disconnect Wallet
    disconnectWalletBtn.addEventListener('click', disconnectWallet);
    
    // Create Test Wallet function
    async function createTestWallet() {
        try {
            createTestWalletBtn.disabled = true;
            createTestWalletBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating wallet...';
            
            const response = await fetch('/api/token/create-test-wallet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: 'test@example.com' })
            });
            
            const data = await response.json();
            
            if (data.status === 'success' || data.status === 'partial_success') {
                // Save the wallet address to localStorage
                localStorage.setItem('walletAddress', data.wallet.address);
                
                // Store the private key temporarily (in a real app, you would handle this differently)
                localStorage.setItem('tempPrivateKey', data.wallet.private_key);
                
                // Update UI
                connectedAddress.textContent = formatAddress(data.wallet.address);
                walletStatus.style.display = 'block';
                
                // Show wallet details in a modal
                showWalletInfoModal(data.wallet, data.tokens);
                
                // Fetch token balance after a short delay to allow transaction to process
                setTimeout(() => {
                    fetchBalance(data.wallet.address);
                    fetchTransactionHistory(data.wallet.address);
                }, 2000);
            } else {
                showAlert('Error', data.error || 'Failed to create test wallet', 'danger');
            }
        } catch (error) {
            console.error('Error creating test wallet:', error);
            showAlert('Error', 'Failed to create test wallet: ' + error.message, 'danger');
        } finally {
            createTestWalletBtn.disabled = false;
            createTestWalletBtn.innerHTML = 'Create Test Wallet';
        }
    }
    
    // Function to show wallet info modal
    function showWalletInfoModal(wallet, tokens) {
        // Create modal element
        const modalId = 'walletInfoModal';
        let modal = document.getElementById(modalId);
        
        if (modal) {
            document.body.removeChild(modal);
        }
        
        modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal fade';
        modal.tabIndex = '-1';
        modal.role = 'dialog';
        modal.setAttribute('aria-labelledby', 'walletInfoModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="walletInfoModalLabel">Test Wallet Created</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>Important:</strong> This is a test wallet. Save these details securely. 
                            The private key will only be shown once!
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><strong>Address:</strong></label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="${wallet.address}" readonly />
                                <button class="btn btn-outline-secondary" type="button" onclick="navigator.clipboard.writeText('${wallet.address}')">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><strong>Private Key:</strong></label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="${wallet.private_key}" readonly />
                                <button class="btn btn-outline-secondary" type="button" onclick="navigator.clipboard.writeText('${wallet.private_key}')">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                            <small class="text-danger">Never share your private key with anyone!</small>
                        </div>
                        ${tokens ? `
                        <div class="mb-3">
                            <label class="form-label"><strong>Tokens:</strong></label>
                            <p class="mb-1">${tokens.amount} transferred</p>
                            <p class="mb-0"><small>Transaction: ${tokens.tx_hash?.substring(0, 10)}...</small></p>
                        </div>` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                            I've Saved These Details
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show the modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // Claim founding token
    claimFoundingToken.addEventListener('click', claimFoundingTokenFunc);

    // Check connection status
    function checkConnection() {
        const savedAddress = localStorage.getItem('walletAddress');

        if (savedAddress) {
            connectedAddress.textContent = formatAddress(savedAddress);
            walletStatus.style.display = 'block';

            // If MetaMask is available, verify connection is still valid
            if (typeof window.ethereum !== 'undefined') {
                window.ethereum.request({ method: 'eth_accounts' })
                    .then(accounts => {
                        if (accounts.length > 0) {
                            localStorage.setItem('walletAddress', accounts[0]);
                            connectedAddress.textContent = formatAddress(accounts[0]);
                            fetchBalance(accounts[0]);
                            fetchTransactionHistory(accounts[0]);
                        } else {
                            disconnectWallet();
                        }
                    })
                    .catch(err => {
                        console.error('Error checking accounts:', err);
                        disconnectWallet();
                    });
            }
        }
    }

    // Connect to MetaMask
    async function connectMetaMask() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                // Request account access
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                const account = accounts[0];

                localStorage.setItem('walletAddress', account);
                connectedAddress.textContent = formatAddress(account);
                walletStatus.style.display = 'block';

                // Fetch token balance
                fetchBalance(account);

                // Fetch transaction history
                fetchTransactionHistory(account);

                // Add event listener for account changes
                window.ethereum.on('accountsChanged', function (accounts) {
                    if (accounts.length === 0) {
                        // User disconnected from MetaMask
                        disconnectWallet();
                    } else {
                        localStorage.setItem('walletAddress', accounts[0]);
                        connectedAddress.textContent = formatAddress(accounts[0]);
                        fetchBalance(accounts[0]);
                        fetchTransactionHistory(accounts[0]);
                    }
                });
            } catch (error) {
                console.error('User denied account access', error);
                showAlert('Error', 'Failed to connect to MetaMask: ' + error.message, 'danger');
            }
        } else {
            alert('MetaMask is not installed! Please install it from metamask.io');
        }
    }

    // Disconnect wallet
    function disconnectWallet() {
        localStorage.removeItem('walletAddress');
        walletStatus.style.display = 'none';
        connectedAddress.textContent = '0x0000...0000';
        balanceAmount.textContent = '0.00';
        valueAmount.textContent = '$0.00';

        // Reset transaction history
        tokenTransactionsList.innerHTML = '<tr><td colspan="4" class="text-center">No transactions yet</td></tr>';
    }

    // Fetch token balance
    async function fetchBalance(address) {
        try {
            // Show loading state
            const originalBalance = balanceAmount.textContent;
            const originalValue = valueAmount.textContent;
            balanceAmount.innerHTML = '<small>Loading...</small>';
            valueAmount.innerHTML = '<small>Loading...</small>';

            // Try to get balance from our API first
            const response = await fetch(`/api/token/balance/${address}`);
            const data = await response.json();

            if (data.error) {
                console.error('API Error:', data.error);
                // Fallback to direct Web3 call
                await fetchBalanceFromWeb3(address);
            } else {
                balanceAmount.textContent = data.balance.toFixed(2);

                // Update current token price if available
                if (data.token_price) {
                    currentTokenPrice = data.token_price;
                }

                valueAmount.textContent = '$' + data.value_usd.toFixed(2);

                // Add animation to show updated values
                balanceAmount.classList.add('highlight');
                valueAmount.classList.add('highlight');
                setTimeout(() => {
                    balanceAmount.classList.remove('highlight');
                    valueAmount.classList.remove('highlight');
                }, 1500);

                // Create sparkle effect for dramatic flair
                createSparkle(valueAmount);
            }

            return true;
        } catch (error) {
            console.error('Error fetching balance:', error);
            balanceAmount.textContent = '0.00';
            valueAmount.textContent = '$0.00';
            showAlert('Error', 'Failed to fetch token balance', 'danger');
            return false;
        }
    }

    // Fetch balance using Web3 directly
    async function fetchBalanceFromWeb3(address) {
        if (typeof window.ethereum !== 'undefined' && TOKEN_CONTRACT !== '0x0000000000000000000000000000000000000000') {
            try {
                const web3 = new Web3(window.ethereum);
                const tokenContract = new web3.eth.Contract(TOKEN_ABI, TOKEN_CONTRACT);

                const balance = await tokenContract.methods.balanceOf(address).call();
                const decimals = await tokenContract.methods.decimals().call();

                // Convert balance to DOTM
                const formattedBalance = balance / (10 ** decimals);
                balanceAmount.textContent = formattedBalance.toFixed(2);

                // Calculate USD value ($1 per token)
                const usdValue = formattedBalance * 1;
                valueAmount.textContent = '$' + usdValue.toFixed(2);
            } catch (error) {
                console.error('Error fetching balance from Web3:', error);
                balanceAmount.textContent = '0.00';
                valueAmount.textContent = '$0.00';
                // Display a more user-friendly error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'alert alert-warning mt-2';
                errorMessage.innerHTML = 'Could not connect to Ethereum network. Please check your connection.';
                balanceAmount.parentNode.appendChild(errorMessage);
            }
        }
    }

    // Fetch transaction history
    async function fetchTransactionHistory(address) {
        // In a real implementation, you'd fetch transaction history from your API
        // or use an Ethereum explorer API like Etherscan


    // Function to fetch the current token price
    async function fetchTokenPrice() {
        try {
            const start = performance.now();
            const response = await fetch('/api/token/price');
            const data = await response.json();
            const end = performance.now();

            console.log(`Token price fetched in ${end - start}ms:`, data);

            if (data.price) {
                // Update the current price
                const previousPrice = currentTokenPrice;
                currentTokenPrice = data.price;

                // Update UI with new price
                updatePriceDisplay(previousPrice, currentTokenPrice);

                // Update the token value in the header if it exists
                updateTokenValuePill(currentTokenPrice);
            }

            return data;
        } catch (error) {
            console.error('Error fetching token price:', error);
            return { price: currentTokenPrice };
        }
    }

    // Function to create sparkle animation
    function createSparkle(element) {
        const rect = element.getBoundingClientRect();

        for (let i = 0; i < 5; i++) {
            const sparkle = document.createElement('div');
            sparkle.classList.add('sparkle');

            // Random position around the element
            const x = rect.left + Math.random() * rect.width;
            const y = rect.top + Math.random() * rect.height;

            sparkle.style.left = `${x}px`;
            sparkle.style.top = `${y}px`;
            sparkle.style.width = `${10 + Math.random() * 10}px`;
            sparkle.style.height = sparkle.style.width;

            document.body.appendChild(sparkle);

            // Remove the sparkle after animation completes
            setTimeout(() => {
                document.body.removeChild(sparkle);
            }, 800);
        }
    }

    // Function to update price display with animation
    function updatePriceDisplay(oldPrice, newPrice) {
        if (!balanceAmount || !valueAmount) return;

        const balance = parseFloat(balanceAmount.textContent) || 0;
        const newValue = balance * newPrice;

        // Update value display with animation
        valueAmount.classList.add('highlight');
        valueAmount.textContent = `$${newValue.toFixed(2)}`;

        setTimeout(() => {
            valueAmount.classList.remove('highlight');
        }, 1500);
    }

    // Function to update the token value pill in the header
    function updateTokenValuePill(price) {
        const tokenValuePill = document.querySelector('.token-value-pill');
        if (!tokenValuePill) return;

        // Add updating animation
        tokenValuePill.classList.add('updating');

        // Create sparkle effect
        createSparkle(tokenValuePill);

        // Update content
        tokenValuePill.textContent = `1 DOTM = $${price.toFixed(2)}`;

        // Remove animation class after animation completes
        setTimeout(() => {
            tokenValuePill.classList.remove('updating');
        }, 1000);
    }

    // Start price updates when page loads
    function startPriceUpdates() {
        // Fetch immediately
        fetchTokenPrice();

        // Then update every minute
        priceUpdateTimer = setInterval(fetchTokenPrice, 60000);
    }

    // Stop price updates
    function stopPriceUpdates() {
        if (priceUpdateTimer) {
            clearInterval(priceUpdateTimer);
            priceUpdateTimer = null;
        }
    }

    // Start price updates when page loads
    startPriceUpdates();

    // Add event listener to pause updates when tab is not visible
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            if (!priceUpdateTimer) {
                startPriceUpdates();
            }
        } else {
            stopPriceUpdates();
        }
    });

    // Token Price Ping Monitoring
    const triggerPriceUpdateBtn = document.getElementById('triggerPriceUpdate');
    const pingStatus = document.getElementById('pingStatus');
    const pingDataTable = document.getElementById('pingDataTable');

    if (triggerPriceUpdateBtn) {
        // Initial load of ping data
        fetchPingData();

        // Add event listener to trigger price update
        triggerPriceUpdateBtn.addEventListener('click', async function() {
            pingStatus.innerHTML = '<div class="alert alert-info">Triggering token price update...</div>';

            try {
                const response = await fetch('/populate-token-pings');
                const data = await response.json();

                if (data.status === 'success') {
                    pingStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    // Fetch updated ping data
                    fetchPingData();
                } else {
                    pingStatus.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                }
            } catch (error) {
                pingStatus.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            }
        });
    }

    // Function to fetch ping data
    async function fetchPingData() {
        try {
            // Show loading indicator
            if (pingDataTable) {
                pingDataTable.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Fetching ping data...</p>
                        </td>
                    </tr>
                `;
            }

            const response = await fetch('/token-price-pings');
            const data = await response.json();

            if (pingDataTable && data.status === 'success' && data.pings && data.pings.length > 0) {
                // Clear table
                pingDataTable.innerHTML = '';

                // Add ping data rows
                data.pings.forEach(ping => {
                    const row = document.createElement('tr');

                    // Format timestamp
                    const timestamp = ping.timestamp ? new Date(ping.timestamp).toLocaleString() : 
                                     (ping.created_at ? new Date(ping.created_at).toLocaleString() : 'N/A');

                    // Format price with color based on value
                    const price = parseFloat(ping.token_price);
                    const priceColor = price > 1.0 ? 'text-success' : (price < 1.0 ? 'text-danger' : '');

                    row.innerHTML = `
                        <td>${timestamp}</td>
                        <td class="${priceColor}">$${price.toFixed(2)}</td>
                        <td>${ping.ping_destination || 'N/A'}</td>
                        <td>${ping.roundtrip_ms || ping.response_time_ms || 0} ms</td>
                        <td><span class="badge bg-${ping.source === 'etherscan' ? 'primary' : 'secondary'}">${ping.source || 'N/A'}</span></td>
                    `;

                    pingDataTable.appendChild(row);
                });

                // Add animation to show updated table
                pingDataTable.classList.add('highlight');
                setTimeout(() => {
                    pingDataTable.classList.remove('highlight');
                }, 1500);
            } else if (pingDataTable) {
                pingDataTable.innerHTML = '<tr><td colspan="5" class="text-center">No ping data available - Click "Populate Sample Data" to generate test data</td></tr>';
            }
        } catch (error) {
            console.error('Error fetching ping data:', error);
            if (pingDataTable) {
                pingDataTable.innerHTML = `<tr><td colspan="5" class="text-center">Error loading ping data: ${error.message}</td></tr>`;
            }
        }
    }

    // If on tokens page, fetch ping data when page loads
    if (document.getElementById('pingDataTable')) {
        fetchPingData();

        // Add event listener for the "Populate Sample Data" button
        document.querySelector('a[href="/populate-token-pings"]').addEventListener('click', async function(e) {
            e.preventDefault();
            pingStatus.innerHTML = '<div class="alert alert-info">Populating token price pings...</div>';

            try {
                const response = await fetch('/populate-token-pings');
                const data = await response.json();

                if (data.status === 'success') {
                    pingStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    // Fetch updated ping data
                    fetchPingData();
                } else {
                    pingStatus.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                }
            } catch (error) {
                pingStatus.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            }
        });
    }


        // For now, just show a placeholder
        tokenTransactionsList.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <div class="d-flex justify-content-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                    <p class="mt-2">Fetching transaction history...</p>
                </td>
            </tr>
        `;

        // Simulate a delay for demonstration
        setTimeout(() => {
            // Sample transaction data
            tokenTransactionsList.innerHTML = `
                <tr>
                    <td>Today</td>
                    <td>Founding Member</td>
                    <td>+1.00 DOTM</td>
                    <td><span class="badge bg-success">Complete</span></td>
                </tr>
                <tr>
                    <td>Yesterday</td>
                    <td>Data Purchase Reward</td>
                    <td>+0.10 DOTM</td>
                    <td><span class="badge bg-success">Complete</span></td>
                </tr>
            `;
        }, 1500);
    }

    // Claim founding token
    async function claimFoundingTokenFunc() {
        const address = localStorage.getItem('walletAddress');

        if (!address) {
            showAlert('Error', 'Please connect your wallet first', 'danger');
            return;
        }

        // Disable the button
        claimFoundingToken.disabled = true;
        claimFoundingToken.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';

        try {
            // Call our API to assign the founding token
            const response = await fetch('/api/token/founding-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ address: address })
            });

            const data = await response.json();

            if (data.error) {
                showAlert('Error', data.error, 'danger');
            } else {
                showAlert('Success', 'Founding token claimed! Transaction: ' + data.tx_hash.substring(0, 10) + '...', 'success');

                // Update balance after a short delay
                setTimeout(() => {
                    fetchBalance(address);
                    fetchTransactionHistory(address);
                }, 2000);
            }
        } catch (error) {
            console.error('Error claiming token:', error);
            showAlert('Error', 'Failed to claim token: ' + error.message, 'danger');
        } finally {
            // Re-enable the button
            claimFoundingToken.disabled = false;
            claimFoundingToken.innerHTML = 'Claim Founding Token';
        }
    }

    // Show alert in founding claim status
    function showAlert(title, message, type) {
        foundingClaimStatus.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <strong>${title}:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        foundingClaimStatus.style.display = 'block';

        // Auto hide after 5 seconds
        setTimeout(() => {
            const alert = foundingClaimStatus.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    // Format address for display (0x1234...5678)
    function formatAddress(address) {
        return address.substring(0, 6) + '...' + address.substring(address.length - 4);
    }
});