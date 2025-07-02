# NFT Payment Lambda Handler

A comprehensive AWS Lambda application for NFT data analysis, wallet integration, and X402 payment processing.

## Features

- **Multi-API NFT Data Fetching**: Integrates with Moralis, Alchemy, NFTScan, OpenSea, NFTGo, and Reservoir APIs
- **CDP Wallet Integration**: Secure crypto wallet connections via Coinbase Developer Platform
- **X402 Payment Protocol**: Micropayment support for NFT transactions
- **AI-Powered Analysis**: Amazon Bedrock integration for intelligent NFT insights
- **Real-time Gas Tracking**: Ethereum gas price monitoring
- **Social Sentiment Analysis**: Community sentiment tracking for NFT collections
- **Image Processing**: NFT image upload and retrieval functionality

## Quick Start

### Prerequisites

- AWS Account with Lambda, API Gateway, and DynamoDB access
- Python 3.9+
- Valid API keys for supported services

### 1. Environment Setup

Set the following environment variables in your Lambda function:

```bash
# Required API Keys
MORALIS_API_KEY=your_moralis_api_key
ALCHEMY_API_KEY=your_alchemy_api_key
NFTSCAN_API_KEY=your_nftscan_api_key
OPENSEA_API_KEY=your_opensea_api_key
NFTGO_API_KEY=your_nftgo_api_key
RESERVOIR_API_KEY=your_reservoir_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key

# Optional Configuration
DEFAULT_CHAIN=ethereum
LOG_LEVEL=INFO
```

### 2. Deployment

#### Option A: Direct Upload to Lambda

1. Create deployment package:
   ```bash
   python create_complete_package.py
   ```

2. Upload `lambda_deployment_complete.zip` to your Lambda function

3. Set handler to: `lambda_handler.lambda_handler`

#### Option B: Using AWS CLI

```bash
aws lambda update-function-code \
  --function-name your-function-name \
  --zip-file fileb://lambda_deployment_complete.zip
```

### 3. API Gateway Setup

Create the following endpoints in API Gateway:

```
GET  /nft/data?address={contract}&id={token_id}
POST /wallet/login
GET  /wallet/status
POST /payment/init
GET  /blockchain/gas
POST /search/web
GET  /nft/sentiment?address={contract}
```

## Usage Examples

### Fetch NFT Data

```bash
curl "https://your-api-gateway-url/nft/data?address=0x1234...&id=1"
```

### Connect Wallet

```bash
curl -X POST "https://your-api-gateway-url/wallet/login" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234...", "wallet_type": "metamask"}'
```

### Initialize Payment

```bash
curl -X POST "https://your-api-gateway-url/payment/init" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234...", "amount": "0.01", "currency": "ETH"}'
```

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
