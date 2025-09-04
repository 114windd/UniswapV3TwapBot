// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {IERC20} from '../lib/openzeppelin-contracts/contracts/token/ERC20/IERC20.sol';
import {SafeERC20} from '../lib/openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol';
import {ISwapRouter} from '../lib/v3-periphery/contracts/interfaces/ISwapRouter.sol';

/**
 * @title MinimalMockSwapRouter
 * @notice Minimal mock implementation of Uniswap V3 SwapRouter for Anvil testing
 * @dev Implements ISwapRouter interface with 1:1 swaps, no slippage or complex logic
 */
contract MockSwapRouter is ISwapRouter {
    using SafeERC20 for IERC20;

    // -----------------------------
    // Core swap functions
    // -----------------------------

    function exactInputSingle(
        ExactInputSingleParams calldata params
    ) external payable override returns (uint256 amountOut) {
        amountOut = params.amountIn;

        IERC20(params.tokenIn).safeTransferFrom(
            msg.sender,
            address(this),
            params.amountIn
        );
        IERC20(params.tokenOut).safeTransfer(params.recipient, amountOut);
    }

    function exactInput(
        ExactInputParams calldata params
    ) external payable override returns (uint256 amountOut) {
        amountOut = params.amountIn;

        // For simplicity, assume first 20 bytes = tokenIn, last 20 bytes = tokenOut
        address tokenIn = address(bytes20(params.path[0:20]));
        address tokenOut = address(
            bytes20(params.path[params.path.length - 20:])
        );

        IERC20(tokenIn).safeTransferFrom(
            msg.sender,
            address(this),
            params.amountIn
        );
        IERC20(tokenOut).safeTransfer(params.recipient, amountOut);
    }

    function exactOutputSingle(
        ExactOutputSingleParams calldata params
    ) external payable override returns (uint256 amountIn) {
        amountIn = params.amountOut;

        IERC20(params.tokenIn).safeTransferFrom(
            msg.sender,
            address(this),
            amountIn
        );
        IERC20(params.tokenOut).safeTransfer(
            params.recipient,
            params.amountOut
        );
    }

    function exactOutput(
        ExactOutputParams calldata params
    ) external payable override returns (uint256 amountIn) {
        amountIn = params.amountOut;

        address tokenIn = address(bytes20(params.path[0:20]));
        address tokenOut = address(
            bytes20(params.path[params.path.length - 20:])
        );

        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenOut).safeTransfer(params.recipient, params.amountOut);
    }

    // -----------------------------
    // Callback stub (required by interface)
    // -----------------------------
    function uniswapV3SwapCallback(
        int256,
        int256,
        bytes calldata
    ) external override {}
}
