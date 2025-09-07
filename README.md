# UniSwap V3 TWAP Bot

A decentralized Time-Weighted Average Price (TWAP) bot for executing large trades on Uniswap V3 with minimal price impact through automated slice execution.

## Overview

The TWAP Bot allows users to split large token swaps into smaller, time-distributed slices to reduce price impact and achieve better average execution prices. Instead of executing a large trade all at once, the bot spreads it across multiple smaller transactions over a specified time period.

## Features

- **Automated Slice Execution**: Break large trades into smaller slices executed over time
- **Minimal Price Impact**: Reduce slippage by avoiding large single transactions
- **Flexible Parameters**: Customizable duration, intervals, and slippage tolerance
- **Multi-Token Support**: Works with any ERC20 tokens with Uniswap V3 pools
- **Event-Driven Architecture**: Automatic detection and execution of new orders
- **Comprehensive Testing**: Full test suite with fuzz testing capabilities
- **Multi-Network Support**: Deployable on mainnet, testnets, and local development

## Architecture

### Smart Contracts

- **`UniswapV3TWAPBot.sol`**: Main contract handling order creation, slice execution, and fund management
- **`MockSwapRouter.sol`**: Mock router for testing purposes
- **`MockERC20.sol`**: Mock ERC20 tokens for testing

### Python Bot

- **`twap_bot.py`**: Core functions for blockchain interaction
- **`main.py`**: Automated bot that monitors and executes TWAP orders

## Prerequisites

- **Foundry**: For smart contract development and testing
- **Python 3.8+**: For the automation bot
- **Node.js**: For additional tooling (optional)

### Required Tools

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install Python dependencies
pip install web3 eth-account python-dotenv
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd uniswap-v3-twap-bot
```

2. **Install smart contract dependencies**
```bash
forge install
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with the following variables:

```bash
# Private key for deployment and bot operations
PRIVATE_KEY=your_private_key_here

# RPC URLs for different networks
ANVIL_RPC_URL=http://127.0.0.1:8545
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/your_project_id

# Contract addresses (filled after deployment)
TWAP_BOT_ADDRESS=
UNISWAP_V3_ROUTER_ADDRESS=

# Bot configuration
BOT_CHECK_INTERVAL=10
GAS_LIMIT=300000
```

## Usage

### 1. Deploy Contracts

**Local Development (Anvil):**
```bash
# Start local blockchain
anvil

# Deploy contracts
forge script script/DeployUniSwapV3TWAPBOT.s.sol --rpc-url $ANVIL_RPC_URL --private-key $PRIVATE_KEY --broadcast
```

**Sepolia Testnet:**
```bash
forge script script/DeployUniSwapV3TWAPBOT.s.sol --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast --verify
```

### 2. Create TWAP Orders

**Using Cast (Command Line):**
```bash
# First deposit tokens
cast send $TWAP_BOT_ADDRESS "deposit(address,uint256)" $TOKEN_ADDRESS $AMOUNT --private-key $PRIVATE_KEY --rpc-url $RPC_URL

# Create TWAP order
cast send $TWAP_BOT_ADDRESS "createTWAPOrder(address,address,uint256,uint256,uint256,uint256,uint24)" \
  $TOKEN_IN $TOKEN_OUT $TOTAL_AMOUNT $DURATION $INTERVAL $MAX_SLIPPAGE $POOL_FEE \
  --private-key $PRIVATE_KEY --rpc-url $RPC_URL
```

**Using Python:**
```python
from twap_bot import connect_to_chain, load_contract, load_wallet

# Connect to blockchain
w3 = connect_to_chain(RPC_URL)
contract = load_contract(w3, CONTRACT_ADDRESS, ABI_PATH)
account = load_wallet(w3, PRIVATE_KEY)

# Create order parameters
token_in = "0x..."
token_out = "0x..."
total_amount = 1000 * 10**18  # 1000 tokens
duration = 3600  # 1 hour
interval = 300   # 5 minutes
max_slippage = 50  # 0.5%
pool_fee = 3000  # 0.3%

# Build and send transaction
tx = contract.functions.createTWAPOrder(
    token_in, token_out, total_amount, duration, interval, max_slippage, pool_fee
).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 200000,
    'gasPrice': w3.eth.gas_price
})

# Sign and send
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
```

