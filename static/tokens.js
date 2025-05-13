
document.addEventListener('DOMContentLoaded', function() {
    const connectMetamaskBtn = document.getElementById('connectMetamask');
    const connectWalletConnectBtn = document.getElementById('connectWalletConnect');
    const disconnectWalletBtn = document.getElementById('disconnectWallet');
    const walletStatus = document.getElementById('walletStatus');
    const connectedAddress = document.getElementById('connectedAddress');
    const contractAddress = document.getElementById('contractAddress');
    const claimFoundingToken = document.getElementById('claimFoundingToken');
    const foundingClaimStatus = document.getElementById('foundingClaimStatus');
    const balanceAmount = document.querySelector('.balance-amount');
    const valueAmount = document.querySelector('.value-amount');
    const tokenTransactionsList = document.getElementById('tokenTransactionsList');
    
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
        
        // Add some CSS for the refresh button
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
    
    // Disconnect Wallet
    disconnectWalletBtn.addEventListener('click', disconnectWallet);
    
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
                valueAmount.textContent = '$' + data.value_usd.toFixed(2);
                
                // Add animation to show updated values
                balanceAmount.classList.add('highlight');
                valueAmount.classList.add('highlight');
                setTimeout(() => {
                    balanceAmount.classList.remove('highlight');
                    valueAmount.classList.remove('highlight');
                }, 1500);
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
                
                // Calculate USD value ($100 per token)
                const usdValue = formattedBalance * 100;
                valueAmount.textContent = '$' + usdValue.toFixed(2);
            } catch (error) {
                console.error('Error fetching balance from Web3:', error);
                balanceAmount.textContent = '0.00';
                valueAmount.textContent = '$0.00';
            }
        }
    }
    
    // Fetch transaction history
    async function fetchTransactionHistory(address) {
        // In a real implementation, you'd fetch transaction history from your API
        // or use an Ethereum explorer API like Etherscan
        
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
