import logging
import time
from web3 import Web3
from typing import Optional
from web3.contract.contract import Contract
from eth_account import Account
from typing import Callable
import json
import asyncio




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_chain(rpc_url: str) -> Web3:
    """
    Connect to an Ethereum node using the provided RPC URL.
    
    Args:
        rpc_url (str): The RPC endpoint URL (e.g., Infura, Alchemy, or local node)
    
    Returns:
        Web3: Connected Web3 instance
    
    Raises:
        ConnectionError: If unable to connect to the Ethereum node
        ValueError: If the RPC URL is invalid
    """
    if not rpc_url:
        raise ValueError("RPC URL cannot be empty")
    
    if not rpc_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
        raise ValueError("Invalid RPC URL format. Must start with http://, https://, ws://, or wss://")
    
    logger.info(f"Attempting to connect to Ethereum node at: {rpc_url}")
    
    try:
        # Initialize Web3 connection
        w3 = Web3(Web3.HTTPProvider(rpc_url))
                
        # Test connection by checking if we can get the latest block
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Test connection with a simple call
                latest_block = w3.eth.block_number
                chain_id = w3.eth.chain_id
                
                # Verify we got valid responses
                if latest_block == 0:
                    raise ConnectionError("Connected but received block number 0")
                
                logger.info(f"Successfully connected to Ethereum network")
                logger.info(f"Chain ID: {chain_id}")
                logger.info(f"Latest block: {latest_block}")
                logger.info(f"Node version: {w3.client_version}")
                
                # Check if node is synced (block should be recent)
                current_time = int(time.time())
                latest_block_data = w3.eth.get_block('latest')
                block_timestamp = latest_block_data['timestamp']
                
                # If block is more than 15 minutes old, warn about sync status
                if current_time - block_timestamp > 900:  # 15 minutes
                    logger.warning(f"Node may not be fully synced. Latest block timestamp: {block_timestamp}, current time: {current_time}")
                
                return w3
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise ConnectionError(f"Failed to connect after {max_retries} attempts: {str(e)}")
                    
    except Exception as e:
        logger.error(f"Failed to initialize Web3 connection: {str(e)}")
        raise ConnectionError(f"Cannot connect to Ethereum node: {str(e)}")

def load_contract(w3: Web3, contract_address: str, abi_file_path: str) -> Contract:
    """
    Load a Web3 contract instance.
    
    Args:
        w3 (Web3): Connected Web3 instance
        contract_address (str): The deployed contract address
        abi_file_path (str): Path to JSON file containing contract ABI
    
    Returns:
        Contract: Web3 contract instance
    """
    logger.info(f"Loading contract at {contract_address}")
    
    # Load ABI from file
    with open(abi_file_path, 'r') as f:
        abi_data = json.load(f)
        
        # Handle artifact format or direct ABI
        if isinstance(abi_data, dict) and 'abi' in abi_data:
            abi = abi_data['abi']
        else:
            abi = abi_data
    
    # Create contract instance
    contract = w3.eth.contract(
        address=w3.to_checksum_address(contract_address),
        abi=abi
    )
    
    logger.info("Contract loaded successfully")
    return contract

def load_erc20_contract(w3: Web3, token_address: str) -> Contract:
    """
    Load an ERC20 token contract.
    
    Args:
        w3 (Web3): Connected Web3 instance
        token_address (str): The ERC20 token contract address
    
    Returns:
        Contract: Web3 contract instance for ERC20 token
    """
    erc20_abi = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
        {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
    ]
    
    return w3.eth.contract(
        address=w3.to_checksum_address(token_address),
        abi=erc20_abi
    )

def load_wallet(w3: Web3, private_key: str) -> Account:
    """
    Load a wallet from private key for signing transactions.
    
    Args:
        w3 (Web3): Connected Web3 instance
        private_key (str): Private key (with or without 0x prefix)
    
    Returns:
        Account: eth_account Account object for signing transactions
    """
    logger.info("Loading wallet...")
    
    # Remove 0x prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    # Create account from private key
    account = Account.from_key(private_key)
    
    logger.info(f"Wallet loaded: {account.address}")
    return account
def execute_slice(w3: Web3, contract: Contract, account: Account, order_id: int) -> dict:
    """
    Execute one slice of a TWAP order.
    
    Args:
        w3 (Web3): Connected Web3 instance
        contract (Contract): TWAP bot contract instance
        account (Account): Account for signing transactions
        order_id (int): ID of the order to execute a slice for
    
    Returns:
        dict: Transaction result with hash and receipt
    """
    logger.info(f"Executing slice for order ID: {order_id}")
    
    # Check if slice can be executed (basic validation)
    try:
        order = contract.functions.getOrder(order_id).call()
        logger.info(f"Order found - next execution time: {order[11]}, current time: {int(time.time())}")
    except Exception as e:
        logger.error(f"Failed to get order {order_id}: {e}")
        raise
    
    # Build transaction
    tx = contract.functions.executeSlice(order_id).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 300000,  # Estimate gas limit
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    logger.info(f"Transaction sent: {tx_hash.hex()}")
    
    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        logger.info(f"Slice executed successfully - Gas used: {receipt.gasUsed}")
    else:
        logger.error("Transaction failed")
        raise Exception("Slice execution failed")
    
    return {
        'tx_hash': tx_hash.hex(),
        'receipt': receipt,
        'gas_used': receipt.gasUsed
    }