### 3. Run the Automation Bot

```bash
python main.py
```

The bot will:
- Listen for new `OrderCreated` events
- Monitor active orders for execution readiness
- Automatically execute slices when timing conditions are met
- Handle errors and retry logic

## Smart Contract Interface

### Key Functions

**Deposit tokens:**
```solidity
function deposit(address token, uint256 amount) external returns (bool success)
```

**Create TWAP order:**
```solidity
function createTWAPOrder(
    address tokenIn,
    address tokenOut,
    uint256 totalAmount,
    uint256 duration,
    uint256 interval,
    uint256 maxSlippageBps,
    uint24 poolFee
) external returns (uint256 orderId)
```

**Execute slice:**
```solidity
function executeSlice(uint256 orderId) external returns (uint256 amountOut)
```

**Cancel order:**
```solidity
function cancelOrder(uint256 orderId) external returns (uint256 refundAmount)
```

**Withdraw proceeds:**
```solidity
function withdrawProceeds(uint256 orderId) external returns (uint256 withdrawnAmount)
```

### Events

- `OrderCreated`: Emitted when a new TWAP order is created
- `SliceExecuted`: Emitted when a slice is successfully executed
- `OrderCancelled`: Emitted when an order is cancelled
- `ProceedsWithdrawn`: Emitted when proceeds are withdrawn

## Testing

**Run all tests:**
```bash
forge test
```

**Run specific test file:**
```bash
forge test --match-contract UniswapV3TWAPBotTest
```

**Run with verbose output:**
```bash
forge test -vvv
```

**Run fuzz tests:**
```bash
forge test --match-test testFuzz
```

**Generate coverage report:**
```bash
forge coverage
```

### Test Structure

- **Unit Tests**: Test individual contract functions
- **Integration Tests**: Test complete order lifecycle
- **Fuzz Tests**: Test with randomized inputs
- **Mock Contracts**: Isolated testing environment

## Network Deployment

### Supported Networks

- **Anvil (Local)**: `http://127.0.0.1:8545`
- **Sepolia Testnet**: Ethereum testnet
- **Mainnet**: Production deployment (configure RPC)

### Contract Addresses

After deployment, update your `.env` file with the deployed contract addresses:

```bash
# Example addresses (replace with your deployed contracts)
TWAP_BOT_ADDRESS=0x1234...
```

## Security Considerations

- **Reentrancy Protection**: All state-changing functions use `nonReentrant` modifier
- **Access Control**: Only order creators can cancel their orders and withdraw proceeds
- **Input Validation**: Comprehensive parameter validation on all functions
- **Safe Token Handling**: Uses OpenZeppelin's `SafeERC20` for token transfers
- **Slippage Protection**: Built-in slippage tolerance mechanisms

## Gas Optimization

- **Batch Operations**: Consider batching multiple slice executions
- **Gas Price Monitoring**: Bot monitors gas prices for optimal execution
- **Efficient Storage**: Optimized struct packing for reduced gas costs

## Monitoring and Analytics

The bot provides comprehensive logging for:
- Order creation and execution
- Gas usage tracking
- Error handling and recovery
- Performance metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is experimental and provided as-is. Users should:
- Test thoroughly before mainnet deployment
- Understand the risks of automated trading
- Ensure proper security practices
- Consider market conditions and slippage

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Review the test files for usage examples
- Check the inline documentation in the smart contracts

---

**Built with:**
- Solidity ^0.8.19
- Foundry for development and testing
- OpenZeppelin for security primitives
- Web3.py for Python integration
- Uniswap V3 for decentralized swapping