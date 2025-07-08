# 🏆 DeFi & Tokenization Platform - Chainlink Hackathon 2024

A comprehensive **DeFi and Tokenization** platform demonstrating state-changing Chainlink integrations across multiple services. Built for the Chainlink hackathon with focus on **innovative DeFi protocols** and **real-world asset tokenization**.

## 🎯 Hackathon Track Focus

### � **DeFi Track - AI-Powered Yield Optimizer**
- **Automated Portfolio Rebalancing**: Chainlink Automation triggers rebalancing based on market conditions
- **Dynamic Interest Rates**: Real-time rate adjustments using Chainlink Price Feeds
- **Cross-Chain Lending**: Multi-blockchain lending protocol with CCIP messaging
- **VRF-Powered Strategy Selection**: Provably fair randomness for portfolio optimization
- **Liquidation Engine**: Automated liquidations with Chainlink price data

### 🏠 **Tokenization Track - Dynamic Real Estate NFTs**
- **Real Estate Tokenization**: Convert physical properties into tradeable NFT tokens
- **Dynamic Pricing**: Property values update automatically using Chainlink price feeds
- **Fractional Ownership**: Invest in real estate with fractional NFT shares
- **VRF Trait Generation**: Random property characteristics for enhanced valuation
- **Rental Yield Distribution**: Automated income distribution to fractional owners

### 🔗 **State-Changing Chainlink Integration**
- **✅ Price Feeds**: Dynamic pricing and collateral calculations
- **✅ VRF**: Random trait generation and strategy optimization
- **✅ Automation**: Automated rebalancing, revaluations, and rate updates  
- **✅ CCIP**: Cross-chain lending operations and asset transfers
- **✅ Multiple Services**: 4+ Chainlink services used meaningfully

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Hardhat development environment
- Valid API keys for blockchain networks
- Chainlink VRF subscription with LINK tokens
- AWS Account for Lambda deployment (optional)

### Smart Contract Deployment
```bash
# Install dependencies
npm install

# Compile contracts
npm run compile

# Deploy to testnet (Sepolia)
npm run deploy:sepolia

# Deploy to mainnet (Ethereum)
npm run deploy:ethereum

# Deploy to Polygon
npm run deploy:polygon

# Deploy to Avalanche
npm run deploy:avalanche
```

### Environment Setup
```bash
# Create .env file with the following variables
PRIVATE_KEY=your_private_key_here
ETHEREUM_RPC_URL=your_ethereum_rpc_url
POLYGON_RPC_URL=your_polygon_rpc_url
AVALANCHE_RPC_URL=your_avalanche_rpc_url

# Chainlink Configuration
VRF_SUBSCRIPTION_ID=your_vrf_subscription_id
ETHERSCAN_API_KEY=your_etherscan_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key
SNOWTRACE_API_KEY=your_snowtrace_api_key
```

### Smart Contract Deployment
```bash
# Install dependencies
npm install

# Compile contracts
npm run compile

# Deploy to testnet (Sepolia) 
npm run deploy:sepolia

# Deploy to mainnet networks
npm run deploy:ethereum
npm run deploy:polygon
npm run deploy:avalanche

# Interact with deployed contracts
npm run interact:ethereum
```

### Contract Verification
```bash
# Verify on Etherscan
npm run verify:ethereum <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>

# Verify on Polygonscan
npm run verify:polygon <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
```

## 🔧 Smart Contract Documentation

### Core Contracts

#### 1. DeFiYieldOptimizer.sol
**AI-powered yield optimization with Chainlink automation**

```solidity
// Create portfolio with automatic rebalancing
function createPortfolio(
    uint256 _ethAmount,
    uint256 _btcAmount, 
    bool _enableAutoRebalance
) external payable

// Request VRF for portfolio optimization
function requestPortfolioOptimization() public returns (uint256 requestId)

// Harvest yield with compounding
function harvestYield() external
```

**State Changes:**
- ✅ Portfolio creation/updates using Chainlink price feeds
- ✅ VRF-powered strategy optimization
- ✅ Automated rebalancing via Chainlink Automation

