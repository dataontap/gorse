
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DOTMToken is ERC20, Ownable {
    // Maximum supply of 10,333,333 tokens with 18 decimals
    uint256 public constant MAX_SUPPLY = 10333333 * 10**18;
    
    // Reward percentage for data purchases (10.33%)
    uint256 public dataRewardPercentage = 1033; // 10.33% represented as 1033 basis points
    
    // New member reward amount ($10.33 CAD worth of tokens)
    uint256 public constant NEW_MEMBER_REWARD = 1033 * 10**16; // 10.33 DOTM tokens
    
    constructor() ERC20("DOTM Token", "DOTM") Ownable(msg.sender) {
        // No initial mint, tokens are minted as needed
    }
    
    // Function to mint new tokens (only owner) with max supply check
    function mint(address to, uint256 amount) public onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Minting would exceed max supply");
        _mint(to, amount);
    }
    
    // Function to calculate and award data purchase rewards (10.33%)
    function rewardDataPurchase(address user, uint256 purchaseAmountCents) public onlyOwner {
        require(totalSupply() < MAX_SUPPLY, "Max supply reached");
        
        // Calculate 10.33% reward: purchaseAmountCents * 1033 / 10000
        uint256 rewardAmount = (purchaseAmountCents * dataRewardPercentage) / 10000;
        
        // Ensure we don't exceed max supply
        if (totalSupply() + rewardAmount > MAX_SUPPLY) {
            rewardAmount = MAX_SUPPLY - totalSupply();
        }
        
        if (rewardAmount > 0) {
            _mint(user, rewardAmount);
        }
    }
    
    // Function to update reward percentage (only owner)
    function setDataRewardPercentage(uint256 newPercentageBasisPoints) public onlyOwner {
        require(newPercentageBasisPoints <= 10000, "Percentage cannot exceed 100%");
        dataRewardPercentage = newPercentageBasisPoints;
    }
    
    // Function to award new member tokens (10.33 DOTM per new member)
    function awardNewMember(address newMember) public onlyOwner {
        require(totalSupply() + NEW_MEMBER_REWARD <= MAX_SUPPLY, "Not enough tokens left for new member");
        _mint(newMember, NEW_MEMBER_REWARD);
    }
    
    // Function to check remaining mintable tokens
    function remainingMintableTokens() public view returns (uint256) {
        return MAX_SUPPLY - totalSupply();
    }
}
