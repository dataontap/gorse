
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
def reward_data_purchase(user_address, purchase_amount_cents):
    web3 = get_web3_connection()
    token_contract = get_token_contract()
    
    # Convert to token units (assuming 1 DOTM = $100)
    token_reward = (purchase_amount_cents / 10000)  # 10% of purchase in token units
    
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
