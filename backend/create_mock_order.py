#!/usr/bin/env python3
"""
Mock Order Creation Script for TWAP Bot
Creates a sample TWAP order for testing the bot's automated execution
"""

import sys
import time
from twap_bot import connect_to_chain, load_contract, load_wallet, load_erc20_contract

# Configuration
RPC_URL = 'http://127.0.0.1:8545'
CONTRACT_ADDRESS = '0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9'  # Update with your deployed address
ABI_FILE = '../out/UniSwapV3TWAPBot.sol/UniswapV3TWAPBot.json'
PRIVATE_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'  # Anvil default account

# Mock token addresses (from deployment)
USDC_ADDRESS = '0x5FbDB2315678afecb367f032d93F642f64180aa3'
WETH_ADDRESS = '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512'

def main():
    print("=" * 60)
    print("TWAP Bot - Mock Order Creation Script")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Connect to blockchain
        print("📡 Step 1: Connecting to blockchain...")
        w3 = connect_to_chain(RPC_URL)
        print(f"   ✓ Connected to Chain ID: {w3.eth.chain_id}")
        print(f"   ✓ Latest Block: {w3.eth.block_number}")
        print()
        
        # Step 2: Load contracts
        print("📄 Step 2: Loading contracts...")
        contract = load_contract(w3, CONTRACT_ADDRESS, ABI_FILE)
        account = load_wallet(w3, PRIVATE_KEY)
        usdc = load_erc20_contract(w3, USDC_ADDRESS)
        weth = load_erc20_contract(w3, WETH_ADDRESS)
        print(f"   ✓ TWAP Bot: {CONTRACT_ADDRESS}")
        print(f"   ✓ Account: {account.address}")
        print(f"   ✓ USDC Token: {USDC_ADDRESS}")
        print(f"   ✓ WETH Token: {WETH_ADDRESS}")
        print()
        
        # Step 3: Check balances
        print("💰 Step 3: Checking token balances...")
        usdc_balance = usdc.functions.balanceOf(account.address).call()
        usdc_balance_formatted = usdc_balance / 10**6  # USDC has 6 decimals
        print(f"   ✓ USDC Balance: {usdc_balance_formatted:,.2f} USDC")
        
        if usdc_balance == 0:
            print("   ❌ ERROR: No USDC balance! Make sure mock tokens are deployed and minted.")
            return
        print()
        
        # Step 4: Approve TWAP contract
        print("✅ Step 4: Approving TWAP contract to spend USDC...")
        amount_to_deposit = 1000 * 10**6  # 1000 USDC
        
        current_allowance = usdc.functions.allowance(account.address, CONTRACT_ADDRESS).call()
        if current_allowance < amount_to_deposit:
            print(f"   ℹ Approving {amount_to_deposit / 10**6} USDC...")
            tx = usdc.functions.approve(CONTRACT_ADDRESS, amount_to_deposit).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"   ✓ Approval successful! Tx: {tx_hash.hex()[:20]}...")
            else:
                print("   ❌ Approval failed!")
                return
        else:
            print(f"   ✓ Already approved (allowance: {current_allowance / 10**6} USDC)")
        print()
        
        # Step 5: Deposit tokens
        print("💵 Step 5: Depositing tokens to TWAP Bot...")
        deposited_balance = contract.functions.userBalances(account.address, USDC_ADDRESS).call()
        
        if deposited_balance < amount_to_deposit:
            print(f"   ℹ Depositing {amount_to_deposit / 10**6} USDC...")
            tx = contract.functions.deposit(USDC_ADDRESS, amount_to_deposit).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': w3.eth.gas_price
            })
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"   ✓ Deposit successful! Tx: {tx_hash.hex()[:20]}...")
            else:
                print("   ❌ Deposit failed!")
                return
        else:
            print(f"   ✓ Already deposited (balance: {deposited_balance / 10**6} USDC)")
        print()
        
        # Step 6: Create TWAP order
        print("🎯 Step 6: Creating TWAP Order...")
        print("   Order Parameters:")
        print(f"   • Token In: USDC ({amount_to_deposit / 10**6} USDC)")
        print(f"   • Token Out: WETH")
        print(f"   • Duration: 60 seconds (1 minute)")
        print(f"   • Interval: 10 seconds")
        print(f"   • Number of Slices: 6")
        print(f"   • Slice Size: {amount_to_deposit / 6 / 10**6:.2f} USDC per slice")
        print(f"   • Max Slippage: 0.5%")
        print(f"   • Pool Fee: 0.3%")
        print()
        
        tx = contract.functions.createTWAPOrder(
            USDC_ADDRESS,           # tokenIn
            WETH_ADDRESS,           # tokenOut
            amount_to_deposit,      # totalAmount (1000 USDC)
            60,                     # duration (1 minute)
            10,                     # interval (10 seconds)
            50,                     # maxSlippage (0.5%)
            3000                    # poolFee (0.3%)
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 400000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"   ⏳ Transaction sent: {tx_hash.hex()}")
        print(f"   ⏳ Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"   ✓ Order created successfully!")
            print()
            
            # Get order ID from event
            order_events = contract.events.OrderCreated().process_receipt(receipt)
            if order_events:
                order_id = order_events[0]['args']['orderId']
                print("📊 Order Details:")
                print(f"   • Order ID: {order_id}")
                print(f"   • Transaction: {tx_hash.hex()}")
                print(f"   • Gas Used: {receipt.gasUsed:,}")
                print()
                
                # Fetch and display order details
                order = contract.functions.getOrder(order_id).call()
                print("📋 Order Information:")
                print(f"   • Creator: {order[1]}")
                print(f"   • Total Amount: {order[4] / 10**6} USDC")
                print(f"   • Slice Size: {order[7] / 10**6} USDC")
                print(f"   • Slices Executed: {order[11]}")
                print(f"   • Next Execution: {order[12]} (Unix timestamp)")
                print(f"   • Start Time: {order[10]} (Unix timestamp)")
                print()
                
                # Calculate next execution time
                next_exec = order[12]
                current_time = int(time.time())
                if next_exec <= current_time:
                    print("   ⚡ READY: First slice can be executed NOW!")
                else:
                    wait_time = next_exec - current_time
                    print(f"   ⏰ WAITING: First slice ready in {wait_time} seconds")
                print()
                
                print("=" * 60)
                print("✅ SUCCESS! Mock order created successfully!")
                print("=" * 60)
                print()
                print("🤖 Next Steps:")
                print("   1. Start the bot with: python3 main.py")
                print("   2. The bot will automatically execute slices every 10 SECONDS")
                print("   3. Monitor the logs to see slice executions")
                print("   4. All 6 slices will complete in ~1 minute!")
                print()
                print(f"   Or manually execute a slice with:")
                print(f"   cast send {CONTRACT_ADDRESS} 'executeSlice(uint256)' {order_id} \\")
                print(f"        --rpc-url {RPC_URL} --private-key {PRIVATE_KEY}")
                print()
            else:
                print("   ⚠ Warning: Could not retrieve order ID from event")
        else:
            print("   ❌ Order creation failed!")
            print(f"   Transaction: {tx_hash.hex()}")
            return
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR OCCURRED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Anvil is running: anvil")
        print("  2. Make sure contracts are deployed")
        print("  3. Update CONTRACT_ADDRESS in this script if needed")
        print("  4. Check that mock tokens have sufficient balance")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

