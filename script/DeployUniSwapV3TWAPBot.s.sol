// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script, console} from 'forge-std/Script.sol';
import {UniswapV3TWAPBot} from '../src/UniSwapV3TWAPBot.sol';
import {HelperConfig} from './HelperConfig.s.sol';

/**
 * @title Deploy Script for UniswapV3TWAPBot
 * @notice Deploys the TWAP Bot contract to Anvil (local) and Sepolia (testnet)
 * @dev Uses environment variables for configuration and private keys
 */
contract DeployUniSwapV3TWAPBOT is Script {
    HelperConfig public helperConfig;
    UniswapV3TWAPBot public twapBot;

    function setUp() public {
        helperConfig = new HelperConfig();
    }

    /**
     * @notice Main deployment function
     * @dev Detects the network and deploys with appropriate parameters
     */
    function run() public {
        // Load environment variables
        uint256 deployerPrivateKey = vm.envUint('PRIVATE_KEY');
        address owner = vm.addr(deployerPrivateKey);

        console.log('Deploying UniswapV3TWAPBot...');
        console.log('Deployer address:', owner);
        console.log('Chain ID:', block.chainid);
        console.log('Network:', helperConfig.getNetworkName());

        // Deploy mock contracts if on Anvil
        if (helperConfig.isAnvil()) {
            helperConfig.deployMockContractsForAnvil(deployerPrivateKey);
        }

        // Get the appropriate SwapRouter address
        address swapRouter = helperConfig.getSwapRouterAddress();
        console.log('SwapRouter address:', swapRouter);

        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);

        // Deploy the TWAP Bot contract
        twapBot = new UniswapV3TWAPBot(swapRouter, owner);

        vm.stopBroadcast();

        // Log deployment details
        console.log('UniswapV3TWAPBot deployed to:', address(twapBot));
        console.log('Owner:', owner);
        console.log('SwapRouter:', swapRouter);

        // Verify deployment
        helperConfig.verifyDeployment(twapBot, owner);
    }
}
