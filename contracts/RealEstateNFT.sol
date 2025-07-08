// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/automation/AutomationCompatible.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title Dynamic NFT Real Estate Tokenization with Chainlink
 * @notice Tokenizes real estate assets with dynamic pricing using Chainlink price feeds and VRF
 * @dev Demonstrates tokenization with multiple Chainlink services and state changes
 */
contract RealEstateNFT is ERC721, ERC721URIStorage, VRFConsumerBaseV2, AutomationCompatibleInterface, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    // Chainlink VRF Variables
    VRFCoordinatorV2Interface private immutable vrfCoordinator;
    uint64 private immutable subscriptionId;
    bytes32 private immutable keyHash;
    uint32 private constant CALLBACK_GAS_LIMIT = 300000;
    uint16 private constant REQUEST_CONFIRMATIONS = 3;
    uint32 private constant NUM_WORDS = 3;
    
    // Price Feeds
    AggregatorV3Interface internal ethUsdPriceFeed;
    AggregatorV3Interface internal homePriceFeed; // Custom real estate price feed
    
    // Counters
    Counters.Counter private tokenIdCounter;
    
    // Property Data Structures
    struct Property {
        uint256 tokenId;
        string propertyAddress;
        uint256 baseValueUSD;
        uint256 currentValueUSD;
        uint256 sqft;
        string propertyType;
        uint256 yearBuilt;
        uint256 lastValuation;
        bool isDynamic;
        uint256[] traits; // Random traits from VRF
        uint256 rentalYieldBasisPoints; // Annual rental yield in basis points
        address[] fractionalOwners;
        mapping(address => uint256) fractionalShares;
    }
    
    struct ValuationRequest {
        uint256 tokenId;
        address requester;
        uint256 timestamp;
        bool fulfilled;
    }
    
    // Storage
    mapping(uint256 => Property) public properties;
    mapping(uint256 => ValuationRequest) public valuationRequests;
    mapping(uint256 => uint256) public vrfRequestToTokenId;
    mapping(address => uint256[]) public ownerProperties;
    
    // Fractional ownership
    mapping(uint256 => uint256) public totalFractionalShares;
    mapping(uint256 => uint256) public availableFractionalShares;
    
    // Events
    event PropertyTokenized(uint256 indexed tokenId, string propertyAddress, uint256 valueUSD);
    event PropertyRevalued(uint256 indexed tokenId, uint256 oldValue, uint256 newValue);
    event TraitsGenerated(uint256 indexed tokenId, uint256[] traits);
    event FractionalSharesPurchased(uint256 indexed tokenId, address buyer, uint256 shares, uint256 price);
    event RentalYieldDistributed(uint256 indexed tokenId, uint256 totalAmount);
    
    // Automation Variables
    uint256 public constant REVALUATION_INTERVAL = 7 days; // Weekly revaluations
    
    constructor(
        address _vrfCoordinator,
        uint64 _subscriptionId,
        bytes32 _keyHash,
        address _ethUsdPriceFeed,
        address _homePriceFeed
    ) 
        ERC721("Dynamic Real Estate NFT", "DREN") 
        VRFConsumerBaseV2(_vrfCoordinator) 
    {
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        subscriptionId = _subscriptionId;
        keyHash = _keyHash;
        ethUsdPriceFeed = AggregatorV3Interface(_ethUsdPriceFeed);
        homePriceFeed = AggregatorV3Interface(_homePriceFeed);
    }
    
    /**
     * @notice Tokenize a real estate property with dynamic pricing
     * @param to Address to mint the NFT to
     * @param propertyAddress Physical address of the property
     * @param baseValueUSD Base value of the property in USD
     * @param sqft Square footage of the property
     * @param propertyType Type of property (residential, commercial, etc.)
     * @param yearBuilt Year the property was built
     * @param isDynamic Whether the property has dynamic pricing enabled
     * @param enableFractional Whether to enable fractional ownership
     * @param totalShares Total fractional shares if enabled
     */
    function tokenizeProperty(
        address to,
        string memory propertyAddress,
        uint256 baseValueUSD,
        uint256 sqft,
        string memory propertyType,
        uint256 yearBuilt,
        bool isDynamic,
        bool enableFractional,
        uint256 totalShares
    ) external onlyOwner returns (uint256) {
        tokenIdCounter.increment();
        uint256 tokenId = tokenIdCounter.current();
        
        // Mint NFT (STATE CHANGE)
        _safeMint(to, tokenId);
        
        // Initialize property data (STATE CHANGE)
        Property storage property = properties[tokenId];
        property.tokenId = tokenId;
        property.propertyAddress = propertyAddress;
        property.baseValueUSD = baseValueUSD;
        property.currentValueUSD = baseValueUSD;
        property.sqft = sqft;
        property.propertyType = propertyType;
        property.yearBuilt = yearBuilt;
        property.lastValuation = block.timestamp;
        property.isDynamic = isDynamic;
        property.rentalYieldBasisPoints = 500; // Default 5% rental yield
        
        // Setup fractional ownership if enabled
        if (enableFractional) {
            totalFractionalShares[tokenId] = totalShares;
            availableFractionalShares[tokenId] = totalShares;
        }
        
        // Add to owner's properties
        ownerProperties[to].push(tokenId);
        
        // Request VRF for property traits
        if (isDynamic) {
            requestPropertyTraits(tokenId);
        }
        
        emit PropertyTokenized(tokenId, propertyAddress, baseValueUSD);
        return tokenId;
    }
    
    /**
     * @notice Request random traits for property using Chainlink VRF
     * @param tokenId Property token ID
     */
    function requestPropertyTraits(uint256 tokenId) public returns (uint256 requestId) {
        require(_exists(tokenId), "Property does not exist");
        
        // Request randomness for property traits (STATE CHANGE)
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            REQUEST_CONFIRMATIONS,
            CALLBACK_GAS_LIMIT,
            NUM_WORDS
        );
        
        vrfRequestToTokenId[requestId] = tokenId;
        return requestId;
    }
    
    /**
     * @notice Callback function used by VRF Coordinator for trait generation
     * @param requestId Request ID from VRF
     * @param randomWords Array of random values
     */
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
        uint256 tokenId = vrfRequestToTokenId[requestId];
        require(tokenId != 0, "Invalid request");
        
        // Generate property traits using randomness (STATE CHANGE)
        Property storage property = properties[tokenId];
        
        // Clear existing traits
        delete property.traits;
        
        // Generate traits from randomness
        for (uint i = 0; i < randomWords.length; i++) {
            property.traits.push(randomWords[i] % 100); // Traits as percentages
        }
        
        // Update property value based on traits
        updatePropertyValueFromTraits(tokenId);
        
        delete vrfRequestToTokenId[requestId];
        emit TraitsGenerated(tokenId, property.traits);
    }
    
    /**
     * @notice Update property value based on generated traits and market data
     * @param tokenId Property token ID
     */
    function updatePropertyValueFromTraits(uint256 tokenId) internal {
        Property storage property = properties[tokenId];
        require(property.traits.length >= 3, "Insufficient traits");
        
        // Get current home price index from Chainlink
        int256 homePriceIndex = getLatestPrice(homePriceFeed);
        require(homePriceIndex > 0, "Invalid home price data");
        
        // Calculate value adjustment based on traits
        uint256 locationScore = property.traits[0]; // 0-100
        uint256 conditionScore = property.traits[1]; // 0-100
        uint256 marketScore = property.traits[2]; // 0-100
        
        // Combine scores to create multiplier
        uint256 avgScore = (locationScore + conditionScore + marketScore) / 3;
        uint256 multiplier = 80 + (avgScore * 40) / 100; // 80% to 120% multiplier
        
        // Apply market price index
        uint256 marketAdjustment = (uint256(homePriceIndex) * 100) / 1e8; // Normalize to percentage
        
        // Calculate new value (STATE CHANGE)
        uint256 oldValue = property.currentValueUSD;
        property.currentValueUSD = (property.baseValueUSD * multiplier * marketAdjustment) / 10000;
        property.lastValuation = block.timestamp;
        
        emit PropertyRevalued(tokenId, oldValue, property.currentValueUSD);
    }
    
    /**
     * @notice Purchase fractional shares of a property
     * @param tokenId Property token ID
     * @param shares Number of shares to purchase
     */
    function purchaseFractionalShares(uint256 tokenId, uint256 shares) external payable nonReentrant {
        require(_exists(tokenId), "Property does not exist");
        require(shares > 0, "Shares must be greater than 0");
        require(availableFractionalShares[tokenId] >= shares, "Insufficient shares available");
        
        // Calculate price per share based on current property value
        uint256 pricePerShare = properties[tokenId].currentValueUSD / totalFractionalShares[tokenId];
        uint256 totalPrice = pricePerShare * shares;
        
        // Convert USD price to ETH using Chainlink price feed
        int256 ethPrice = getLatestPrice(ethUsdPriceFeed);
        require(ethPrice > 0, "Invalid ETH price");
        
        uint256 ethRequired = (totalPrice * 1e18) / uint256(ethPrice);
        require(msg.value >= ethRequired, "Insufficient ETH sent");
        
        // Update fractional ownership (STATE CHANGE)
        properties[tokenId].fractionalShares[msg.sender] += shares;
        properties[tokenId].fractionalOwners.push(msg.sender);
        availableFractionalShares[tokenId] -= shares;
        
        // Refund excess ETH
        if (msg.value > ethRequired) {
            payable(msg.sender).transfer(msg.value - ethRequired);
        }
        
        emit FractionalSharesPurchased(tokenId, msg.sender, shares, ethRequired);
    }
    
    /**
     * @notice Distribute rental yield to fractional owners
     * @param tokenId Property token ID
     */
    function distributeRentalYield(uint256 tokenId) external payable onlyOwner {
        require(_exists(tokenId), "Property does not exist");
        require(msg.value > 0, "No yield to distribute");
        
        Property storage property = properties[tokenId];
        uint256 totalShares = totalFractionalShares[tokenId];
        require(totalShares > 0, "No fractional shares exist");
        
        // Distribute yield proportionally to fractional owners
        for (uint i = 0; i < property.fractionalOwners.length; i++) {
            address owner = property.fractionalOwners[i];
            uint256 shares = property.fractionalShares[owner];
            
            if (shares > 0) {
                uint256 yieldAmount = (msg.value * shares) / totalShares;
                if (yieldAmount > 0) {
                    payable(owner).transfer(yieldAmount);
                }
            }
        }
        
        emit RentalYieldDistributed(tokenId, msg.value);
    }
    
    /**
     * @notice Get latest price from Chainlink price feed
     * @param _priceFeed Address of the Chainlink price feed
     * @return Latest price
     */
    function getLatestPrice(AggregatorV3Interface _priceFeed) public view returns (int256) {
        (, int256 price, , , ) = _priceFeed.latestRoundData();
        return price;
    }
    
    /**
     * @notice Chainlink Automation: Check if revaluation is needed
     * @return upkeepNeeded Whether upkeep is needed
     * @return performData Data for performUpkeep
     */
    function checkUpkeep(bytes calldata checkData) external view override returns (bool upkeepNeeded, bytes memory performData) {
        // Check if any property needs revaluation
        uint256 currentTokenId = tokenIdCounter.current();
        
        for (uint256 i = 1; i <= currentTokenId; i++) {
            if (_exists(i) && properties[i].isDynamic) {
                if (block.timestamp - properties[i].lastValuation > REVALUATION_INTERVAL) {
                    upkeepNeeded = true;
                    performData = abi.encode(i);
                    break;
                }
            }
        }
    }
    
    /**
     * @notice Perform automated revaluation using Chainlink Automation
     * @param performData Data from checkUpkeep containing token ID
     */
    function performUpkeep(bytes calldata performData) external override {
        uint256 tokenId = abi.decode(performData, (uint256));
        
        require(_exists(tokenId), "Property does not exist");
        require(properties[tokenId].isDynamic, "Property is not dynamic");
        require(
            block.timestamp - properties[tokenId].lastValuation > REVALUATION_INTERVAL,
            "Revaluation not needed"
        );
        
        // Trigger new trait generation and revaluation (STATE CHANGE)
        requestPropertyTraits(tokenId);
    }
    
    /**
     * @notice Get property details
     * @param tokenId Property token ID
     * @return Property data
     */
    function getPropertyDetails(uint256 tokenId) external view returns (
        string memory propertyAddress,
        uint256 baseValueUSD,
        uint256 currentValueUSD,
        uint256 sqft,
        string memory propertyType,
        uint256 yearBuilt,
        uint256 lastValuation,
        bool isDynamic,
        uint256[] memory traits
    ) {
        require(_exists(tokenId), "Property does not exist");
        Property storage property = properties[tokenId];
        
        return (
            property.propertyAddress,
            property.baseValueUSD,
            property.currentValueUSD,
            property.sqft,
            property.propertyType,
            property.yearBuilt,
            property.lastValuation,
            property.isDynamic,
            property.traits
        );
    }
    
    /**
     * @notice Get fractional ownership details
     * @param tokenId Property token ID
     * @param owner Address to check
     * @return shares Number of shares owned
     * @return totalShares Total shares for the property
     * @return availableShares Available shares for purchase
     */
    function getFractionalOwnership(uint256 tokenId, address owner) external view returns (
        uint256 shares,
        uint256 totalShares,
        uint256 availableShares
    ) {
        require(_exists(tokenId), "Property does not exist");
        
        return (
            properties[tokenId].fractionalShares[owner],
            totalFractionalShares[tokenId],
            availableFractionalShares[tokenId]
        );
    }
    
    /**
     * @notice Override required by Solidity for multiple inheritance
     */
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }
    
    /**
     * @notice Override required by Solidity for multiple inheritance
     */
    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }
    
    /**
     * @notice Override required by Solidity for multiple inheritance
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
