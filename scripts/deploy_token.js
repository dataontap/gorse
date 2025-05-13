
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying DOTM Token with the account:", deployer.address);

  const DOTMToken = await ethers.getContractFactory("DOTMToken");
  const token = await DOTMToken.deploy();
  await token.deployed();

  console.log("DOTM Token deployed to:", token.address);
  console.log("Total supply:", await token.totalSupply());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