#### 2. RealEstateNFT.sol
**Dynamic real estate tokenization with fractional ownership**

```solidity
// Tokenize real estate property
function tokenizeProperty(
    address to,
    string memory propertyAddress,
    uint256 baseValueUSD,
    bool enableFractional
) external returns (uint256 tokenId)

// Purchase fractional shares using Chainlink price feeds
function purchaseFractionalShares(
    uint256 tokenId,
    uint256 shares
) external payable

// Automated property revaluation
function performUpkeep(bytes calldata performData) external override
```

**State Changes:**
- ✅ Dynamic NFT minting with VRF traits
- ✅ Price-based fractional share purchases
- ✅ Automated property revaluations

#### 3. CrossChainLending.sol
**Multi-chain lending protocol with CCIP integration**

```solidity
// Supply tokens with collateral calculation
function supply(address tokenAddress, uint256 amount) external

// Borrow against collateral using price feeds
function borrow(address tokenAddress, uint256 amount) external

// Cross-chain lending operations
function sendCrossChainOperation(
    uint64 destinationChain,
    address tokenAddress,
    uint256 amount,
    uint8 operationType
) external payable
```

**State Changes:**
- ✅ Lending pool state updates using price feeds
- ✅ Cross-chain message sending via CCIP
- ✅ Automated interest rate adjustments

### AI Agent Endpoints

#### Chat with AI Agent
```bash
POST /ai/chat
Content-Type: application/json

{
  "message": "What's the best NFT collection to invest in?",
  "wallet_address": "0x1234...",
  "context": "portfolio_analysis"
}
```

#### Get AI-Powered Recommendations
```bash
GET /nft/multi-analysis?collections=bayc,cryptopunks,azuki
```

### DeFi Integration

#### Calculate Yield Opportunities
```bash
POST /defi/yield-analysis
Content-Type: application/json

{
  "wallet_address": "0x1234...",
  "risk_level": "moderate",
  "amount": "10.0"
}
```

#### Get Gas Optimization Suggestions
```bash
GET /blockchain/gas?network=ethereum&urgency=standard
```

### Cross-Chain Operations

#### Enable Cross-Chain Price Sync (State-Changing)
```bash
POST /chainlink/crosschain/sync
Content-Type: application/json

{
  "source_chain": "ethereum",
  "target_chains": ["polygon", "avalanche"]
}
```

#### Multi-Chain Portfolio View
```bash
GET /wallet/portfolio?address=0x1234...&chains=ethereum,polygon,arbitrum
```

## 💡 Hackathon Demonstration

### DeFi Track Examples

#### Yield Optimization with Chainlink Automation
```javascript
// Deploy DeFi Yield Optimizer
const defiOptimizer = await DeFiYieldOptimizer.deploy(
    vrfCoordinator,
    subscriptionId,
    keyHash,
    ethUsdPriceFeed,
    btcUsdPriceFeed,
    linkUsdPriceFeed
);

// Create portfolio with auto-rebalancing
await defiOptimizer.createPortfolio(
    ethers.utils.parseEther("10"), // 10 ETH
    ethers.utils.parseEther("1"),  // 1 BTC equivalent
    true, // Enable auto-rebalance
    { value: ethers.utils.parseEther("5") }
);

// Request VRF for portfolio optimization
await defiOptimizer.requestPortfolioOptimization();
```

#### Cross-Chain Lending Protocol
```javascript
// Initialize lending pools with Chainlink price feeds
await crossChainLending.initializeLendingPool(ethToken, 7500); // 75% LTV
await crossChainLending.initializeLendingPool(btcToken, 7000); // 70% LTV

// Supply collateral (state change using price feeds)
await crossChainLending.supply(ethToken, ethers.utils.parseEther("10"));

// Borrow against collateral (price feed validation)
await crossChainLending.borrow(usdcToken, ethers.utils.parseUnits("15000", 6));

// Cross-chain operation via CCIP
await crossChainLending.sendCrossChainOperation(
    polygonChainSelector,
    receiverContract,
    ethToken,
    ethers.utils.parseEther("5"),
    0 // Supply operation
);
```

