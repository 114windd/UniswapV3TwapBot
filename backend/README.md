You are an expert Python developer with deep knowledge of blockchain and Ethereum development using web3.py. I want you to implement the off-chain backend for a Uniswap V3 TWAP bot. This backend must:

connect_to_chain() - Connect_to_chain(rpc_url: str) -> Web3 – connects to an Ethereum node.
load_contract() - needed to interact with your smart contract
load_wallet() - needed to sign transactions
execute_slice() - the main purpose of your bot
get_order() - needed to check order status
listen_for_orders() - to detect new orders automatically

Requirements for each function implementation:

- Use proper web3.py calls to interact with smart contracts and ERC20 tokens. 
- Handle events asynchronously and reliably. 
- Include logging for monitoring each operation (order creation, slice execution, withdrawals, cancellations). 
- Ensure safety: check 
  - allowances, 
  - confirm transactions, 
  - handle errors,
  -  prevent double execution of slices. 
- Keep code modular, well-structured, and documented. 

Documentation

Refer to web3.py documentation for contract interaction and event listening. Refer to Uniswap V3 documentation for understanding TWAP mechanics: https://docs.uniswap.org/contracts/v3/overview  Let me know if you need any additional information. I am aware this is a simplified implementation however only implement the functions mentioned. I have pasted the smart contract code. 

here is what the project layout should look like:twap_bot/ ├── twap_bot.py # Main bot class with all functionality ├── config.py # Simple configuration ├── UniswapV3TWAPBot.json # Contract ABI (your file) ├── requirements.txt ├── .env.example └── README.md

Do not continue without my permission. Implement each function one at a time. Once you are done implementing each function , wait for my confirmation before continuing 