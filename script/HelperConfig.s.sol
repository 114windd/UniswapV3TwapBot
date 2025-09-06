// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script, console} from 'forge-std/Script.sol';
import {UniswapV3TWAPBot} from '../src/UniSwapV3TWAPBot.sol';
import {MockSwapRouter} from '../test/MockSwapRouter.sol';
import {MockERC20} from '../test/MockERC20.sol';

/**
 * @title HelperConfig
 * @notice Helper configuration contract for UniswapV3TWAPBot deployment
 * @dev Contains constants, mock contract deployment, and helper functions
 */
contract HelperConfig is Script {
    // Uniswap V3 SwapRouter addresses
    // Reference: https://docs.uniswap.org/contracts/v3/reference/deployments/
    address public constant MAINNET_SWAP_ROUTER =
        0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address public constant SEPOLIA_SWAP_ROUTER =
        0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E;

    // Chain IDs
    uint256 public constant ETHEREUM_MAINNET_CHAIN_ID = 1;
    uint256 public constant SEPOLIA_TESTNET_CHAIN_ID = 11155111;
    uint256 public constant ANVIL_CHAIN_ID = 31337;

    // Mock Contract instances (public for sharing state)
    MockSwapRouter public mockSwapRouter;
    MockERC20 public mockUSDC;
    MockERC20 public mockWETH;
    MockERC20 public mockDAI;

    // Anvil SwapRouter address (set after mock deployment)
    address public anvilSwapRouter;

    /**
     * @notice Get the appropriate SwapRouter address based on chain ID
     * @return swapRouter The SwapRouter address for the current chain
     */
    function getSwapRouterAddress() public view returns (address swapRouter) {
        uint256 chainId = block.chainid;

        if (chainId == ETHEREUM_MAINNET_CHAIN_ID) {
            // Ethereum Mainnet
            swapRouter = MAINNET_SWAP_ROUTER;
        } else if (chainId == SEPOLIA_TESTNET_CHAIN_ID) {
            // Sepolia Testnet
            swapRouter = SEPOLIA_SWAP_ROUTER;
        } else if (chainId == ANVIL_CHAIN_ID) {
            // Anvil (local) - use deployed MockSwapRouter address
            swapRouter = anvilSwapRouter;
        } else {
            revert('Unsupported chain ID');
        }
    }

    /**
     * @notice Deploy mock contracts for Anvil testing
     * @dev Deploys MockSwapRouter and MockERC20 tokens, then funds the router
     * @param deployerPrivateKey The private key for deployment
     */
    function deployMockContractsForAnvil(uint256 deployerPrivateKey) public {
        console.log('Deploying mock contracts for Anvil...');

        vm.startBroadcast(deployerPrivateKey);

        // Deploy Mock ERC20 tokens
        mockUSDC = new MockERC20('Mock USDC', 'mUSDC', 6, 10_000_000 * 10 ** 6);
        mockWETH = new MockERC20('Mock WETH', 'mWETH', 18, 1_000 * 10 ** 18);
        mockDAI = new MockERC20('Mock DAI', 'mDAI', 18, 10_000_000 * 10 ** 18);

        console.log('Mock USDC deployed:', address(mockUSDC));
        console.log('Mock WETH deployed:', address(mockWETH));
        console.log('Mock DAI deployed:', address(mockDAI));

        // Deploy MockSwapRouter
        mockSwapRouter = new MockSwapRouter();
        anvilSwapRouter = address(mockSwapRouter);
        console.log('MockSwapRouter deployed:', anvilSwapRouter);
        vm.stopBroadcast();
    }

    /**
     * @notice Verify the deployment was successful
     * @dev Performs basic checks on the deployed contract
     * @param twapBot The deployed TWAP Bot contract
     * @param expectedOwner The expected owner address
     */
    function verifyDeployment(
        UniswapV3TWAPBot twapBot,
        address expectedOwner
    ) public view {
        require(
            address(twapBot) != address(0),
            'Deployment failed: zero address'
        );

        // Check that the SwapRouter was set correctly
        address deployedRouter = address(twapBot.swapRouter());
        address expectedRouter = getSwapRouterAddress();
        require(
            deployedRouter == expectedRouter,
            'SwapRouter address mismatch'
        );

        // Check owner was set correctly
        address actualOwner = twapBot.owner();
        require(actualOwner == expectedOwner, 'Owner address mismatch');

        // Check initial state
        require(twapBot.nextOrderId() == 0, 'Initial order ID should be 0');
        require(!twapBot.paused(), 'Contract should not be paused initially');

        console.log('Deployment verification passed!');
    }

    /**
     * @notice Check if current chain is Anvil
     * @return True if running on Anvil (chain ID 31337)
     */
    function isAnvil() public view returns (bool) {
        return block.chainid == ANVIL_CHAIN_ID;
    }

    /**
     * @notice Get network name based on chain ID
     * @return networkName The name of the current network
     */
    function getNetworkName() public view returns (string memory networkName) {
        uint256 chainId = block.chainid;

        if (chainId == ETHEREUM_MAINNET_CHAIN_ID) {
            networkName = 'Ethereum Mainnet';
        } else if (chainId == SEPOLIA_TESTNET_CHAIN_ID) {
            networkName = 'Sepolia Testnet';
        } else if (chainId == ANVIL_CHAIN_ID) {
            networkName = 'Anvil (Local)';
        } else {
            networkName = 'Unknown Network';
        }
    }
}