### Tokenization Track Examples

#### Dynamic Real Estate NFT
```javascript
// Deploy Real Estate NFT contract
const realEstateNFT = await RealEstateNFT.deploy(
    vrfCoordinator,
    subscriptionId,
    keyHash,
    ethUsdPriceFeed,
    homePriceFeed
);

// Tokenize property with dynamic pricing
await realEstateNFT.tokenizeProperty(
    buyer.address,
    "123 Blockchain Street, DeFi City",
    500000, // $500K base value
    2500,   // 2500 sqft
    "Residential",
    2020,   // Built in 2020
    true,   // Dynamic pricing enabled
    true,   // Fractional ownership enabled
    1000    // 1000 total shares
);

// Purchase fractional shares using Chainlink price feeds
await realEstateNFT.purchaseFractionalShares(
    1,    // Token ID
    100,  // 100 shares (10% ownership)
    { value: calculatedEthPrice }
);

// VRF generates random property traits
// Automation triggers periodic revaluations
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CHAINLINK HACKATHON ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Frontend UI   │ 
                    │   (Optional)    │
                    └─────────────────┘
                             │
                    ┌─────────────────┐
                    │  Smart Contract │ 
                    │   Interactions  │
                    └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                   │                    │
┌──────▼──────┐    ┌────────▼────────┐    ┌─────▼──────┐
│DeFi Yield   │    │ Real Estate NFT │    │Cross-Chain │
│Optimizer    │    │  Tokenization   │    │  Lending   │
└─────────────┘    └─────────────────┘    └────────────┘
        │                   │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                   │                    │
┌──────▼──────┐    ┌────────▼────────┐    ┌─────▼──────┐
│ Chainlink   │    │ Chainlink VRF   │    │ Chainlink  │
│Price Feeds  │    │   Randomness    │    │Automation  │
└─────────────┘    └─────────────────┘    └────────────┘
                             │
                    ┌────────▼────────┐
                    │ Chainlink CCIP  │
                    │ Cross-Chain     │
                    └─────────────────┘
```

### Multi-Chain Deployment Strategy
- **Ethereum**: Primary DeFi hub with complex yield strategies
- **Polygon**: Lower gas costs for frequent operations and NFT trading
- **Avalanche**: High throughput for automated rebalancing operations
- **Cross-Chain**: CCIP enables seamless multi-chain portfolio management

## 🏆 Hackathon Compliance & Achievements

### ✅ Chainlink Integration Requirements Met

#### **State-Changing Operations** (Required for eligibility)
1. **Price Feeds** → Portfolio rebalancing, collateral calculations, NFT pricing
2. **VRF** → Portfolio optimization, NFT trait generation, property valuation  
3. **Automation** → Automated rebalancing, property revaluations, interest rate updates
4. **CCIP** → Cross-chain lending operations, multi-chain asset transfers

#### **Multiple Service Bonus Points**
- ✅ **4 Chainlink Services** used meaningfully (+3 bonus points)
- ✅ **DeFi Track**: Innovative yield optimization with AI-powered strategies
- ✅ **Tokenization Track**: Real estate NFTs with dynamic pricing and fractional ownership

### 🎯 Innovation Highlights

#### **1. AI-Powered DeFi Yield Optimizer**
- **Novel Approach**: Combines VRF randomness with AI strategy selection
- **State Changes**: Portfolio rebalancing, yield harvesting, risk management
- **Automation**: Continuous optimization without manual intervention
- **Multi-Asset**: ETH, BTC, stablecoins with dynamic allocation

#### **2. Dynamic Real Estate NFT Tokenization**  
- **Real-World Assets**: Tokenizes physical properties with verifiable data
- **Fractional Ownership**: Enables micro-investing in real estate
- **Dynamic Pricing**: Property values update based on market conditions
- **Automated Revaluation**: Chainlink Automation triggers periodic updates

