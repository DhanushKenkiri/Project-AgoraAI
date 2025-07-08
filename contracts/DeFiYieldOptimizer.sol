// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/automation/AutomationCompatible.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title DeFi Yield Optimizer with Chainlink Integration
 * @notice AI-powered yield optimization using Chainlink price feeds, automation, and VRF
 * @dev Demonstrates multiple Chainlink services in a DeFi context with state changes
 */
contract DeFiYieldOptimizer is VRFConsumerBaseV2, AutomationCompatibleInterface, Ownable, ReentrancyGuard {
    
    // Chainlink VRF Variables
    VRFCoordinatorV2Interface private immutable vrfCoordinator;
    uint64 private immutable subscriptionId;
    bytes32 private immutable keyHash;
    uint32 private constant CALLBACK_GAS_LIMIT = 200000;
    uint16 private constant REQUEST_CONFIRMATIONS = 3;
    uint32 private constant NUM_WORDS = 1;
    
    // Chainlink Price Feeds
    AggregatorV3Interface internal ethUsdPriceFeed;
    AggregatorV3Interface internal btcUsdPriceFeed;
    AggregatorV3Interface internal linkUsdPriceFeed;
    
    // Strategy Configuration
    struct YieldStrategy {
        address tokenAddress;
        uint256 currentAllocation;
        uint256 targetAllocation;
        uint256 minYield;
        uint256 maxRisk;
        bool isActive;
        uint256 lastRebalance;
    }
    
    struct UserPortfolio {
        uint256 totalValue;
        uint256 ethAllocation;
        uint256 btcAllocation;
        uint256 stableAllocation;
        uint256 totalYieldEarned;
        uint256 riskScore;
        bool autoRebalance;
        uint256 lastUpdate;
    }
    
    // Storage
    mapping(address => UserPortfolio) public userPortfolios;
    mapping(uint256 => address) public vrfRequestToUser;
    mapping(address => YieldStrategy[]) public userStrategies;
    
    // Events
    event PortfolioRebalanced(address indexed user, uint256 newEthAllocation, uint256 newBtcAllocation);
    event YieldHarvested(address indexed user, uint256 amount);
    event StrategyOptimized(address indexed user, uint256 vrfRequestId);
    event PriceThresholdTriggered(address indexed user, string asset, int256 price);
    
    // Automation Variables
    uint256 public constant REBALANCE_INTERVAL = 24 hours;
    uint256 public lastRebalanceTime;
    
    constructor(
        address _vrfCoordinator,
        uint64 _subscriptionId,
        bytes32 _keyHash,
        address _ethUsdPriceFeed,
        address _btcUsdPriceFeed,
        address _linkUsdPriceFeed
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        subscriptionId = _subscriptionId;
        keyHash = _keyHash;
        
        ethUsdPriceFeed = AggregatorV3Interface(_ethUsdPriceFeed);
        btcUsdPriceFeed = AggregatorV3Interface(_btcUsdPriceFeed);
        linkUsdPriceFeed = AggregatorV3Interface(_linkUsdPriceFeed);
        
        lastRebalanceTime = block.timestamp;
    }
    
    /**
     * @notice Get latest price from Chainlink price feed
     * @param _priceFeed Address of the Chainlink price feed
     * @return Latest price with 8 decimals
     */
    function getLatestPrice(AggregatorV3Interface _priceFeed) public view returns (int256) {
        (, int256 price, , , ) = _priceFeed.latestRoundData();
        return price;
    }
    
    /**
     * @notice Create or update user portfolio with Chainlink price data
     * @param _ethAmount Amount of ETH to allocate
     * @param _btcAmount Amount of BTC to allocate
     * @param _enableAutoRebalance Enable automatic rebalancing
     */
    function createPortfolio(
        uint256 _ethAmount,
        uint256 _btcAmount,
        bool _enableAutoRebalance
    ) external payable nonReentrant {
        require(msg.value > 0, "Must deposit funds");
        
        // Get current prices from Chainlink
        int256 ethPrice = getLatestPrice(ethUsdPriceFeed);
        int256 btcPrice = getLatestPrice(btcUsdPriceFeed);
        
        require(ethPrice > 0 && btcPrice > 0, "Invalid price data");
        
        // Calculate portfolio value in USD
        uint256 ethValueUsd = (_ethAmount * uint256(ethPrice)) / 1e8;
        uint256 btcValueUsd = (_btcAmount * uint256(btcPrice)) / 1e8;
        uint256 totalValueUsd = ethValueUsd + btcValueUsd + (msg.value);
        
        // Calculate risk score using VRF for randomization component
        if (_enableAutoRebalance) {
            requestPortfolioOptimization();
        }
        
        // Update user portfolio (STATE CHANGE)
        userPortfolios[msg.sender] = UserPortfolio({
            totalValue: totalValueUsd,
            ethAllocation: _ethAmount,
            btcAllocation: _btcAmount,
            stableAllocation: msg.value,
            totalYieldEarned: 0,
            riskScore: calculateRiskScore(ethValueUsd, btcValueUsd, totalValueUsd),
            autoRebalance: _enableAutoRebalance,
            lastUpdate: block.timestamp
        });
        
        emit PortfolioRebalanced(msg.sender, _ethAmount, _btcAmount);
    }
    
    /**
     * @notice Request portfolio optimization using Chainlink VRF for randomization
     * @dev This demonstrates VRF usage for DeFi strategy optimization
     */
    function requestPortfolioOptimization() public returns (uint256 requestId) {
        require(userPortfolios[msg.sender].totalValue > 0, "No portfolio found");
        
        // Request randomness for portfolio optimization (STATE CHANGE)
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            REQUEST_CONFIRMATIONS,
            CALLBACK_GAS_LIMIT,
            NUM_WORDS
        );
        
        vrfRequestToUser[requestId] = msg.sender;
        
        emit StrategyOptimized(msg.sender, requestId);
        return requestId;
    }
    
    /**
     * @notice Callback function used by VRF Coordinator
     * @param requestId Request ID from VRF
     * @param randomWords Array of random values
     */
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
        address user = vrfRequestToUser[requestId];
        require(user != address(0), "Invalid request");
        
        // Use randomness to optimize portfolio allocation (STATE CHANGE)
        uint256 randomness = randomWords[0];
        optimizePortfolioWithRandomness(user, randomness);
        
        delete vrfRequestToUser[requestId];
    }
    
    /**
     * @notice Optimize portfolio using VRF randomness and price data
     * @param user User address
     * @param randomness Random value from VRF
     */
    function optimizePortfolioWithRandomness(address user, uint256 randomness) internal {
        UserPortfolio storage portfolio = userPortfolios[user];
        
        // Get current prices
        int256 ethPrice = getLatestPrice(ethUsdPriceFeed);
        int256 btcPrice = getLatestPrice(btcUsdPriceFeed);
        
        // Use randomness to determine rebalancing strategy
        uint256 strategy = randomness % 3; // 0, 1, or 2
        
        uint256 newEthAllocation = portfolio.ethAllocation;
        uint256 newBtcAllocation = portfolio.btcAllocation;
        
        if (strategy == 0) {
            // Conservative: Increase stable allocation
            newEthAllocation = (portfolio.ethAllocation * 80) / 100;
            newBtcAllocation = (portfolio.btcAllocation * 80) / 100;
        } else if (strategy == 1) {
            // Aggressive: Increase ETH allocation if price is favorable
            if (ethPrice > btcPrice / 15) { // Simple price ratio check
                newEthAllocation = (portfolio.ethAllocation * 120) / 100;
                newBtcAllocation = (portfolio.btcAllocation * 90) / 100;
            }
        } else {
            // Balanced: Increase BTC allocation
            newEthAllocation = (portfolio.ethAllocation * 90) / 100;
            newBtcAllocation = (portfolio.btcAllocation * 110) / 100;
        }
        
        // Update portfolio allocations (STATE CHANGE)
        portfolio.ethAllocation = newEthAllocation;
        portfolio.btcAllocation = newBtcAllocation;
        portfolio.lastUpdate = block.timestamp;
        
        emit PortfolioRebalanced(user, newEthAllocation, newBtcAllocation);
    }
    
    /**
     * @notice Chainlink Automation function to check if rebalancing is needed
     * @return upkeepNeeded Whether upkeep is needed
     * @return performData Data to be used in performUpkeep
     */
    function checkUpkeep(bytes calldata checkData) external view override returns (bool upkeepNeeded, bytes memory performData) {
        upkeepNeeded = (block.timestamp - lastRebalanceTime) > REBALANCE_INTERVAL;
        performData = checkData;
    }
    
    /**
     * @notice Perform automated rebalancing using Chainlink Automation
     * @param performData Data from checkUpkeep
     */
    function performUpkeep(bytes calldata performData) external override {
        require((block.timestamp - lastRebalanceTime) > REBALANCE_INTERVAL, "Rebalancing not needed");
        
        // Update global rebalance time (STATE CHANGE)
        lastRebalanceTime = block.timestamp;
        
        // Trigger rebalancing for users with auto-rebalance enabled
        // In production, this would iterate through active users
        // For demo purposes, we emit an event
        emit PriceThresholdTriggered(address(this), "GLOBAL_REBALANCE", getLatestPrice(ethUsdPriceFeed));
    }
    
    /**
     * @notice Calculate risk score based on allocation
     * @param ethValue ETH value in USD
     * @param btcValue BTC value in USD  
     * @param totalValue Total portfolio value in USD
     * @return Risk score (0-100)
     */
    function calculateRiskScore(uint256 ethValue, uint256 btcValue, uint256 totalValue) internal pure returns (uint256) {
        if (totalValue == 0) return 0;
        
        uint256 cryptoAllocation = ((ethValue + btcValue) * 100) / totalValue;
        
        // Higher crypto allocation = higher risk
        if (cryptoAllocation > 80) return 90;
        if (cryptoAllocation > 60) return 70;
        if (cryptoAllocation > 40) return 50;
        if (cryptoAllocation > 20) return 30;
        return 10;
    }
    
    /**
     * @notice Harvest yield from portfolio (simulated)
     * @dev In production, this would interact with actual DeFi protocols
     */
    function harvestYield() external nonReentrant {
        UserPortfolio storage portfolio = userPortfolios[msg.sender];
        require(portfolio.totalValue > 0, "No portfolio found");
        
        // Calculate yield based on time and allocation (simplified)
        uint256 timeDiff = block.timestamp - portfolio.lastUpdate;
        uint256 yieldAmount = (portfolio.totalValue * timeDiff * 5) / (365 days * 100); // 5% APY
        
        // Update portfolio (STATE CHANGE)
        portfolio.totalYieldEarned += yieldAmount;
        portfolio.totalValue += yieldAmount;
        portfolio.lastUpdate = block.timestamp;
        
        emit YieldHarvested(msg.sender, yieldAmount);
    }
    
    /**
     * @notice Get portfolio value in USD using current Chainlink prices
     * @param user User address
     * @return Current portfolio value in USD
     */
    function getPortfolioValueUSD(address user) external view returns (uint256) {
        UserPortfolio memory portfolio = userPortfolios[user];
        
        int256 ethPrice = getLatestPrice(ethUsdPriceFeed);
        int256 btcPrice = getLatestPrice(btcUsdPriceFeed);
        
        uint256 ethValueUsd = (portfolio.ethAllocation * uint256(ethPrice)) / 1e8;
        uint256 btcValueUsd = (portfolio.btcAllocation * uint256(btcPrice)) / 1e8;
        
        return ethValueUsd + btcValueUsd + portfolio.stableAllocation;
    }
    
    /**
     * @notice Emergency withdrawal function
     */
    function emergencyWithdraw() external nonReentrant {
        UserPortfolio storage portfolio = userPortfolios[msg.sender];
        require(portfolio.stableAllocation > 0, "No funds to withdraw");
        
        uint256 amount = portfolio.stableAllocation;
        portfolio.stableAllocation = 0;
        
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Withdrawal failed");
    }
    
    /**
     * @notice Get supported price feeds
     * @return Array of price feed addresses
     */
    function getSupportedPriceFeeds() external view returns (address[] memory) {
        address[] memory feeds = new address[](3);
        feeds[0] = address(ethUsdPriceFeed);
        feeds[1] = address(btcUsdPriceFeed);
        feeds[2] = address(linkUsdPriceFeed);
        return feeds;
    }
}
