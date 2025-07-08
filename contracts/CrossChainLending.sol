// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/automation/AutomationCompatible.sol";
import "@chainlink/contracts/src/v0.8/ccip/applications/CCIPReceiver.sol";
import "@chainlink/contracts/src/v0.8/ccip/libraries/Client.sol";
import "@chainlink/contracts/src/v0.8/interfaces/IRouterClient.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title Cross-Chain Lending Protocol with Chainlink Integration
 * @notice Multi-chain lending and borrowing with Chainlink price feeds, automation, and CCIP
 * @dev Demonstrates DeFi cross-chain functionality with state changes
 */
contract CrossChainLending is CCIPReceiver, AutomationCompatibleInterface, Ownable, ReentrancyGuard {
    
    // Chainlink Price Feeds
    AggregatorV3Interface internal ethUsdPriceFeed;
    AggregatorV3Interface internal btcUsdPriceFeed;
    AggregatorV3Interface internal usdcUsdPriceFeed;
    
    // CCIP Router
    IRouterClient private immutable ccipRouter;
    
    // Lending Pool Configuration
    struct LendingPool {
        address tokenAddress;
        uint256 totalDeposits;
        uint256 totalBorrows;
        uint256 utilizationRate;
        uint256 borrowRate;
        uint256 supplyRate;
        uint256 collateralFactor; // Basis points (e.g., 7500 = 75%)
        bool isActive;
        uint256 lastUpdate;
    }
    
    struct UserPosition {
        uint256 supplied;
        uint256 borrowed;
        uint256 collateralValue;
        uint256 borrowLimit;
        uint256 healthFactor;
        uint256 lastUpdate;
        bool isActive;
    }
    
    struct CrossChainRequest {
        uint64 sourceChain;
        address sender;
        address token;
        uint256 amount;
        uint8 requestType; // 0: supply, 1: borrow, 2: repay, 3: withdraw
        bool fulfilled;
    }
    
    // Storage
    mapping(address => LendingPool) public lendingPools;
    mapping(address => mapping(address => UserPosition)) public userPositions; // user => token => position
    mapping(bytes32 => CrossChainRequest) public crossChainRequests;
    mapping(uint64 => bool) public supportedChains;
    
    address[] public supportedTokens;
    
    // Events
    event Deposit(address indexed user, address indexed token, uint256 amount);
    event Withdraw(address indexed user, address indexed token, uint256 amount);
    event Borrow(address indexed user, address indexed token, uint256 amount);
    event Repay(address indexed user, address indexed token, uint256 amount);
    event Liquidation(address indexed borrower, address indexed liquidator, address indexed token, uint256 amount);
    event CrossChainOperationInitiated(bytes32 indexed requestId, uint64 indexed targetChain, address indexed user);
    event CrossChainOperationCompleted(bytes32 indexed requestId, bool success);
    event InterestRateUpdated(address indexed token, uint256 newBorrowRate, uint256 newSupplyRate);
    
    // Automation Variables
    uint256 public constant RATE_UPDATE_INTERVAL = 1 hours;
    uint256 public lastRateUpdate;
    
    // Liquidation threshold
    uint256 public constant LIQUIDATION_THRESHOLD = 8000; // 80% in basis points
    
    constructor(
        address _ccipRouter,
        address _ethUsdPriceFeed,
        address _btcUsdPriceFeed,
        address _usdcUsdPriceFeed
    ) CCIPReceiver(_ccipRouter) {
        ccipRouter = IRouterClient(_ccipRouter);
        ethUsdPriceFeed = AggregatorV3Interface(_ethUsdPriceFeed);
        btcUsdPriceFeed = AggregatorV3Interface(_btcUsdPriceFeed);
        usdcUsdPriceFeed = AggregatorV3Interface(_usdcUsdPriceFeed);
        lastRateUpdate = block.timestamp;
    }
    
    /**
     * @notice Initialize a lending pool for a token
     * @param tokenAddress Address of the token
     * @param collateralFactor Collateral factor in basis points
     */
    function initializeLendingPool(
        address tokenAddress,
        uint256 collateralFactor
    ) external onlyOwner {
        require(tokenAddress != address(0), "Invalid token address");
        require(collateralFactor <= 9000, "Collateral factor too high"); // Max 90%
        
        // Initialize lending pool (STATE CHANGE)
        lendingPools[tokenAddress] = LendingPool({
            tokenAddress: tokenAddress,
            totalDeposits: 0,
            totalBorrows: 0,
            utilizationRate: 0,
            borrowRate: 500, // 5% initial rate
            supplyRate: 300, // 3% initial rate
            collateralFactor: collateralFactor,
            isActive: true,
            lastUpdate: block.timestamp
        });
        
        supportedTokens.push(tokenAddress);
    }
    
    /**
     * @notice Supply tokens to a lending pool
     * @param tokenAddress Address of the token to supply
     * @param amount Amount to supply
     */
    function supply(address tokenAddress, uint256 amount) external nonReentrant {
        require(lendingPools[tokenAddress].isActive, "Pool not active");
        require(amount > 0, "Amount must be greater than 0");
        
        // Transfer tokens from user (requires approval)
        IERC20(tokenAddress).transferFrom(msg.sender, address(this), amount);
        
        // Update pool state (STATE CHANGE)
        LendingPool storage pool = lendingPools[tokenAddress];
        pool.totalDeposits += amount;
        pool.lastUpdate = block.timestamp;
        
        // Update user position (STATE CHANGE)
        UserPosition storage position = userPositions[msg.sender][tokenAddress];
        position.supplied += amount;
        position.lastUpdate = block.timestamp;
        position.isActive = true;
        
        // Update interest rates
        updateInterestRates(tokenAddress);
        
        emit Deposit(msg.sender, tokenAddress, amount);
    }
    
    /**
     * @notice Borrow tokens from a lending pool
     * @param tokenAddress Address of the token to borrow
     * @param amount Amount to borrow
     */
    function borrow(address tokenAddress, uint256 amount) external nonReentrant {
        require(lendingPools[tokenAddress].isActive, "Pool not active");
        require(amount > 0, "Amount must be greater than 0");
        
        // Check borrow limit using Chainlink price feeds
        uint256 borrowLimitUSD = calculateBorrowLimit(msg.sender);
        uint256 currentBorrowsUSD = calculateUserBorrowsUSD(msg.sender);
        uint256 amountUSD = convertToUSD(tokenAddress, amount);
        
        require(currentBorrowsUSD + amountUSD <= borrowLimitUSD, "Insufficient collateral");
        
        // Update pool state (STATE CHANGE)
        LendingPool storage pool = lendingPools[tokenAddress];
        require(pool.totalDeposits >= pool.totalBorrows + amount, "Insufficient liquidity");
        
        pool.totalBorrows += amount;
        pool.lastUpdate = block.timestamp;
        
        // Update user position (STATE CHANGE)
        UserPosition storage position = userPositions[msg.sender][tokenAddress];
        position.borrowed += amount;
        position.lastUpdate = block.timestamp;
        position.isActive = true;
        
        // Transfer tokens to user
        IERC20(tokenAddress).transfer(msg.sender, amount);
        
        // Update interest rates
        updateInterestRates(tokenAddress);
        
        emit Borrow(msg.sender, tokenAddress, amount);
    }
    
    /**
     * @notice Repay borrowed tokens
     * @param tokenAddress Address of the token to repay
     * @param amount Amount to repay
     */
    function repay(address tokenAddress, uint256 amount) external nonReentrant {
        UserPosition storage position = userPositions[msg.sender][tokenAddress];
        require(position.borrowed > 0, "No outstanding borrow");
        
        uint256 repayAmount = amount > position.borrowed ? position.borrowed : amount;
        
        // Transfer tokens from user
        IERC20(tokenAddress).transferFrom(msg.sender, address(this), repayAmount);
        
        // Update pool state (STATE CHANGE)
        LendingPool storage pool = lendingPools[tokenAddress];
        pool.totalBorrows -= repayAmount;
        pool.lastUpdate = block.timestamp;
        
        // Update user position (STATE CHANGE)
        position.borrowed -= repayAmount;
        position.lastUpdate = block.timestamp;
        
        // Update interest rates
        updateInterestRates(tokenAddress);
        
        emit Repay(msg.sender, tokenAddress, repayAmount);
    }
    
    /**
     * @notice Withdraw supplied tokens
     * @param tokenAddress Address of the token to withdraw
     * @param amount Amount to withdraw
     */
    function withdraw(address tokenAddress, uint256 amount) external nonReentrant {
        UserPosition storage position = userPositions[msg.sender][tokenAddress];
        require(position.supplied >= amount, "Insufficient supplied balance");
        
        // Check if withdrawal would affect health factor
        uint256 newCollateralValue = calculateCollateralValue(msg.sender) - convertToUSD(tokenAddress, amount);
        uint256 currentBorrowsUSD = calculateUserBorrowsUSD(msg.sender);
        
        if (currentBorrowsUSD > 0) {
            uint256 newHealthFactor = (newCollateralValue * 10000) / currentBorrowsUSD;
            require(newHealthFactor >= LIQUIDATION_THRESHOLD, "Withdrawal would trigger liquidation");
        }
        
        // Update pool state (STATE CHANGE)
        LendingPool storage pool = lendingPools[tokenAddress];
        pool.totalDeposits -= amount;
        pool.lastUpdate = block.timestamp;
        
        // Update user position (STATE CHANGE)
        position.supplied -= amount;
        position.lastUpdate = block.timestamp;
        
        // Transfer tokens to user
        IERC20(tokenAddress).transfer(msg.sender, amount);
        
        // Update interest rates
        updateInterestRates(tokenAddress);
        
        emit Withdraw(msg.sender, tokenAddress, amount);
    }
    
    /**
     * @notice Liquidate an undercollateralized position
     * @param borrower Address of the borrower to liquidate
     * @param tokenAddress Address of the token to repay
     * @param amount Amount to repay
     */
    function liquidate(address borrower, address tokenAddress, uint256 amount) external nonReentrant {
        // Check if position is liquidatable
        uint256 healthFactor = calculateHealthFactor(borrower);
        require(healthFactor < LIQUIDATION_THRESHOLD, "Position is healthy");
        
        UserPosition storage borrowerPosition = userPositions[borrower][tokenAddress];
        require(borrowerPosition.borrowed > 0, "No outstanding borrow");
        
        uint256 liquidationAmount = amount > borrowerPosition.borrowed ? borrowerPosition.borrowed : amount;
        
        // Calculate liquidation bonus (10%)
        uint256 collateralValue = convertToUSD(tokenAddress, liquidationAmount);
        uint256 bonusValue = (collateralValue * 1100) / 1000; // 110% of debt value
        
        // Transfer repayment from liquidator
        IERC20(tokenAddress).transferFrom(msg.sender, address(this), liquidationAmount);
        
        // Update borrower position (STATE CHANGE)
        borrowerPosition.borrowed -= liquidationAmount;
        
        // Update pool state (STATE CHANGE)
        LendingPool storage pool = lendingPools[tokenAddress];
        pool.totalBorrows -= liquidationAmount;
        
        // Transfer collateral to liquidator (simplified - using same token)
        uint256 collateralToTransfer = (bonusValue * 1e18) / convertToUSD(tokenAddress, 1e18);
        UserPosition storage borrowerCollateral = userPositions[borrower][tokenAddress];
        
        if (borrowerCollateral.supplied >= collateralToTransfer) {
            borrowerCollateral.supplied -= collateralToTransfer;
            IERC20(tokenAddress).transfer(msg.sender, collateralToTransfer);
        }
        
        emit Liquidation(borrower, msg.sender, tokenAddress, liquidationAmount);
    }
    
    /**
     * @notice Send cross-chain lending operation using Chainlink CCIP
     * @param destinationChain Destination chain selector
     * @param receiver Receiver address on destination chain
     * @param tokenAddress Token address to operate on
     * @param amount Amount for the operation
     * @param operationType Type of operation (0: supply, 1: borrow, 2: repay, 3: withdraw)
     */
    function sendCrossChainOperation(
        uint64 destinationChain,
        address receiver,
        address tokenAddress,
        uint256 amount,
        uint8 operationType
    ) external payable returns (bytes32 messageId) {
        require(supportedChains[destinationChain], "Unsupported destination chain");
        require(operationType <= 3, "Invalid operation type");
        
        // Create CCIP message
        Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
            receiver: abi.encode(receiver),
            data: abi.encode(msg.sender, tokenAddress, amount, operationType),
            tokenAmounts: new Client.EVMTokenAmount[](0),
            extraArgs: Client._argsToBytes(Client.EVMExtraArgsV1({gasLimit: 500000})),
            feeToken: address(0) // Pay fees in native gas
        });
        
        // Send CCIP message (STATE CHANGE)
        messageId = ccipRouter.ccipSend{value: msg.value}(destinationChain, evm2AnyMessage);
        
        // Store cross-chain request (STATE CHANGE)
        crossChainRequests[messageId] = CrossChainRequest({
            sourceChain: destinationChain,
            sender: msg.sender,
            token: tokenAddress,
            amount: amount,
            requestType: operationType,
            fulfilled: false
        });
        
        emit CrossChainOperationInitiated(messageId, destinationChain, msg.sender);
        return messageId;
    }
    
    /**
     * @notice Handle incoming CCIP messages
     * @param any2EvmMessage CCIP message data
     */
    function _ccipReceive(Client.Any2EVMMessage memory any2EvmMessage) internal override {
        bytes32 messageId = any2EvmMessage.messageId;
        uint64 sourceChain = any2EvmMessage.sourceChainSelector;
        
        // Decode message data
        (address sender, address tokenAddress, uint256 amount, uint8 operationType) = 
            abi.decode(any2EvmMessage.data, (address, address, uint256, uint8));
        
        bool success = false;
        
        try this.executeCrossChainOperation(sender, tokenAddress, amount, operationType) {
            success = true;
        } catch {
            success = false;
        }
        
        // Update request status (STATE CHANGE)
        CrossChainRequest storage request = crossChainRequests[messageId];
        request.fulfilled = true;
        
        emit CrossChainOperationCompleted(messageId, success);
    }
    
    /**
     * @notice Execute cross-chain operation
     * @param sender Original sender
     * @param tokenAddress Token address
     * @param amount Amount
     * @param operationType Operation type
     */
    function executeCrossChainOperation(
        address sender,
        address tokenAddress,
        uint256 amount,
        uint8 operationType
    ) external {
        require(msg.sender == address(this), "Only self-callable");
        
        if (operationType == 0) {
            // Cross-chain supply logic (simplified)
            UserPosition storage position = userPositions[sender][tokenAddress];
            position.supplied += amount;
            lendingPools[tokenAddress].totalDeposits += amount;
        } else if (operationType == 1) {
            // Cross-chain borrow logic (simplified)
            UserPosition storage position = userPositions[sender][tokenAddress];
            position.borrowed += amount;
            lendingPools[tokenAddress].totalBorrows += amount;
        }
        // Additional operation types can be implemented
    }
    
    /**
     * @notice Update interest rates based on utilization
     * @param tokenAddress Token address
     */
    function updateInterestRates(address tokenAddress) internal {
        LendingPool storage pool = lendingPools[tokenAddress];
        
        if (pool.totalDeposits == 0) return;
        
        // Calculate utilization rate (STATE CHANGE)
        pool.utilizationRate = (pool.totalBorrows * 10000) / pool.totalDeposits;
        
        // Update rates based on utilization (simple linear model)
        pool.borrowRate = 200 + (pool.utilizationRate * 8); // 2% + utilization * 0.08%
        pool.supplyRate = (pool.borrowRate * pool.utilizationRate) / 10000;
        
        emit InterestRateUpdated(tokenAddress, pool.borrowRate, pool.supplyRate);
    }
    
    /**
     * @notice Calculate user's borrow limit using Chainlink price feeds
     * @param user User address
     * @return Borrow limit in USD
     */
    function calculateBorrowLimit(address user) public view returns (uint256) {
        uint256 totalCollateralValue = 0;
        
        for (uint i = 0; i < supportedTokens.length; i++) {
            address token = supportedTokens[i];
            UserPosition memory position = userPositions[user][token];
            
            if (position.supplied > 0) {
                uint256 valueUSD = convertToUSD(token, position.supplied);
                uint256 collateralValue = (valueUSD * lendingPools[token].collateralFactor) / 10000;
                totalCollateralValue += collateralValue;
            }
        }
        
        return totalCollateralValue;
    }
    
    /**
     * @notice Calculate user's total borrows in USD
     * @param user User address
     * @return Total borrows in USD
     */
    function calculateUserBorrowsUSD(address user) public view returns (uint256) {
        uint256 totalBorrowsUSD = 0;
        
        for (uint i = 0; i < supportedTokens.length; i++) {
            address token = supportedTokens[i];
            UserPosition memory position = userPositions[user][token];
            
            if (position.borrowed > 0) {
                totalBorrowsUSD += convertToUSD(token, position.borrowed);
            }
        }
        
        return totalBorrowsUSD;
    }
    
    /**
     * @notice Calculate user's collateral value
     * @param user User address
     * @return Collateral value in USD
     */
    function calculateCollateralValue(address user) public view returns (uint256) {
        uint256 totalCollateralValue = 0;
        
        for (uint i = 0; i < supportedTokens.length; i++) {
            address token = supportedTokens[i];
            UserPosition memory position = userPositions[user][token];
            
            if (position.supplied > 0) {
                totalCollateralValue += convertToUSD(token, position.supplied);
            }
        }
        
        return totalCollateralValue;
    }
    
    /**
     * @notice Calculate user's health factor
     * @param user User address
     * @return Health factor (10000 = 100%)
     */
    function calculateHealthFactor(address user) public view returns (uint256) {
        uint256 borrowLimitUSD = calculateBorrowLimit(user);
        uint256 currentBorrowsUSD = calculateUserBorrowsUSD(user);
        
        if (currentBorrowsUSD == 0) return 10000; // Maximum health
        
        return (borrowLimitUSD * 10000) / currentBorrowsUSD;
    }
    
    /**
     * @notice Convert token amount to USD using Chainlink price feeds
     * @param tokenAddress Token address
     * @param amount Token amount
     * @return USD value
     */
    function convertToUSD(address tokenAddress, uint256 amount) public view returns (uint256) {
        AggregatorV3Interface priceFeed;
        
        // Map tokens to price feeds (simplified)
        if (tokenAddress == address(0x1234)) { // Example ETH token
            priceFeed = ethUsdPriceFeed;
        } else if (tokenAddress == address(0x5678)) { // Example BTC token
            priceFeed = btcUsdPriceFeed;
        } else {
            priceFeed = usdcUsdPriceFeed; // Default to USDC
        }
        
        (, int256 price, , , ) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price data");
        
        return (amount * uint256(price)) / 1e8;
    }
    
    /**
     * @notice Chainlink Automation: Check if interest rate update is needed
     * @return upkeepNeeded Whether upkeep is needed
     * @return performData Data for performUpkeep
     */
    function checkUpkeep(bytes calldata checkData) external view override returns (bool upkeepNeeded, bytes memory performData) {
        upkeepNeeded = (block.timestamp - lastRateUpdate) > RATE_UPDATE_INTERVAL;
        performData = checkData;
    }
    
    /**
     * @notice Perform automated interest rate updates using Chainlink Automation
     * @param performData Data from checkUpkeep
     */
    function performUpkeep(bytes calldata performData) external override {
        require((block.timestamp - lastRateUpdate) > RATE_UPDATE_INTERVAL, "Update not needed");
        
        // Update rates for all supported tokens (STATE CHANGE)
        lastRateUpdate = block.timestamp;
        
        for (uint i = 0; i < supportedTokens.length; i++) {
            updateInterestRates(supportedTokens[i]);
        }
    }
    
    /**
     * @notice Add supported chain for cross-chain operations
     * @param chainSelector Chain selector
     */
    function addSupportedChain(uint64 chainSelector) external onlyOwner {
        supportedChains[chainSelector] = true;
    }
    
    /**
     * @notice Get pool information
     * @param tokenAddress Token address
     * @return Pool data
     */
    function getPoolInfo(address tokenAddress) external view returns (
        uint256 totalDeposits,
        uint256 totalBorrows,
        uint256 utilizationRate,
        uint256 borrowRate,
        uint256 supplyRate,
        bool isActive
    ) {
        LendingPool memory pool = lendingPools[tokenAddress];
        return (
            pool.totalDeposits,
            pool.totalBorrows,
            pool.utilizationRate,
            pool.borrowRate,
            pool.supplyRate,
            pool.isActive
        );
    }
}