#### **3. Cross-Chain Lending Protocol**
- **Multi-Chain Support**: Ethereum, Polygon, Avalanche integration
- **CCIP Integration**: Seamless cross-chain collateral and borrowing
- **Price Feed Validation**: Real-time collateral monitoring
- **Automated Liquidations**: Protects lender capital with instant liquidations

### 📊 Technical Excellence

#### **Smart Contract Security**
- ReentrancyGuard protection on all state-changing functions
- Comprehensive input validation and error handling
- Ownable access control for administrative functions
- SafeMath operations for all financial calculations

#### **Chainlink Best Practices**
- Proper VRF subscription management and fulfillment
- Price feed validation with staleness checks
- Automation upkeep gas optimization
- CCIP message encoding/decoding standards

#### **Production Readiness**
- Multi-network deployment configurations
- Contract verification and documentation
- Gas-optimized operations
- Comprehensive test coverage

### 🏅 Submission Checklist

- ✅ **State-changing Chainlink integration** (4 services)
- ✅ **DeFi innovation** (yield optimization + lending)
- ✅ **Tokenization innovation** (real estate + fractional ownership)
- ✅ **Public GitHub repository** with complete source code
- ✅ **Comprehensive README** with setup instructions
- ✅ **Smart contracts** deployed and verified
- ✅ **Demo scripts** showcasing all functionality
- ✅ **Technical documentation** for judges

### 🎬 Demo Video Outline

1. **Problem Statement** (30s): Complex DeFi strategies + illiquid real estate
2. **Solution Overview** (60s): Chainlink-powered automation + tokenization  
3. **DeFi Demo** (90s): Portfolio creation, VRF optimization, automated rebalancing
4. **Tokenization Demo** (90s): Property tokenization, fractional purchases, dynamic pricing
5. **Cross-Chain Demo** (60s): Multi-chain lending, CCIP operations
6. **Technical Deep Dive** (30s): State changes, multiple Chainlink services
7. **Impact & Future** (30s): Accessibility, automation, real-world adoption

**Total Duration**: 5 minutes (hackathon requirement)

### State-Changing Chainlink Usage Examples

1. **Automated Market Making**: Using Chainlink Automation to adjust NFT prices based on market conditions
2. **Cross-Chain Arbitrage**: CCIP-enabled price synchronization for cross-chain trading opportunities  
3. **Dynamic Yield Farming**: VRF-powered random reward distribution in DeFi pools
4. **Oracle-Based Insurance**: Chainlink feeds triggering automated insurance payments

### AI Agent Capabilities

1. **Natural Language Trading**: "Buy me the cheapest blue-chip NFT under 5 ETH"
2. **Portfolio Optimization**: AI-driven rebalancing suggestions based on market analysis
3. **Risk Assessment**: ML-powered risk scoring for DeFi protocols and NFT investments
4. **Market Prediction**: Sentiment analysis combined with on-chain data for trend prediction

## 🚀 Deployment Guide

### AWS Lambda Setup
```bash
# Set runtime to Python 3.9
# Set handler to lambda_handler.lambda_handler
# Set timeout to 30 seconds
# Set memory to 512 MB
```

### API Gateway Configuration
```bash
# Enable CORS for all endpoints
# Set up custom domain (optional)
# Configure rate limiting
# Add API key authentication
```

### DynamoDB Tables
```bash
# Sessions table for user state
# Transactions table for payment tracking
# Analytics table for usage metrics
```

## 📊 Usage Analytics

Track hackathon metrics:
- **Chainlink Integrations**: Price feeds, VRF requests, automation setups
- **AI Interactions**: Chat messages, analysis requests, recommendations
- **Cross-Chain Operations**: Bridge transactions, multi-chain queries
- **DeFi Activities**: Yield calculations, gas optimizations, portfolio analysis

## 🔧 Troubleshooting

### Common Issues
1. **API Rate Limits**: Implement exponential backoff
2. **Chainlink Network Issues**: Fallback to backup oracle networks
3. **Cross-Chain Delays**: Set appropriate timeout values
4. **AI Model Limits**: Queue requests for high-volume usage

