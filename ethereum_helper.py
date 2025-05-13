
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
        raise ValueError("ETHEREUM_URL environment variable not set")
    
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
                    cur.execute("SELECT eth_address FROM users WHERE UserID = %s", (user_id,))
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
            'chainId': 1, # Ethereum mainnet
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
        1 * (10 ** 18)  # 1 token in wei
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