def get_order(contract: Contract, order_id: int) -> dict:
    """
    Get order details from the smart contract.
    
    Args:
        contract (Contract): TWAP bot contract instance
        order_id (int): ID of the order to retrieve
    
    Returns:
        dict: Order details with named fields
    """
    logger.info(f"Getting order details for ID: {order_id}")
    
    # Call the contract function
    order_data = contract.functions.getOrder(order_id).call()
    
    # Convert tuple to named dictionary based on smart contract Order struct
    order = {
        'orderId': order_data[0],
        'creator': order_data[1],
        'tokenIn': order_data[2],
        'tokenOut': order_data[3],
        'totalAmount': order_data[4],
        'interval': order_data[5],
        'duration': order_data[6],
        'sliceSize': order_data[7],
        'maxSlippageBps': order_data[8],
        'poolFee': order_data[9],
        'startTime': order_data[10],
        'slicesExecuted': order_data[11],
        'nextExecutionTime': order_data[12],
        'totalOut': order_data[13],
        'cancelled': order_data[14]
    }
    
    logger.info(f"Order {order_id} - Executed: {order['slicesExecuted']}, Cancelled: {order['cancelled']}")
    
    return order
def listen_for_orders(w3: Web3, contract: Contract, callback: Callable[[dict], None]) -> None:
    """
    Listen for new OrderCreated events and process them.
    
    Args:
        w3 (Web3): Connected Web3 instance
        contract (Contract): TWAP bot contract instance
        callback (Callable): Function to call when new order is detected
    """
    logger.info("Starting to listen for new orders...")
    
    # Create event filter for OrderCreated events
    event_filter = contract.events.OrderCreated.create_filter(from_block='latest')
    
    while True:
        try:
            # Get new entries
            for event in event_filter.get_new_entries():
                logger.info(f"New order detected: {event['args']['orderId']}")
                
                # Extract event data
                order_event = {
                    'orderId': event['args']['orderId'],
                    'creator': event['args']['creator'],
                    'tokenIn': event['args']['tokenIn'],
                    'tokenOut': event['args']['tokenOut'],
                    'totalAmount': event['args']['totalAmount'],
                    'duration': event['args']['duration'],
                    'interval': event['args']['interval'],
                    'sliceSize': event['args']['sliceSize'],
                    'blockNumber': event['blockNumber'],
                    'transactionHash': event['transactionHash'].hex()
                }
                
                # Call the callback function
                try:
                    callback(order_event)
                except Exception as e:
                    logger.error(f"Error in callback for order {order_event['orderId']}: {e}")
            
            # Small delay to avoid excessive polling
            time.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("Stopping order listener...")
            break
        except Exception as e:
            logger.error(f"Error listening for events: {e}")
            asyncio.sleep(5)  # Wait before retrying

async def async_listen_for_orders(w3: Web3, contract: Contract, callback: Callable[[dict], None]) -> None:
    """
    Async version of listen_for_orders for better integration.
    
    Args:
        w3 (Web3): Connected Web3 instance
        contract (Contract): TWAP bot contract instance
        callback (Callable): Function to call when new order is detected
    """
    logger.info("Starting async order listener...")
    
    event_filter = contract.events.OrderCreated.create_filter(fromBlock='latest')
    
    while True:
        try:
            for event in event_filter.get_new_entries():
                logger.info(f"New order detected: {event['args']['orderId']}")
                
                order_event = {
                    'orderId': event['args']['orderId'],
                    'creator': event['args']['creator'],
                    'tokenIn': event['args']['tokenIn'],
                    'tokenOut': event['args']['tokenOut'],
                    'totalAmount': event['args']['totalAmount'],
                    'duration': event['args']['duration'],
                    'interval': event['args']['interval'],
                    'sliceSize': event['args']['sliceSize'],
                    'blockNumber': event['blockNumber'],
                    'transactionHash': event['transactionHash'].hex()
                }
                
                try:
                    callback(order_event)
                except Exception as e:
                    logger.error(f"Error in callback for order {order_event['orderId']}: {e}")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in async listener: {e}")
            await asyncio.sleep(5)


# Example usage and testing
if __name__ == "__main__":
    # Test the connection function
    test_rpc_url = "http://127.0.0.1:8545"  # Replace with actual RPC
    
    try:
        w3 = connect_to_chain(test_rpc_url)
        print(f"Connection successful! Chain ID: {w3.eth.chain_id}")
    except Exception as e:
        print(f"Connection failed: {e}")