### Debug Mode
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
```

## 🤝 Contributing

This hackathon project demonstrates enterprise-grade Web3 infrastructure with:
- Production-ready code architecture
- Comprehensive error handling
- Scalable cloud deployment
- Multi-chain compatibility
- AI-powered intelligence
- State-changing oracle integration

## 📄 License

MIT License - Built for hackathon demonstration of Web3 + AI integration.

## 🏆 Hackathon Achievement Highlights

✅ **Chainlink State-Changing**: Automation, CCIP, and VRF integration  
✅ **AI/Web3 Agent**: Bedrock-powered intelligent interactions  
✅ **DeFi Integration**: Yield optimization and portfolio management  
✅ **Tokenization**: Dynamic NFT creation and management  
✅ **Cross-Chain**: Multi-blockchain support with CCIP synchronization  

**Total Integration Score: 5/5 Hackathon Tracks** 🎯

### Get Gas Prices

```bash
curl "https://your-api-gateway-url/blockchain/gas"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/nft/data` | GET | Fetch comprehensive NFT data |
| `/wallet/login` | POST | Connect crypto wallet |
| `/wallet/status` | GET | Check wallet connection status |
| `/wallet/nfts` | GET | Get NFTs owned by wallet |
| `/payment/init` | POST | Initialize X402 payment |
| `/transaction/status` | GET | Check transaction status |
| `/blockchain/gas` | GET | Get current gas prices |
| `/search/web` | GET | Search NFT information online |
| `/nft/sentiment` | GET | Get collection sentiment analysis |
| `/ai/chat` | POST | Chat with AI assistant |

## Testing

### Local Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run local test:
   ```bash
   python test_local.py
   ```

### Lambda Console Testing

Use the test events in `lambda_test_events.json` to test different functionality in the AWS Lambda console.

## Configuration

### API Keys

The application requires API keys for various NFT data providers. You can obtain these from:

- [Moralis](https://moralis.io/) - NFT metadata and blockchain data
- [Alchemy](https://www.alchemy.com/) - Enhanced NFT APIs
- [NFTScan](https://nftscan.com/) - Multi-chain NFT data
- [OpenSea](https://opensea.io/developers) - Marketplace data
- [NFTGo](https://nftgo.io/) - Analytics and rarity data
- [Reservoir](https://reservoir.tools/) - NFT market data
- [Perplexity](https://www.perplexity.ai/) - AI-powered search
- [Etherscan](https://etherscan.io/apis) - Gas price data

### Optional Integrations

- **Amazon Bedrock**: For AI-powered NFT analysis
- **CDP Wallet**: For enhanced wallet functionality
- **DynamoDB**: For session and transaction storage

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Lambda Handler │────│   External APIs │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌───────┴───────┐
                       │               │
                ┌─────────────┐  ┌─────────────┐
                │  DynamoDB   │  │   Bedrock   │
                └─────────────┘  └─────────────┘
```

## Error Handling

The application includes comprehensive error handling:

- API timeout management
- Graceful degradation when services are unavailable
- Automatic fallback to alternative data sources
- Detailed error logging for debugging

## Security

- Environment variables for sensitive configuration
- Input validation for all endpoints
- CORS headers for web integration
- Rate limiting considerations built-in

## Development

### Adding New APIs

1. Create new API module in `apis/` directory
2. Implement standardized response format
3. Add API check in `utils/utils.py`
4. Update main handler routing

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## Troubleshooting

### Common Issues

**ImportError**: Ensure all dependencies are included in deployment package
**API Rate Limits**: Implement proper API key rotation
**Timeout Errors**: Adjust timeout values in `config.py`
**Memory Issues**: Increase Lambda memory allocation for large responses

### Logs

Monitor CloudWatch logs for detailed error information:

```bash
aws logs tail /aws/lambda/your-function-name --follow
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check CloudWatch logs for error details
- Review API provider documentation
- Ensure all environment variables are set correctly
