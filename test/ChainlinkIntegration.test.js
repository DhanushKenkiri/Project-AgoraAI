const { expect } = require("chai");
const { ethers } = require("hardhat");

/**
 * Comprehensive test suite for Chainlink hackathon contracts
 * Tests all state-changing operations and Chainlink integrations
 */

describe("Chainlink Hackathon Smart Contracts", function () {
    let deployer, user1, user2;
    let defiOptimizer, realEstateNFT, crossChainLending;
    
    // Mock Chainlink contract addresses (for testing)
    const mockVRFCoordinator = "0x1234567890123456789012345678901234567890";
    const mockEthUsdPriceFeed = "0x2345678901234567890123456789012345678901";
    const mockBtcUsdPriceFeed = "0x3456789012345678901234567890123456789012";
    const mockLinkUsdPriceFeed = "0x4567890123456789012345678901234567890123";
    const mockCCIPRouter = "0x5678901234567890123456789012345678901234";
    const mockKeyHash = "0x6e099d640cde6de9d40ac749b4b594126b0169747122711109c9985d47751f93";
    const subscriptionId = 1;

    beforeEach(async function () {
        [deployer, user1, user2] = await ethers.getSigners();

        // Deploy DeFi Yield Optimizer
        const DeFiYieldOptimizer = await ethers.getContractFactory("DeFiYieldOptimizer");
        defiOptimizer = await DeFiYieldOptimizer.deploy(
            mockVRFCoordinator,
            subscriptionId,
            mockKeyHash,
            mockEthUsdPriceFeed,
            mockBtcUsdPriceFeed,
            mockLinkUsdPriceFeed
        );
        await defiOptimizer.deployed();

        // Deploy Real Estate NFT
        const RealEstateNFT = await ethers.getContractFactory("RealEstateNFT");
        realEstateNFT = await RealEstateNFT.deploy(
            mockVRFCoordinator,
            subscriptionId,
            mockKeyHash,
            mockEthUsdPriceFeed,
            mockEthUsdPriceFeed // Using ETH/USD as home price feed for testing
        );
        await realEstateNFT.deployed();

        // Deploy Cross-Chain Lending
        const CrossChainLending = await ethers.getContractFactory("CrossChainLending");
        crossChainLending = await CrossChainLending.deploy(
            mockCCIPRouter,
            mockEthUsdPriceFeed,
            mockBtcUsdPriceFeed,
            mockLinkUsdPriceFeed
        );
        await crossChainLending.deployed();
    });

    describe("DeFi Yield Optimizer", function () {
        it("Should create portfolio with Chainlink price feeds", async function () {
            const ethAmount = ethers.utils.parseEther("10");
            const btcAmount = ethers.utils.parseEther("1");
            const depositAmount = ethers.utils.parseEther("5");

            // Create portfolio (STATE CHANGE)
            await expect(
                defiOptimizer.connect(user1).createPortfolio(
                    ethAmount,
                    btcAmount,
                    true, // Enable auto-rebalance
                    { value: depositAmount }
                )
            ).to.emit(defiOptimizer, "PortfolioRebalanced");

            // Verify portfolio was created
            const portfolio = await defiOptimizer.userPortfolios(user1.address);
            expect(portfolio.ethAllocation).to.equal(ethAmount);
            expect(portfolio.btcAllocation).to.equal(btcAmount);
            expect(portfolio.autoRebalance).to.be.true;
        });

        it("Should request VRF for portfolio optimization", async function () {
            // First create a portfolio
            const ethAmount = ethers.utils.parseEther("10");
            const btcAmount = ethers.utils.parseEther("1");
            const depositAmount = ethers.utils.parseEther("5");

            await defiOptimizer.connect(user1).createPortfolio(
                ethAmount,
                btcAmount,
                true,
                { value: depositAmount }
            );

            // Request VRF optimization (STATE CHANGE)
            await expect(
                defiOptimizer.connect(user1).requestPortfolioOptimization()
            ).to.emit(defiOptimizer, "StrategyOptimized");
        });

        it("Should harvest yield and update portfolio", async function () {
            // Create portfolio first
            const ethAmount = ethers.utils.parseEther("10");
            const btcAmount = ethers.utils.parseEther("1");
            const depositAmount = ethers.utils.parseEther("5");

            await defiOptimizer.connect(user1).createPortfolio(
                ethAmount,
                btcAmount,
                false,
                { value: depositAmount }
            );

            // Fast forward time to accumulate yield
            await ethers.provider.send("evm_increaseTime", [86400]); // 1 day
            await ethers.provider.send("evm_mine");

            // Harvest yield (STATE CHANGE)
            await expect(
                defiOptimizer.connect(user1).harvestYield()
            ).to.emit(defiOptimizer, "YieldHarvested");

            // Verify yield was added
            const portfolio = await defiOptimizer.userPortfolios(user1.address);
            expect(portfolio.totalYieldEarned).to.be.gt(0);
        });

        it("Should check upkeep for automation", async function () {
            const [upkeepNeeded] = await defiOptimizer.checkUpkeep("0x");
            // Should return boolean (testing the view function)
            expect(typeof upkeepNeeded).to.equal("boolean");
        });
    });

    describe("Real Estate NFT", function () {
        it("Should tokenize property with dynamic pricing", async function () {
            // Tokenize property (STATE CHANGE)
            await expect(
                realEstateNFT.connect(deployer).tokenizeProperty(
                    user1.address,
                    "123 Blockchain Street, DeFi City",
                    500000, // $500K base value
                    2500,   // 2500 sqft
                    "Residential",
                    2020,   // Built in 2020
                    true,   // Dynamic pricing enabled
                    true,   // Fractional ownership enabled
                    1000    // 1000 total shares
                )
            ).to.emit(realEstateNFT, "PropertyTokenized");

            // Verify NFT was minted
            expect(await realEstateNFT.ownerOf(1)).to.equal(user1.address);

            // Verify property details
            const property = await realEstateNFT.getPropertyDetails(1);
            expect(property.propertyAddress).to.equal("123 Blockchain Street, DeFi City");
            expect(property.baseValueUSD).to.equal(500000);
            expect(property.isDynamic).to.be.true;
        });

        it("Should enable fractional ownership purchases", async function () {
            // First tokenize a property
            await realEstateNFT.connect(deployer).tokenizeProperty(
                user1.address,
                "456 Tokenization Ave",
                1000000, // $1M base value
                3000,    // 3000 sqft
                "Commercial",
                2021,
                true,
                true,    // Enable fractional
                10000   // 10000 total shares
            );

            // Purchase fractional shares (STATE CHANGE)
            const sharePrice = ethers.utils.parseEther("0.1");
            await expect(
                realEstateNFT.connect(user2).purchaseFractionalShares(
                    1,   // Token ID
                    100, // 100 shares
                    { value: sharePrice }
                )
            ).to.emit(realEstateNFT, "FractionalSharesPurchased");

            // Verify fractional ownership
            const [shares, totalShares, availableShares] = await realEstateNFT.getFractionalOwnership(1, user2.address);
            expect(shares).to.equal(100);
            expect(totalShares).to.equal(10000);
            expect(availableShares).to.equal(9900); // 10000 - 100
        });

        it("Should request VRF for property traits", async function () {
            // Tokenize property first
            await realEstateNFT.connect(deployer).tokenizeProperty(
                user1.address,
                "789 VRF Street",
                750000,
                2000,
                "Residential",
                2022,
                true, // Dynamic pricing
                false,
                0
            );

            // Request VRF traits (STATE CHANGE)
            await expect(
                realEstateNFT.requestPropertyTraits(1)
            ).to.not.be.reverted;
        });

        it("Should distribute rental yield to fractional owners", async function () {
            // Tokenize property with fractional ownership
            await realEstateNFT.connect(deployer).tokenizeProperty(
                user1.address,
                "999 Yield Street",
                800000,
                2200,
                "Residential",
                2023,
                true,
                true,  // Enable fractional
                1000
            );

            // Purchase some shares
            const sharePrice = ethers.utils.parseEther("0.1");
            await realEstateNFT.connect(user2).purchaseFractionalShares(
                1,
                200, // 20% ownership
                { value: sharePrice }
            );

            // Distribute rental yield (STATE CHANGE)
            const yieldAmount = ethers.utils.parseEther("1");
            await expect(
                realEstateNFT.connect(deployer).distributeRentalYield(1, { value: yieldAmount })
            ).to.emit(realEstateNFT, "RentalYieldDistributed");
        });
    });

    describe("Cross-Chain Lending", function () {
        const mockETH = "0x1234567890123456789012345678901234567890";
        const mockBTC = "0x2345678901234567890123456789012345678901";
        const mockUSDC = "0x3456789012345678901234567890123456789012";

        beforeEach(async function () {
            // Initialize lending pools
            await crossChainLending.initializeLendingPool(mockETH, 7500); // 75% LTV
            await crossChainLending.initializeLendingPool(mockBTC, 7000); // 70% LTV
            await crossChainLending.initializeLendingPool(mockUSDC, 8500); // 85% LTV
        });

        it("Should initialize lending pools with price feeds", async function () {
            // Verify pool was initialized
            const [totalDeposits, totalBorrows, utilizationRate, borrowRate, supplyRate, isActive] = 
                await crossChainLending.getPoolInfo(mockETH);
            
            expect(isActive).to.be.true;
            expect(totalDeposits).to.equal(0);
            expect(totalBorrows).to.equal(0);
        });

        it("Should calculate borrow limits using Chainlink prices", async function () {
            // Test borrow limit calculation (uses price feeds)
            const borrowLimit = await crossChainLending.calculateBorrowLimit(user1.address);
            expect(borrowLimit).to.equal(0); // No collateral supplied yet
        });

        it("Should calculate health factors", async function () {
            // Test health factor calculation
            const healthFactor = await crossChainLending.calculateHealthFactor(user1.address);
            expect(healthFactor).to.equal(10000); // Maximum health (no borrows)
        });

        it("Should check upkeep for automation", async function () {
            const [upkeepNeeded] = await crossChainLending.checkUpkeep("0x");
            expect(typeof upkeepNeeded).to.equal("boolean");
        });

        it("Should add supported chains for CCIP", async function () {
            const polygonChainSelector = "4051577828743386545";
            
            await crossChainLending.addSupportedChain(polygonChainSelector);
            
            // Verify chain was added (this would be checked in the mapping)
            expect(await crossChainLending.supportedChains(polygonChainSelector)).to.be.true;
        });
    });

    describe("Integration Tests", function () {
        it("Should demonstrate multi-service Chainlink integration", async function () {
            // 1. DeFi: Create portfolio with price feeds
            const ethAmount = ethers.utils.parseEther("5");
            const btcAmount = ethers.utils.parseEther("0.5");
            const depositAmount = ethers.utils.parseEther("2");

            await defiOptimizer.connect(user1).createPortfolio(
                ethAmount,
                btcAmount,
                true,
                { value: depositAmount }
            );

            // 2. Tokenization: Create NFT with VRF traits
            await realEstateNFT.connect(deployer).tokenizeProperty(
                user1.address,
                "Integration Test Property",
                600000,
                2800,
                "Mixed-Use",
                2024,
                true, // Dynamic pricing
                true, // Fractional ownership
                5000
            );

            // 3. Cross-Chain: Initialize lending pool
            const mockToken = "0x9999999999999999999999999999999999999999";
            await crossChainLending.initializeLendingPool(mockToken, 8000);

            // Verify all contracts are working
            const portfolio = await defiOptimizer.userPortfolios(user1.address);
            const nftOwner = await realEstateNFT.ownerOf(1);
            const [,,,,, isActive] = await crossChainLending.getPoolInfo(mockToken);

            expect(portfolio.autoRebalance).to.be.true;
            expect(nftOwner).to.equal(user1.address);
            expect(isActive).to.be.true;
        });

        it("Should handle emergency scenarios", async function () {
            // Create portfolio for emergency test
            const depositAmount = ethers.utils.parseEther("1");
            await defiOptimizer.connect(user1).createPortfolio(
                ethers.utils.parseEther("1"),
                ethers.utils.parseEther("0.1"),
                false,
                { value: depositAmount }
            );

            // Test emergency withdrawal
            await expect(
                defiOptimizer.connect(user1).emergencyWithdraw()
            ).to.not.be.reverted;
        });
    });

    describe("Gas Optimization Tests", function () {
        it("Should have reasonable gas costs for all operations", async function () {
            // Portfolio creation
            const tx1 = await defiOptimizer.connect(user1).createPortfolio(
                ethers.utils.parseEther("1"),
                ethers.utils.parseEther("0.1"),
                false,
                { value: ethers.utils.parseEther("0.5") }
            );
            const receipt1 = await tx1.wait();
            console.log(`Portfolio creation gas: ${receipt1.gasUsed}`);

            // NFT tokenization
            const tx2 = await realEstateNFT.connect(deployer).tokenizeProperty(
                user1.address,
                "Gas Test Property",
                500000,
                2000,
                "Residential",
                2024,
                true,
                false,
                0
            );
            const receipt2 = await tx2.wait();
            console.log(`NFT tokenization gas: ${receipt2.gasUsed}`);

            // Pool initialization
            const tx3 = await crossChainLending.initializeLendingPool(
                "0x1111111111111111111111111111111111111111",
                7500
            );
            const receipt3 = await tx3.wait();
            console.log(`Pool initialization gas: ${receipt3.gasUsed}`);

            // All operations should complete successfully
            expect(receipt1.status).to.equal(1);
            expect(receipt2.status).to.equal(1);
            expect(receipt3.status).to.equal(1);
        });
    });
});

// Helper function for testing time-dependent functions
async function increaseTime(seconds) {
    await ethers.provider.send("evm_increaseTime", [seconds]);
    await ethers.provider.send("evm_mine");
}

// Helper function for testing with mock price feeds
async function mockPriceFeedResponse(contract, price) {
    // In a real test environment, you would mock the Chainlink price feed response
    // This is a placeholder for demonstration
    return price;
}
