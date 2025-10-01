import logging
import time
from web3 import Web3
from web3.contract.contract import Contract
from eth_account import Account
from typing import Dict, List

# Import our functions (assuming they're in the same file or properly imported)
from twap_bot import connect_to_chain
from twap_bot import load_contract, load_erc20_contract
from twap_bot import load_wallet
from twap_bot import execute_slice
from twap_bot import get_order
from twap_bot import listen_for_orders

logger = logging.getLogger(__name__)

class TWAPBot:
    """Simple TWAP Bot for executing slices automatically."""
    
    def __init__(self, rpc_url: str, contract_address: str, abi_file_path: str, private_key: str):
        """Initialize the bot with connection details."""
        self.w3 = connect_to_chain(rpc_url)
        self.contract = load_contract(self.w3, contract_address, abi_file_path)
        self.account = load_wallet(self.w3, private_key)
        self.active_orders: List[int] = []
        
        logger.info(f"TWAP Bot initialized with wallet: {self.account.address}")
        
        # Load existing orders on startup
        self._load_existing_orders()
    
    def _load_existing_orders(self):
        """Load any existing orders that haven't been completed yet."""
        try:
            next_order_id = self.contract.functions.nextOrderId().call()
            logger.info(f"Checking for existing orders (0 to {next_order_id - 1})...")
            
            for order_id in range(next_order_id):
                try:
                    order = get_order(self.contract, order_id)
                    
                    # Only add orders that are not cancelled and not fully executed
                    if not order['cancelled']:
                        total_slices = order['duration'] // order['interval']
                        current_time = int(time.time())
                        
                        # Check if order hasn't expired and has slices remaining
                        if (current_time <= order['startTime'] + order['duration'] and 
                            order['slicesExecuted'] < total_slices):
                            self.active_orders.append(order_id)
                            logger.info(f"✓ Loaded existing order {order_id} (slices: {order['slicesExecuted']}/{total_slices})")
                        else:
                            logger.info(f"⊗ Skipping completed/expired order {order_id}")
                except Exception as e:
                    logger.error(f"Error loading order {order_id}: {e}")
            
            if self.active_orders:
                logger.info(f"📊 Monitoring {len(self.active_orders)} active order(s): {self.active_orders}")
            else:
                logger.info("📭 No active orders found. Waiting for new orders...")
                
        except Exception as e:
            logger.error(f"Error loading existing orders: {e}")
    
    def check_and_execute_slices(self):
        """Check active orders and execute slices when ready."""
        current_time = int(time.time())
        
        for order_id in self.active_orders.copy():
            try:
                order = get_order(self.contract, order_id)
                
                # Skip if order is cancelled or completed
                if order['cancelled']:
                    self.active_orders.remove(order_id)
                    logger.info(f"Removed cancelled order {order_id}")
                    continue
                
                # Check if slice is ready to execute
                if current_time >= order['nextExecutionTime']:
                    # Check if order has expired
                    if current_time > order['startTime'] + order['duration']:
                        self.active_orders.remove(order_id)
                        logger.info(f"Removed expired order {order_id}")
                        continue
                    
                    # Execute the slice
                    try:
                        result = execute_slice(self.w3, self.contract, self.account, order_id)
                        logger.info(f"Executed slice for order {order_id}: {result['tx_hash']}")
                    except Exception as e:
                        logger.error(f"Failed to execute slice for order {order_id}: {e}")
                
            except Exception as e:
                logger.error(f"Error checking order {order_id}: {e}")
    
    def handle_new_order(self, order_event: dict):
        """Handle new order events."""
        order_id = order_event['orderId']
        logger.info(f"Adding new order {order_id} to active orders")
        self.active_orders.append(order_id)
    
    def run(self):
        """Main bot loop."""
        logger.info("Starting TWAP Bot...")
        
        # Start listening for new orders in background
        import threading
        listener_thread = threading.Thread(
            target=listen_for_orders,
            args=(self.w3, self.contract, self.handle_new_order),
            daemon=True
        )
        listener_thread.start()
        
        # Main execution loop
        try:
            while True:
                self.check_and_execute_slices()
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("TWAP Bot stopped")

# Example usage
if __name__ == "__main__":
    # Configuration
    RPC_URL = "http://127.0.0.1:8545"  # Anvil
    CONTRACT_ADDRESS = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"  # TWAP Bot contract address
    ABI_FILE_PATH = '/home/windd/foundry-projects/korede/koredeRepo/packages/twap-bot/out/UniSwapV3TWAPBot.sol/UniswapV3TWAPBot.json'
    PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # Your private key
    
    # Create and run bot
    bot = TWAPBot(RPC_URL, CONTRACT_ADDRESS, ABI_FILE_PATH, PRIVATE_KEY)
    bot.run()