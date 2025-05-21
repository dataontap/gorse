import os
from web3 import Web3
import json

# Load contract ABI
with open('contracts/DOTMToken.json', 'r') as f:
    contract_json = json.load(f)
    contract_abi = contract_json['abi']

# Connect to Ethereum network
def get_web3_connection():
    ethereum_url = os.environ.get('ETHEREUM_URL')
    if not ethereum_url:
        print("Warning: ETHEREUM_URL not set, using development fallback")
        # Use Sepolia testnet as fallback
        ethereum_url = "https://ethereum-sepolia-rpc.publicnode.com"

    return Web3(Web3.HTTPProvider(ethereum_url))

# Get contract instance
def get_token_contract():
    web3 = get_web3_connection()
    token_address = os.environ.get('TOKEN_ADDRESS')
    if not token_address:
        raise ValueError("TOKEN_ADDRESS environment variable not set")

    return web3.eth.contract(address=token_address, abi=contract_abi)

# Get token balance for a user
def get_token_balance(address):
    token_contract = get_token_contract()
    balance = token_contract.functions.balanceOf(address).call()
    return balance / (10 ** 18)  # Convert from wei to DOTM

# Award tokens for data purchase (10% of purchase amount)
def award_data_purchase_tokens(user_id, purchase_amount):
    try:
        from main import get_db_connection
        web3 = get_web3_connection()
        token_contract = get_token_contract()
        admin_key = os.environ.get('ETHEREUM_ADMIN_KEY')

        if not admin_key:
            return False, "Admin key not configured"

        # Get user's ETH address from database
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # First check if eth_address column exists
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='eth_address'
                    """)
                    if cur.fetchone() is None:
                        # Column doesn't exist, create it
                        cur.execute("ALTER TABLE users ADD COLUMN eth_address VARCHAR(255)")
                        conn.commit()

                    # Now get the address
                    with get_db_connection() as conn:
                        if conn:
                            with conn.cursor() as cur:
                                # Check if the column name uses uppercase or lowercase
                                cur.execute("""
                                    SELECT column_name FROM information_schema.columns 
                                    WHERE table_name='users' AND lower(column_name)='userid'
                                """)
                                column_info = cur.fetchone()

                                if column_info:
                                    # Use the exact column name case we found
                                    user_id_column = column_info[0]
                                    cur.execute(f"SELECT eth_address FROM users WHERE {user_id_column} = %s", (user_id,))
                                else:
                                    # Try with lowercase as fallback
                                    cur.execute("SELECT eth_address FROM users WHERE userid = %s", (user_id,))

                                result = cur.fetchone()

                                if not result or not result[0]:
                                    return False, "User has no ETH address"

                                eth_address = result[0]

        # Calculate reward (10% of purchase)
        reward_amount = float(purchase_amount) * 0.1

        # Convert to wei (assuming 18 decimals)
        reward_wei = int(reward_amount * (10 ** 18))

        # Send tokens
        admin_account = web3.eth.account.from_key(admin_key)
        nonce = web3.eth.get_transaction_count(admin_account.address)

        # Create transaction
        tx = token_contract.functions.rewardDataPurchase(
            eth_address,
            reward_wei
        ).build_transaction({
            'chainId': 11155111, # Sepolia testnet
            'gas': 200000,
            'gasPrice': web3.to_wei('50', 'gwei'),
            'nonce': nonce,
        })

        # Sign and send transaction
        signed_tx = web3.eth.account.sign_transaction(tx, admin_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return True, web3.to_hex(tx_hash)
    except Exception as e:
        print(f"Error awarding tokens: {str(e)}")
        return False, str(e)
def reward_data_purchase(user_address, purchase_amount_cents):
    web3 = get_web3_connection()
    token_contract = get_token_contract()
    
    # Get DOTM Token contract address from environment variables
    TOKEN_CONTRACT_ADDRESS = os.environ.get('TOKEN_ADDRESS', '0x8250951Ff1AE04adB9dCa9233274710dDCb1850a')



# Fetch current DOTM token price from Etherscan
def get_token_price_from_etherscan():
    import requests
    import time
    import json
    import random
    from datetime import datetime
    import socket

    start_time = time.time() * 1000  # Start time in milliseconds
    eth_price = 2500  # Default value
    token_price = 1.0  # 1 DOTM = $1 USD
    request_time = 0
    response_time = 0
    source = 'development'
    error_msg = None
    ping_destination = 'local'
    roundtrip_ms = random.randint(50, 200)  # Simulate network latency

    # Create token_price_pings table if it doesn't exist
    try:
        from main import get_db_connection
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if table exists
                    cur.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_price_pings')"
                    )
                    table_exists = cur.fetchone()[0]

                    # Create table if it doesn't exist
                    if not table_exists:
                        print("Creating token_price_pings table...")
                        create_table_sql = """
                        CREATE TABLE token_price_pings (
                            id SERIAL PRIMARY KEY,
                            token_price DECIMAL(18,9) NOT NULL,
                            request_time_ms INTEGER,
                            response_time_ms INTEGER,
                            roundtrip_ms INTEGER,
                            ping_destination VARCHAR(255),
                            source VARCHAR(100),
                            additional_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                        cur.execute(create_table_sql)
                        conn.commit()
                        print("token_price_pings table created successfully")

                    # Generate some simulated price data
                    # In a real app, you'd fetch this from an API
                    end_time = time.time() * 1000
                    request_time = int(end_time - start_time)

                    # Small random variation in token price for demonstration
                    token_price = 1.0 + (random.random() * 0.1 - 0.05)

                    # Record the ping in database
                    try:
                        hostname = socket.gethostname()
                        additional_data = json.dumps({
                            'timestamp': datetime.now().isoformat(),
                            'hostname': hostname
                        })

                        cur.execute(
                            """INSERT INTO token_price_pings 
                               (token_price, request_time_ms, response_time_ms, roundtrip_ms, 
                                ping_destination, source, additional_data)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (token_price, request_time, response_time, roundtrip_ms, 
                             ping_destination, source, additional_data)
                        )
                        conn.commit()
                        print(f"Recorded token price ping: {token_price} (took {request_time}ms)")
                    except Exception as e:
                        print(f"Error recording token price ping: {str(e)}")
                        conn.rollback()

                    if not table_exists:
                        print("Creating token_price_pings table...")
                        cur.execute("""
                            CREATE TABLE token_price_pings (
                                id SERIAL PRIMARY KEY,
                                token_price NUMERIC(10, 4) NOT NULL,
                                request_time_ms INTEGER,
                                response_time_ms INTEGER,
                                ping_destination VARCHAR(100),
                                roundtrip_ms INTEGER,
                                source VARCHAR(50),
                                additional_data JSONB,
                                timestamp TIMESTAMP,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        conn.commit()
                        print("token_price_pings table created successfully")
    except Exception as create_err:
        print(f"Error checking/creating token_price_pings table: {str(create_err)}")

    try:
        # Try to use Etherscan API if configured
        if os.environ.get('ETHERSCAN_API_KEY'):
            source = 'etherscan'
            etherscan_api_key = os.environ.get('ETHERSCAN_API_KEY')

            # Use a real API endpoint in production
            etherscan_url = f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={etherscan_api_key}"
        else:
            # Development mode - simulate API call
            source = 'development'
            etherscan_url = "http://localhost:5000/mock_etherscan_api"  # Example mock API

        start_ping = time.time() * 1000
        response = requests.get(
            etherscan_url,
            timeout=5
        )
        end_ping = time.time() * 1000

        request_time = time.time() * 1000 - start_time
        roundtrip_ms = end_ping - start_ping

        # Parse the actual token price from the response
        if source == 'etherscan':
            eth_price = float(response.json().get('result', {}).get('ethusd', 2500))
        else:
            eth_price = 2500 # Default Eth price

        # Simulate some variation in price
        variation = random.uniform(-0.05, 0.05)
        token_price = token_price + variation

        response_time = time.time() * 1000 - start_time
        current_timestamp = datetime.now()

        # Store ping data in database
        from main import get_db_connection

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO token_price_pings (token_price, request_time_ms, response_time_ms, ping_destination, roundtrip_ms, source, additional_data, timestamp) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (
                            token_price,
                            int(request_time),
                            int(response_time),
                            etherscan_url,
                            int(roundtrip_ms),
                            source,
                            json.dumps({
                                'eth_price': eth_price,
                                'variation': variation,
                                'user_id': 1,  # Using fixed UserID for demo mode matching database ID
                                'environment': 'development' if not os.environ.get('ETHEREUM_URL') else 'production'
                            }),
                            current_timestamp
                        )
                    )
                    ping_id = cur.fetchone()[0]
                    conn.commit()
                    print(f"Stored token price ping: {ping_id}")

        return {
            'price': token_price,
            'timestamp': current_timestamp.isoformat(),
            'request_time_ms': int(request_time),
            'response_time_ms': int(response_time),
            'ping_destination': etherscan_url,
            'roundtrip_ms': int(roundtrip_ms),
            'source': source
        }

    except Exception as e:
        print(f"Error fetching token price: {str(e)}")
        error_msg = str(e)
        current_timestamp = datetime.now()

        # Even on error, try to log the attempt
        try:
            from main import get_db_connection
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO token_price_pings (token_price, request_time_ms, response_time_ms, ping_destination, roundtrip_ms, source, additional_data, timestamp) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                            (
                                1.0,  # Default $1 value
                                0,
                                0,
                                etherscan_url,
                                0,
                                'error',
                                json.dumps({
                                    'error': error_msg,
                                }),
                                current_timestamp
                            )
                        )
                        ping_id = cur.fetchone()[0]
                        conn.commit()
                        print(f"Stored error token price ping: {ping_id}")
        except Exception as log_err:
            print(f"Error logging token price error: {str(log_err)}")

        # Return default value on error
        return {
            'price': 1.0,  # Default $1 value without variation
            'timestamp': current_timestamp.isoformat(),
            'request_time_ms': 0,
            'response_time_ms': 0,
            'ping_destination': etherscan_url,
            'roundtrip_ms': 0,
            'error': error_msg,
            'source': 'error'
        }

    # Special case: if purchasing global data ($10), award exactly 1 DOTM
    if purchase_amount_cents == 1000 and 'global_data' in os.environ.get('LAST_PURCHASE_PRODUCT', ''):
        token_reward = 1.0  # Fixed 1 DOTM for 10GB data purchase
    else:
        # Otherwise, use the default 10% calculation
        token_reward = (purchase_amount_cents / 10000)  # 10% of purchase in token units

    print(f"Rewarding {token_reward} DOTM tokens for purchase of {purchase_amount_cents} cents")

    # Get admin account
    admin_private_key = os.environ.get('ADMIN_PRIVATE_KEY')
    admin_account = web3.eth.account.from_key(admin_private_key)

    # Build transaction
    tx = token_contract.functions.rewardDataPurchase(
        user_address,
        int(token_reward * (10 ** 18))  # Convert to wei
    ).build_transaction({
        'from': admin_account.address,
        'nonce': web3.eth.get_transaction_count(admin_account.address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    # Sign and send transaction
    signed_tx = web3.eth.account.sign_transaction(tx, admin_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return web3.to_hex(tx_hash)

# Assign one token to a founding member
def assign_founding_token(member_address):
    web3 = get_web3_connection()
    token_contract = get_token_contract()

    # Get admin account
    admin_private_key = os.environ.get('ADMIN_PRIVATE_KEY')
    admin_account = web3.eth.account.from_key(admin_private_key)

    # Build transaction
    tx = token_contract.functions.mint(
        member_address,
        100 * (10 ** 18)  # 100 tokens in wei
    ).build_transaction({
        'from': admin_account.address,
        'nonce': web3.eth.get_transaction_count(admin_account.address),
        'gas': 200000,
        'gasPrice': web3.eth.gas_price
    })

    # Sign and send transaction
    signed_tx = web3.eth.account.sign_transaction(tx, admin_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return web3.to_hex(tx_hash)