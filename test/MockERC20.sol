// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {ERC20} from '../lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol';

/**
 * @title MockERC20
 * @notice Mock ERC20 token for testing purposes on Anvil
 * @dev Extends OpenZeppelin's ERC20 implementation with public mint function
 */
contract MockERC20 is ERC20 {
    uint8 private _decimals;

    /**
     * @notice Constructor to create a mock ERC20 token
     * @param name The name of the token (e.g., "Mock USDC")
     * @param symbol The symbol of the token (e.g., "mUSDC")
     * @param decimals_ The number of decimals for the token (e.g., 6 for USDC, 18 for WETH)
     * @param initialSupply The initial supply to mint to the deployer
     */
    constructor(
        string memory name,
        string memory symbol,
        uint8 decimals_,
        uint256 initialSupply
    ) ERC20(name, symbol) {
        _decimals = decimals_;

        // Mint initial supply to the contract deployer
        if (initialSupply > 0) {
            _mint(msg.sender, initialSupply);
        }
    }

    /**
     * @notice Override decimals to return custom decimal places
     * @return The number of decimals for this token
     */
    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    /**
     * @notice Mint tokens to a specific address (for testing purposes)
     * @dev Public function to allow easy token creation during testing
     * @param to The address to mint tokens to
     * @param amount The amount of tokens to mint
     */
    function mint(address to, uint256 amount) public {
        require(to != address(0), 'Cannot mint to zero address');
        require(amount > 0, 'Amount must be greater than zero');
        _mint(to, amount);
    }

    /**
     * @notice Mint tokens to multiple addresses at once (batch mint)
     * @dev Useful for setting up multiple test accounts with tokens
     * @param recipients Array of addresses to mint tokens to
     * @param amounts Array of amounts to mint to each recipient
     */
    function batchMint(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) public {
        require(recipients.length == amounts.length, 'Arrays length mismatch');
        require(recipients.length > 0, 'Empty arrays');

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), 'Cannot mint to zero address');
            require(amounts[i] > 0, 'Amount must be greater than zero');
            _mint(recipients[i], amounts[i]);
        }
    }

    /**
     * @notice Burn tokens from caller's balance
     * @dev Useful for testing scenarios where tokens are burned
     * @param amount The amount of tokens to burn
     */
    function burn(uint256 amount) public {
        require(amount > 0, 'Amount must be greater than zero');
        require(
            balanceOf(msg.sender) >= amount,
            'Insufficient balance to burn'
        );
        _burn(msg.sender, amount);
    }

    /**
     * @notice Get token information in a single call
     * @dev Convenience function for testing and debugging
     * @return tokenName The name of the token
     * @return tokenSymbol The symbol of the token
     * @return tokenDecimals The decimals of the token
     * @return tokenTotalSupply The total supply of the token
     */
    function getTokenInfo()
        external
        view
        returns (
            string memory tokenName,
            string memory tokenSymbol,
            uint8 tokenDecimals,
            uint256 tokenTotalSupply
        )
    {
        return (name(), symbol(), decimals(), totalSupply());
    }
}
