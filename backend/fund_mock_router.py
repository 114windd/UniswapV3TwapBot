#!/usr/bin/env python3
"""
Fund Mock Router Script
Adds liquidity to the MockSwapRouter so it can execute swaps
"""

from twap_bot import connect_to_chain, load_contract, load_wallet, load_erc20_contract

# Configuration
RPC_URL = 'http://127.0.0.1:8545'
ROUTER_ADDRESS = '0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9'
PRIVATE_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'

# Token addresses from deployment
USDC_ADDRESS = '0x5FbDB2315678afecb367f032d93F642f64180aa3'
WETH_ADDRESS = '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512'
DAI_ADDRESS = '0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0'

print("=" * 60)
print("Funding MockSwapRouter with Liquidity")
print("=" * 60)
print()

# Connect
w3 = connect_to_chain(RPC_URL)
account = load_wallet(w3, PRIVATE_KEY)
usdc = load_erc20_contract(w3, USDC_ADDRESS)
weth = load_erc20_contract(w3, WETH_ADDRESS)
dai = load_erc20_contract(w3, DAI_ADDRESS)

print(f"Router Address: {ROUTER_ADDRESS}")
print(f"Funding from: {account.address}")
print()

# Fund with WETH (for USDC -> WETH swaps)
print("1. Funding router with WETH...")
weth_amount = 100 * 10**18  # 100 WETH
tx = weth.functions.transfer(ROUTER_ADDRESS, weth_amount).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"   ✓ Sent {weth_amount / 10**18} WETH")

# Fund with DAI (for WETH -> DAI swaps)
print("2. Funding router with DAI...")
dai_amount = 100000 * 10**18  # 100,000 DAI
tx = dai.functions.transfer(ROUTER_ADDRESS, dai_amount).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"   ✓ Sent {dai_amount / 10**18} DAI")

# Fund with USDC (for reverse swaps)
print("3. Funding router with USDC...")
usdc_amount = 100000 * 10**6  # 100,000 USDC
tx = usdc.functions.transfer(ROUTER_ADDRESS, usdc_amount).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"   ✓ Sent {usdc_amount / 10**6} USDC")

print()
print("=" * 60)
print("✅ Router Funded Successfully!")
print("=" * 60)
print()
print("Router Balances:")
print(f"  • USDC: {usdc.functions.balanceOf(ROUTER_ADDRESS).call() / 10**6:,.2f}")
print(f"  • WETH: {weth.functions.balanceOf(ROUTER_ADDRESS).call() / 10**18:,.2f}")
print(f"  • DAI:  {dai.functions.balanceOf(ROUTER_ADDRESS).call() / 10**18:,.2f}")
print()
print("The router can now execute swaps!")

