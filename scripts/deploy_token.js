
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying DOTM Token with the account:", deployer.address);

  const DOTMToken = await ethers.getContractFactory("DOTMToken");
  const token = await DOTMToken.deploy();
  
  // Wait for deployment to complete
  await token.waitForDeployment();
  
  // Get the contract address
  const tokenAddress = await token.getAddress();

  console.log("DOTM Token deployed to:", tokenAddress);
  console.log("Total supply:", await token.totalSupply());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
