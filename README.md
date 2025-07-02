# 🏆 Web3 AI Agent NFT Platform - Hackathon Edition

A comprehensive Web3 AI Agent platform that demonstrates all major hackathon tracks: **DeFi**, **Tokenization**, **Cross-chain**, **AI/Web3 Agent**, and **Chainlink Integration** with state-changing functionality.

## 🎯 Hackathon Tracks Coverage

### 🔗 Chainlink Integration (State-Changing)
- **Price Feeds**: Real-time asset pricing for dynamic NFT valuation
- **VRF (Verifiable Random Function)**: Provably fair randomness for NFT trait generation
- **Automation**: Automated price alerts and market triggers
- **Cross-Chain Communication**: CCIP-enabled price synchronization across chains

### 🤖 AI/Web3 Agent
- **Amazon Bedrock Integration**: AI-powered NFT analysis and recommendations
- **Intelligent Portfolio Management**: AI-driven investment insights
- **Natural Language Processing**: Chat-based Web3 interactions
- **Sentiment Analysis**: Social media sentiment tracking for collections

### 💰 DeFi Integration
- **Dynamic Pricing**: Chainlink-powered automatic price adjustments
- **Yield Strategies**: AI-recommended staking and liquidity provision
- **Gas Optimization**: Real-time gas price tracking and optimization
- **Portfolio Analytics**: Advanced DeFi position analysis

### 🎨 Tokenization
- **NFT Minting**: Dynamic NFT creation with Chainlink VRF traits
- **Fractional Ownership**: Token-based NFT fractionalization
- **Metadata Management**: IPFS-based metadata handling
- **Royalty Distribution**: Automated creator royalty systems

### 🌉 Cross-Chain Functionality
- **Multi-Chain Support**: Ethereum, Polygon, Avalanche, and more
- **Cross-Chain Price Feeds**: Chainlink CCIP price synchronization
- **Bridge Integration**: Seamless asset transfers between chains
- **Universal Wallet**: Single interface for multiple blockchain networks

## 🚀 Quick Start

### Prerequisites
- AWS Account with Lambda, API Gateway, and DynamoDB access
- Python 3.9+
- Valid API keys for supported services

### Environment Setup
```bash
# Blockchain APIs
MORALIS_API_KEY=your_moralis_api_key
ALCHEMY_API_KEY=your_alchemy_api_key
OPENSEA_API_KEY=your_opensea_api_key

# AI/ML Services
PERPLEXITY_API_KEY=your_perplexity_api_key
AWS_BEDROCK_REGION=us-east-1

# Chainlink Integration
CHAINLINK_NODE_URL=your_chainlink_node_url
VRF_COORDINATOR=your_vrf_coordinator_address

# Cross-Chain Configuration
SUPPORTED_CHAINS=ethereum,polygon,avalanche,arbitrum
```

### Deployment
```bash
# Create complete deployment package
python create_complete_package.py

# Deploy to AWS Lambda
aws lambda update-function-code \
  --function-name web3-ai-agent \
  --zip-file fileb://lambda_deployment_complete.zip
```

## 🔧 API Documentation

### Chainlink Endpoints

#### Get Real-Time Price Data
```bash
GET /chainlink/price?pair=ETH/USD
```
**Response:**
```json
{
  "success": true,
  "data": {
    "pair": "ETH/USD",
    "price": 2341.50,
    "timestamp": 1699123456,
    "feed_address": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
  }
}
```

#### Request VRF Randomness for NFT Traits
```bash
POST /chainlink/vrf/request
Content-Type: application/json

{
  "consumer_address": "0x1234...",
  "key_hash": "0xabcd...",
  "fee": "0.1",
  "seed": 12345
}
```

#### Create Price Automation (State-Changing)
```bash
POST /chainlink/automation/create
Content-Type: application/json

{
  "price_threshold": 2500.00,
  "asset_pair": "ETH/USD",
  "callback_address": "0x5678..."
}
```

#### Setup Dynamic NFT Pricing (State-Changing)
```bash
POST /chainlink/pricing/dynamic
Content-Type: application/json

{
  "nft_contract": "0x9abc...",
  "collection_id": "cool-cats"
}
```

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

## 💡 Code Examples

### Chainlink Price Feed Integration
```python
from chainlink_integration import get_chainlink_price, create_price_automation

# Get real-time ETH price
price_data = get_chainlink_price('ETH/USD')
print(f"ETH Price: ${price_data['data']['price']}")

# Create automated price alert
automation = create_price_automation(
    price_threshold=2500.00,
    asset_pair='ETH/USD',
    callback_address='0x1234...'
)
```

### AI-Powered NFT Analysis
```python
from bedrock_integration import bedrock_agent_handler

# Analyze NFT collection with AI
analysis = bedrock_agent_handler({
    'action': 'analyze_collection',
    'parameters': {
        'collection': 'bored-ape-yacht-club',
        'analysis_type': 'comprehensive'
    }
})
```

### Dynamic NFT Pricing with Chainlink
```python
from chainlink_integration import setup_dynamic_nft_pricing

# Enable dynamic pricing for NFT collection
pricing_setup = setup_dynamic_nft_pricing(
    nft_contract='0x9abc...',
    collection_id='my-nft-collection'
)
```

### Cross-Chain Price Synchronization
```python
from chainlink_integration import enable_cross_chain_sync

# Sync prices across multiple chains
sync_config = enable_cross_chain_sync(
    source_chain='ethereum',
    target_chains=['polygon', 'avalanche', 'arbitrum']
)
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │────│  API Gateway     │────│  Lambda Handler │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
              ┌────────▼────────┐              ┌────────▼────────┐              ┌────────▼────────┐
              │ Chainlink Feeds │              │  Amazon Bedrock │              │  Multi-Chain    │
              │ • Price Data    │              │  • AI Analysis  │              │  • Ethereum     │  
              │ • VRF Random    │              │  • NLP Chat     │              │  • Polygon      │
              │ • Automation    │              │  • Sentiment    │              │  • Avalanche    │
              │ • CCIP Sync     │              │  • Recommends   │              │  • Arbitrum     │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
```

## 🔐 Security Features

- **End-to-End Encryption**: All sensitive data encrypted in transit and at rest
- **API Rate Limiting**: Built-in protection against abuse
- **Wallet Security**: Non-custodial wallet integration with secure key management
- **Input Validation**: Comprehensive parameter validation and sanitization
- **Error Handling**: Graceful error handling with detailed logging

## 🎪 Hackathon Demonstration

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
