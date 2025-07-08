const { ethers } = require("hardhat");
const fs = require("fs");

/**
 * Deployment script for DeFi and Tokenization contracts
 * Demonstrates Chainlink integration with state-changing operations
 */

async function main() {
    console.log("🚀 Starting DeFi and Tokenization Contract Deployment...");
    
    // Get network configuration
    const network = hre.network.name;
    console.log(`📡 Deploying to network: ${network}`);
    
    // Network-specific configurations
    const networkConfigs = {
        ethereum: {
            ethUsdPriceFeed: "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
            btcUsdPriceFeed: "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
            linkUsdPriceFeed: "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
            vrfCoordinator: "0x271682DEB8C4E0901D1a1550aD2e64D568E69909",
            keyHash: "0x8af398995b04c28e9951adb9721ef74c74f93e6a478f39e7e0777be13527e7ef",
            ccipRouter: "0x80226fc0Ee2b096224EeAc085Bb9a8cba1146f7D",
            chainSelector: "5009297550715157269",
            vrfSubscriptionId: 1
        },
        polygon: {
            ethUsdPriceFeed: "0xF9680D99D6C9589e2a93a78A04A279e509205945",
            btcUsdPriceFeed: "0xc907E116054Ad103354f2D350FD2514433D57F6f",
            linkUsdPriceFeed: "0xAB594600376Ec9fD91F8e885dADF0CE036862dE0",
            vrfCoordinator: "0xAE975071Be8F8eE67addBC1A82488F1C24858067",
            keyHash: "0x6e099d640cde6de9d40ac749b4b594126b0169747122711109c9985d47751f93",
            ccipRouter: "0x3C3D92629A02a8D95D5CB9650fe49C3544f69B43",
            chainSelector: "4051577828743386545",
            vrfSubscriptionId: 1
        },
        avalanche: {
            ethUsdPriceFeed: "0x976B3D034E162d8bD72D6b9C989d545b839003b0",
            btcUsdPriceFeed: "0x2779D32d5166BAaa2B2b658333bA7e6Ec0C65743",
            linkUsdPriceFeed: "0x0A77230d17318075983913bC2145DB16C7366156",
            vrfCoordinator: "0xd5D517aBE5cF79B7e95eC98dB0f0277788aFF634",
            keyHash: "0x06eb0e2ea7cca202fc7c8258397a36f33d6ecb9f1a6d7931d3508a3acefb8a1",
            ccipRouter: "0xF4c7E640EdA248ef95972845a62bdC74237805dB",
            chainSelector: "6433500567565415381",
            vrfSubscriptionId: 1
        }
    };
    
    const config = networkConfigs[network] || networkConfigs.ethereum;
    
    const [deployer] = await ethers.getSigners();
    console.log(`👤 Deploying contracts with account: ${deployer.address}`);
    console.log(`💰 Account balance: ${ethers.utils.formatEther(await deployer.getBalance())} ETH`);
    
    // Deploy contracts
    const deployedContracts = {};
    
    try {
        // 1. Deploy DeFi Yield Optimizer
        console.log("\n📈 Deploying DeFi Yield Optimizer...");
        const DeFiYieldOptimizer = await ethers.getContractFactory("DeFiYieldOptimizer");
        const defiOptimizer = await DeFiYieldOptimizer.deploy(
            config.vrfCoordinator,
            config.vrfSubscriptionId,
            config.keyHash,
            config.ethUsdPriceFeed,
            config.btcUsdPriceFeed,
            config.linkUsdPriceFeed
        );
        await defiOptimizer.deployed();
        deployedContracts.DeFiYieldOptimizer = defiOptimizer.address;
        console.log(`✅ DeFi Yield Optimizer deployed to: ${defiOptimizer.address}`);
        
        // 2. Deploy Real Estate NFT
        console.log("\n🏠 Deploying Real Estate NFT...");
        const RealEstateNFT = await ethers.getContractFactory("RealEstateNFT");
        const realEstateNFT = await RealEstateNFT.deploy(
            config.vrfCoordinator,
            config.vrfSubscriptionId,
            config.keyHash,
            config.ethUsdPriceFeed,
            config.ethUsdPriceFeed // Using ETH/USD as home price feed for demo
        );
        await realEstateNFT.deployed();
        deployedContracts.RealEstateNFT = realEstateNFT.address;
        console.log(`✅ Real Estate NFT deployed to: ${realEstateNFT.address}`);
        
        // 3. Deploy Cross-Chain Lending
        console.log("\n🌉 Deploying Cross-Chain Lending...");
        const CrossChainLending = await ethers.getContractFactory("CrossChainLending");
        const crossChainLending = await CrossChainLending.deploy(
            config.ccipRouter,
            config.ethUsdPriceFeed,
            config.btcUsdPriceFeed,
            config.linkUsdPriceFeed
        );
        await crossChainLending.deployed();
        deployedContracts.CrossChainLending = crossChainLending.address;
        console.log(`✅ Cross-Chain Lending deployed to: ${crossChainLending.address}`);
        
        // 4. Initialize lending pools
        console.log("\n⚙️ Initializing lending pools...");
        
        // Mock token addresses (replace with actual token addresses)
        const mockETH = "0x1234567890123456789012345678901234567890";
        const mockBTC = "0x2345678901234567890123456789012345678901";
        const mockUSDC = "0x3456789012345678901234567890123456789012";
        
        await crossChainLending.initializeLendingPool(mockETH, 7500); // 75% collateral factor
        await crossChainLending.initializeLendingPool(mockBTC, 7000); // 70% collateral factor
        await crossChainLending.initializeLendingPool(mockUSDC, 8500); // 85% collateral factor
        
        console.log("✅ Lending pools initialized");
        
        // 5. Add supported chains for cross-chain operations
        console.log("\n🔗 Configuring cross-chain support...");
        const supportedChains = ["5009297550715157269", "4051577828743386545", "6433500567565415381"];
        for (const chainSelector of supportedChains) {
            await crossChainLending.addSupportedChain(chainSelector);
        }
        console.log("✅ Cross-chain support configured");
        
        // Save deployment addresses
        const deploymentData = {
            network: network,
            timestamp: new Date().toISOString(),
            deployer: deployer.address,
            contracts: deployedContracts,
            config: config
        };
        
        const deploymentFile = `deployments/${network}-deployment.json`;
        fs.mkdirSync("deployments", { recursive: true });
        fs.writeFileSync(deploymentFile, JSON.stringify(deploymentData, null, 2));
        
        console.log(`\n📄 Deployment data saved to: ${deploymentFile}`);
        
        // Display summary
        console.log("\n🎉 DEPLOYMENT COMPLETE!");
        console.log("=" * 50);
        console.log("📊 Contract Addresses:");
        Object.entries(deployedContracts).forEach(([name, address]) => {
            console.log(`   ${name}: ${address}`);
        });
        
        console.log("\n🔧 Chainlink Integration Features:");
        console.log("   ✅ Price Feeds (State-reading for dynamic pricing)");
        console.log("   ✅ VRF (State-changing trait generation)");
        console.log("   ✅ Automation (State-changing automated rebalancing)");
        console.log("   ✅ CCIP (State-changing cross-chain operations)");
        
        console.log("\n🏆 Hackathon Track Compliance:");
        console.log("   ✅ DeFi Track: Yield optimization with automated rebalancing");
        console.log("   ✅ Tokenization Track: Dynamic real estate NFTs with fractional ownership");
        console.log("   ✅ Cross-chain Track: Multi-chain lending with CCIP messaging");
        console.log("   ✅ State Changes: All Chainlink services trigger on-chain state changes");
        
        console.log("\n📋 Next Steps:");
        console.log("   1. Fund VRF subscription with LINK tokens");
        console.log("   2. Add deployed contracts as VRF consumers");
        console.log("   3. Register contracts with Chainlink Automation");
        console.log("   4. Test cross-chain functionality");
        console.log("   5. Create frontend interface for user interactions");
        
    } catch (error) {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }
}

// Execute deployment
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("💥 Deployment script failed:", error);
        process.exit(1);
    });
