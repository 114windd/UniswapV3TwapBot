import os
from dotenv import load_dotenv

load_dotenv()

# Blockchain connection
RPC_URL =http://127.0.0.1:8545 
PRIVATE_KEY =0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0

# Contract addresses
CONTRACT_ADDRESS =0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

# Bot configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_GAS_PRICE = int(os.getenv("MAX_GAS_PRICE", "50"))  # In gwei
CONFIRMATION_BLOCKS = int(os.getenv("CONFIRMATION_BLOCKS", "1"))

# Timing
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5  # seconds