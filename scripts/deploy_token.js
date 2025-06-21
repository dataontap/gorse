
const { ethers } = require("hardhat");

async function main() {
  console.log("Setting up deployment account...");
  
  // Get the deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Account address:", deployer.address);
  
  // Check account balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");
  
  // Verify minimum balance for deployment (estimate: 0.01 ETH)
  const minBalance = ethers.parseEther("0.01");
  if (balance < minBalance) {
    console.error("❌ Insufficient balance for deployment!");
    console.error("Current balance:", ethers.formatEther(balance), "ETH");
    console.error("Minimum required:", ethers.formatEther(minBalance), "ETH");
    console.error("Please fund your account before deploying.");
    process.exit(1);
  }
  
  console.log("✅ Account setup verified. Proceeding with deployment...");
  console.log("Deploying DOTM Token with the account:", deployer.address);

  const DOTMToken = await ethers.getContractFactory("DOTMToken");
  const token = await DOTMToken.deploy();
  
  // Wait for deployment to complete
  await token.waitForDeployment();
  
  // Get the contract address
  const tokenAddress = await token.getAddress();

  console.log("DOTM Token deployed to:", tokenAddress);
  console.log("Max supply:", await token.MAX_SUPPLY());
  console.log("Current total supply:", await token.totalSupply());
  console.log("Remaining mintable tokens:", await token.remainingMintableTokens());
  console.log("New member reward amount:", await token.NEW_MEMBER_REWARD());
  console.log("Data reward percentage (basis points):", await token.dataRewardPercentage());
  
  // Verify contract on Etherscan (optional)
  console.log("Waiting for block confirmations...");
  await token.deploymentTransaction().wait(5);
  
  console.log("Contract verification can be done with:");
  console.log(`npx hardhat verify --network mainnet ${tokenAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
