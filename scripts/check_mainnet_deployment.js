
const { ethers } = require("hardhat");

async function main() {
  console.log("🔍 Checking DOTM Token deployment status...");
  
  // Check if we have a deployed contract address
  const tokenAddress = process.env.TOKEN_ADDRESS;
  
  if (!tokenAddress) {
    console.log("❌ No TOKEN_ADDRESS found in environment variables");
    console.log("📝 To deploy to mainnet, run: npx hardhat run scripts/deploy_token.js --network mainnet");
    return;
  }

  console.log(`🔗 Checking contract at address: ${tokenAddress}`);

  try {
    // Connect to mainnet
    const network = await ethers.provider.getNetwork();
    console.log(`🌐 Connected to network: ${network.name} (Chain ID: ${network.chainId})`);

    if (network.chainId === 1n) {
      console.log("✅ Connected to Ethereum Mainnet");
    } else if (network.chainId === 11155111n) {
      console.log("⚠️  Connected to Sepolia Testnet");
    } else {
      console.log(`⚠️  Connected to unknown network with Chain ID: ${network.chainId}`);
    }

    // Get contract instance
    const DOTMToken = await ethers.getContractFactory("DOTMToken");
    const token = DOTMToken.attach(tokenAddress);

    // Check if contract exists and get basic info
    const name = await token.name();
    const symbol = await token.symbol();
    const totalSupply = await token.totalSupply();
    const maxSupply = await token.MAX_SUPPLY();
    const owner = await token.owner();

    console.log("\n📊 DOTM Token Contract Information:");
    console.log(`   Name: ${name}`);
    console.log(`   Symbol: ${symbol}`);
    console.log(`   Total Supply: ${ethers.formatEther(totalSupply)} DOTM`);
    console.log(`   Max Supply: ${ethers.formatEther(maxSupply)} DOTM`);
    console.log(`   Owner: ${owner}`);
    console.log(`   Contract Address: ${tokenAddress}`);

    if (network.chainId === 1n) {
      console.log("\n🎉 DOTM Token is LIVE on Ethereum Mainnet!");
      console.log(`🔗 View on Etherscan: https://etherscan.io/token/${tokenAddress}`);
    } else {
      console.log("\n📝 DOTM Token is deployed on testnet. To deploy to mainnet:");
      console.log("   1. Ensure you have sufficient ETH for gas fees");
      console.log("   2. Run: npx hardhat run scripts/deploy_token.js --network mainnet");
    }

  } catch (error) {
    console.error("❌ Error checking deployment:", error.message);
    
    if (error.code === 'CALL_EXCEPTION') {
      console.log("💡 Contract not found at this address or network mismatch");
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
