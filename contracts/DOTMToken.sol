
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DOTMToken is ERC20, Ownable {
    // Initial supply of 100,000 tokens with 18 decimals
    uint256 public constant INITIAL_SUPPLY = 100000 * 10**18;
    
    // Reward percentage for data purchases (1%)
    uint256 public dataRewardPercentage = 1;
    
    constructor() ERC20("DOTM Token", "DOTM") Ownable(msg.sender) {
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    // Function to mint new tokens (only owner)
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    
    // Function to calculate and award data purchase rewards
    function rewardDataPurchase(address user, uint256 purchaseAmount) public onlyOwner {
        uint256 rewardAmount = (purchaseAmount * dataRewardPercentage) / 100;
        _mint(user, rewardAmount);
    }
    
    // Function to update reward percentage (only owner)
    function setDataRewardPercentage(uint256 newPercentage) public onlyOwner {
        require(newPercentage <= 100, "Percentage cannot exceed 100");
        dataRewardPercentage = newPercentage;
    }
    
    // Function to award new member tokens (1 DOTM per new member)
    function awardNewMember(address newMember) public onlyOwner {
        uint256 memberReward = 1 * 10**18; // 1 DOTM token
        _mint(newMember, memberReward);
    }
}
