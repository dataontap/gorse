
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const PRIVATE_KEY = process.env.PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000000";
// Using a public RPC endpoint as fallback if environment variable is not set
const GOERLI_URL = process.env.GOERLI_URL || "https://ethereum-goerli-rpc.publicnode.com";
const ETHEREUM_API_KEY = process.env.ETHEREUM_API_KEY || "";

module.exports = {
  solidity: "0.8.20",
  networks: {
    hardhat: {},
    goerli: {
      url: GOERLI_URL,
      accounts: [PRIVATE_KEY]
    },
    mainnet: {
      url: `https://eth-mainnet.g.alchemy.com/v2/${ETHEREUM_API_KEY}`,
      accounts: [PRIVATE_KEY]
    }
  },
  etherscan: {
    apiKey: ETHEREUM_API_KEY
  }
};
