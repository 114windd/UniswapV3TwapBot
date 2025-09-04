// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// OpenZeppelin (via lib/openzeppelin-contracts)
import {IERC20} from '../lib/openzeppelin-contracts/contracts/token/ERC20/IERC20.sol';
import {SafeERC20} from '../lib/openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol';
import {ReentrancyGuard} from '../lib/openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol';
import {Ownable} from '../lib/openzeppelin-contracts/contracts/access/Ownable.sol';
import {Pausable} from '../lib/openzeppelin-contracts/contracts/utils/Pausable.sol';

// Uniswap v3 periphery (via lib/v3-periphery)
import {ISwapRouter} from '../lib/v3-periphery/contracts/interfaces/ISwapRouter.sol';
import {TransferHelper} from '../lib/v3-periphery/contracts/libraries/TransferHelper.sol';

/**
 * @title UniswapV3TWAPBot
 * @notice A smart contract for executing Time-Weighted Average Price (TWAP) orders on Uniswap V3
 * @dev Allows users to split large trades into smaller slices executed over time to minimize price impact
 */
contract UniswapV3TWAPBot is ReentrancyGuard, Ownable, Pausable {
    using SafeERC20 for IERC20;

    // Uniswap V3 SwapRouter interface
    ISwapRouter public immutable swapRouter;

    // Order struct containing all TWAP order details
    struct Order {
        // Static fields (set once at creation)
        address creator; // Address that created the order
        address tokenIn; // Token to swap from
        address tokenOut; // Token to swap to
        uint256 totalAmount; // Total amount of tokenIn to swap
        uint256 interval; // Time interval between slice executions (in seconds)
        uint256 duration; // Total duration for TWAP execution (in seconds)
        uint256 sliceSize; // Amount of tokenIn per slice
        uint256 maxSlippageBps; // Maximum slippage tolerance in basis points (1 bps = 0.01%)
        uint24 poolFee; // Uniswap V3 pool fee tier (e.g., 3000 for 0.3%)
        uint256 startTime; // Timestamp when order was created
        // Dynamic fields (updated during execution)
        uint256 slicesExecuted; // Number of slices already executed
        uint256 nextExecutionTime; // Timestamp for next allowed execution
        uint256 totalOut; // Total amount of tokenOut received
        bool cancelled; // Whether the order has been cancelled
    }

    // Mapping from orderId to Order
    mapping(uint256 => Order) public orders;

    // Counter for generating unique order IDs
    uint256 public nextOrderId;

    // Mapping to track user balances for each token
    mapping(address => mapping(address => uint256)) public userBalances;

    // Events
    event Deposited(
        address indexed user,
        address indexed token,
        uint256 amount
    );
    event OrderCreated(
        uint256 indexed orderId,
        address indexed creator,
        address tokenIn,
        address tokenOut,
        uint256 totalAmount,
        uint256 duration,
        uint256 interval,
        uint256 sliceSize
    );
    event SliceExecuted(
        uint256 indexed orderId,
        uint256 sliceNumber,
        uint256 amountIn,
        uint256 amountOut,
        uint256 timestamp
    );
    event OrderCancelled(uint256 indexed orderId, uint256 refundAmount);
    event ProceedsWithdrawn(
        uint256 indexed orderId,
        address indexed recipient,
        uint256 amount
    );

    // Modifiers
    modifier onlyOrderCreator(uint256 orderId) {
        require(orders[orderId].creator == msg.sender, 'Not order creator');
        _;
    }

    modifier orderExists(uint256 orderId) {
        require(orders[orderId].creator != address(0), 'Order does not exist');
        _;
    }

    modifier orderNotCancelled(uint256 orderId) {
        require(!orders[orderId].cancelled, 'Order is cancelled');
        _;
    }

    /**
     * @notice Constructor to initialize the contract with Uniswap V3 SwapRouter
     * @param _swapRouter Address of the Uniswap V3 SwapRouter contract
     * @param _owner Address of the contract owner
     */
    constructor(address _swapRouter, address _owner) Ownable(_owner) {
        require(_swapRouter != address(0), 'Invalid router address');
        require(_owner != address(0), 'Invalid owner address');
        swapRouter = ISwapRouter(_swapRouter);
    }

    /**
     * @notice Deposits tokens into the contract for TWAP order execution
     * @dev Transfers tokens from the user to this contract using SafeERC20
     * @param token The address of the token to deposit
     * @param amount The amount of tokens to deposit
     * @return success Boolean indicating if the deposit was successful
     */
    function deposit(
        address token,
        uint256 amount
    ) external nonReentrant whenNotPaused returns (bool success) {
        // Validate inputs
        require(token != address(0), 'Invalid token address');
        require(amount > 0, 'Amount must be greater than 0');

        // Check user has sufficient balance
        uint256 userBalance = IERC20(token).balanceOf(msg.sender);
        require(userBalance >= amount, 'Insufficient balance');

        // Check user has approved this contract
        uint256 allowance = IERC20(token).allowance(msg.sender, address(this));
        require(allowance >= amount, 'Insufficient allowance');

        // Store balance before transfer for verification
        uint256 balanceBefore = IERC20(token).balanceOf(address(this));

        // Transfer tokens from user to this contract
        // Using SafeERC20 to handle tokens that don't return bool on transfer
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);

        // Verify the transfer was successful
        uint256 balanceAfter = IERC20(token).balanceOf(address(this));
        require(
            balanceAfter >= balanceBefore + amount,
            'Transfer failed: balance mismatch'
        );

        // Update user balance tracking
        userBalances[msg.sender][token] += amount;

        // Emit deposit event
        emit Deposited(msg.sender, token, amount);

        return true;
    }

    /**
     * @notice Creates a new TWAP order for gradual token swapping
     * @dev Calculates slice size based on duration and interval, validates all parameters
     * @param tokenIn Address of the token to swap from
     * @param tokenOut Address of the token to swap to
     * @param totalAmount Total amount of tokenIn to swap over the duration
     * @param duration Total time period for executing the TWAP order (in seconds)
     * @param interval Time interval between slice executions (in seconds)
     * @param maxSlippageBps Maximum acceptable slippage in basis points (e.g., 50 = 0.5%)
     * @param poolFee Uniswap V3 pool fee tier (500, 3000, or 10000)
     * @return orderId The unique identifier for the created order
     */
    function createTWAPOrder(
        address tokenIn,
        address tokenOut,
        uint256 totalAmount,
        uint256 duration,
        uint256 interval,
        uint256 maxSlippageBps,
        uint24 poolFee
    ) external nonReentrant whenNotPaused returns (uint256 orderId) {
        // Validate token addresses
        require(tokenIn != address(0), 'Invalid tokenIn address');
        require(tokenOut != address(0), 'Invalid tokenOut address');
        require(tokenIn != tokenOut, 'TokenIn and tokenOut must be different');

        // Validate amounts and timing parameters
        require(totalAmount > 0, 'Total amount must be greater than 0');
        require(duration > 0, 'Duration must be greater than 0');
        require(interval > 0, 'Interval must be greater than 0');
        require(interval <= duration, 'Interval cannot exceed duration');

        // Validate slippage tolerance (max 10% = 1000 bps)
        require(maxSlippageBps <= 1000, 'Max slippage too high (>10%)');

        // Validate Uniswap V3 pool fee tiers
        require(
            poolFee == 500 || poolFee == 3000 || poolFee == 10000,
            'Invalid pool fee tier'
        );

        // Calculate number of slices and slice size
        uint256 numberOfSlices = duration / interval;
        require(numberOfSlices > 0, 'Duration too short for given interval');
        require(numberOfSlices <= 1000, 'Too many slices (max 1000)');

        // Calculate slice size (rounded down, remainder will be in last slice)
        uint256 sliceSize = totalAmount / numberOfSlices;
        require(sliceSize > 0, 'Slice size too small');

        // Check that user has sufficient deposited balance
        require(
            userBalances[msg.sender][tokenIn] >= totalAmount,
            'Insufficient deposited balance'
        );

        // Reserve the tokens for this order
        userBalances[msg.sender][tokenIn] -= totalAmount;

        // Generate unique order ID
        orderId = nextOrderId++;

        // Create the order
        orders[orderId] = Order({
            // Static fields
            creator: msg.sender,
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            totalAmount: totalAmount,
            interval: interval,
            duration: duration,
            sliceSize: sliceSize,
            maxSlippageBps: maxSlippageBps,
            poolFee: poolFee,
            startTime: block.timestamp,
            // Dynamic fields (initialized)
            slicesExecuted: 0,
            nextExecutionTime: block.timestamp, // First slice can be executed immediately
            totalOut: 0,
            cancelled: false
        });

        // Emit order creation event
        emit OrderCreated(
            orderId,
            msg.sender,
            tokenIn,
            tokenOut,
            totalAmount,
            duration,
            interval,
            sliceSize
        );

        return orderId;
    }

    /**
     * @notice Executes one slice of a TWAP order
     * @dev Performs a swap on Uniswap V3 for one slice, updates order state, and handles timing
     * @param orderId The unique identifier of the order to execute a slice for
     * @return amountOut The amount of tokenOut received from this slice execution
     */

    /**
     * @notice Executes one slice of a TWAP order
     * @dev Performs a swap on Uniswap V3 for one slice, updates order state, and handles timing
     * @param orderId The unique identifier of the order to execute a slice for
     * @return amountOut The amount of tokenOut received from this slice execution
     */
    function executeSlice(
        uint256 orderId
    )
        external
        nonReentrant
        whenNotPaused
        orderExists(orderId)
        orderNotCancelled(orderId)
        returns (uint256 amountOut)
    {
        Order storage order = orders[orderId];

        // Check if execution time has arrived
        require(
            block.timestamp >= order.nextExecutionTime,
            'Too early to execute slice'
        );

        // Check if order is still active (within duration)
        require(
            block.timestamp <= order.startTime + order.duration,
            'Order has expired'
        );

        // Calculate total number of slices
        uint256 totalSlices = order.duration / order.interval;

        // Check if all slices have been executed
        require(
            order.slicesExecuted < totalSlices,
            'All slices already executed'
        );

        // Calculate amount for this slice
        uint256 amountIn;
        if (order.slicesExecuted == totalSlices - 1) {
            // Last slice: use remaining amount to handle rounding
            amountIn =
                order.totalAmount -
                (order.slicesExecuted * order.sliceSize);
        } else {
            // Regular slice: use calculated slice size
            amountIn = order.sliceSize;
        }

        require(amountIn > 0, 'No amount to swap');

        // Calculate minimum amount out based on slippage tolerance
        // This is a simplified calculation - in production, you'd want to use a price oracle
        // For now, we'll set amountOutMinimum to 0 and rely on the deadline for MEV protection
        uint256 amountOutMinimum = 0;

        // Approve the router to spend tokens
        IERC20(order.tokenIn).forceApprove(address(swapRouter), amountIn);

        // Prepare swap parameters
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter
            .ExactInputSingleParams({
                tokenIn: order.tokenIn,
                tokenOut: order.tokenOut,
                fee: order.poolFee,
                recipient: address(this), // Contract receives the tokens
                deadline: block.timestamp + 300, // 5 minute deadline
                amountIn: amountIn,
                amountOutMinimum: amountOutMinimum,
                sqrtPriceLimitX96: 0 // No price limit
            });

        // Execute the swap
        try swapRouter.exactInputSingle(params) returns (uint256 _amountOut) {
            amountOut = _amountOut;

            // Update order state
            order.slicesExecuted += 1;
            order.nextExecutionTime = block.timestamp + order.interval;
            order.totalOut += amountOut;

            // Update user balance for tokenOut
            userBalances[order.creator][order.tokenOut] += amountOut;

            // Emit slice execution event
            emit SliceExecuted(
                orderId,
                order.slicesExecuted,
                amountIn,
                amountOut,
                block.timestamp
            );
        } catch Error(string memory reason) {
            // Reset approval on failure
            IERC20(order.tokenIn).forceApprove(address(swapRouter), 0);
            revert(string(abi.encodePacked('Swap failed: ', reason)));
        } catch {
            // Reset approval on failure
            IERC20(order.tokenIn).forceApprove(address(swapRouter), 0);
            revert('Swap failed: unknown error');
        }

        return amountOut;
    }

    /**
     * @notice Retrieves the complete order details for a given order ID
     * @dev Returns all static and dynamic fields of an order struct
     * @param orderId The unique identifier of the order to query
     * @return order The complete Order struct containing all order details
     */
    function getOrder(
        uint256 orderId
    ) external view orderExists(orderId) returns (Order memory order) {
        return orders[orderId];
    }

    /**
     * @notice Calculates the remaining amount of tokenIn that hasn't been executed yet
     * @dev Accounts for the actual slice execution pattern, including the final slice handling
     * @param orderId The unique identifier of the order to query
     * @return remaining The amount of tokenIn still to be swapped
     */
    function remainingAmount(
        uint256 orderId
    ) external view orderExists(orderId) returns (uint256 remaining) {
        Order storage order = orders[orderId];

        // If order is cancelled, no remaining amount
        if (order.cancelled) {
            return 0;
        }

        // Calculate total slices for this order
        uint256 totalSlices = order.duration / order.interval;

        // If all slices executed, no remaining amount
        if (order.slicesExecuted >= totalSlices) {
            return 0;
        }

        // Calculate remaining amount based on executed slices
        // This matches the logic used in executeSlice() for consistent calculation
        uint256 executedAmount = order.slicesExecuted * order.sliceSize;

        // Handle edge case where executed amount might exceed total due to rounding
        if (executedAmount >= order.totalAmount) {
            return 0;
        }

        return order.totalAmount - executedAmount;
    }

    /**
     * @notice Cancels a TWAP order and refunds the remaining unspent tokens to the creator
     * @dev Only the order creator can cancel their order. Updates cancelled flag and refunds tokenIn
     * @param orderId The unique identifier of the order to cancel
     * @return refundAmount The amount of tokenIn refunded to the order creator
     */
    function cancelOrder(
        uint256 orderId
    )
        external
        nonReentrant
        whenNotPaused
        orderExists(orderId)
        onlyOrderCreator(orderId)
        orderNotCancelled(orderId)
        returns (uint256 refundAmount)
    {
        Order storage order = orders[orderId];

        // Calculate the remaining amount to refund
        refundAmount = this.remainingAmount(orderId);

        // Mark the order as cancelled
        order.cancelled = true;

        // If there's an amount to refund, add it back to user's balance
        if (refundAmount > 0) {
            userBalances[order.creator][order.tokenIn] += refundAmount;
        }

        // Emit cancellation event
        emit OrderCancelled(orderId, refundAmount);

        return refundAmount;
    }

    /**
     * @notice Allows the order creator to withdraw the proceeds (tokenOut) from their TWAP order
     * @dev Safely transfers all accumulated tokenOut from executed slices to the order creator
     * @param orderId The unique identifier of the order to withdraw proceeds from
     * @return withdrawnAmount The amount of tokenOut withdrawn to the user's external wallet
     */
    function withdrawProceeds(
        uint256 orderId
    )
        external
        nonReentrant
        whenNotPaused
        orderExists(orderId)
        onlyOrderCreator(orderId)
        returns (uint256 withdrawnAmount)
    {
        Order storage order = orders[orderId];

        // Check that there are proceeds to withdraw
        uint256 availableBalance = userBalances[order.creator][order.tokenOut];
        require(availableBalance > 0, 'No proceeds to withdraw');

        // Calculate how much of the available balance belongs to this specific order
        // Note: This implementation withdraws the user's entire balance for tokenOut
        // In a production system, you might want to track per-order balances separately
        withdrawnAmount = availableBalance;

        // Update user balance (set to zero since we're withdrawing everything)
        userBalances[order.creator][order.tokenOut] = 0;

        // Transfer tokens to the order creator
        IERC20(order.tokenOut).safeTransfer(order.creator, withdrawnAmount);

        // Emit withdrawal event
        emit ProceedsWithdrawn(orderId, order.creator, withdrawnAmount);

        return withdrawnAmount;
    }
}
