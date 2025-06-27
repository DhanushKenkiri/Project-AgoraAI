# NFT Payment Lambda Handler

This repository contains an AWS Lambda handler for NFT payment processing, CDP wallet integration, and X402 payment protocol support.

## Features

- Multiple NFT API integrations (Moralis, Alchemy, NFTScan, OpenSea, NFTGo, Reservoir)
- CDP wallet connection with signature verification
- X402 payment protocol integration
- NFT data aggregation with web search fallback
- AI-assisted recommendations and sentiment analysis
- Comprehensive REST API endpoints

## Deployment Instructions

### 1. Create the Deployment Package

```bash
# Create the complete deployment package
python create_complete_package.py
```

This will create a file named `lambda_deployment_complete.zip` that contains all necessary code.

### 2. Upload to AWS Lambda

1. Go to the AWS Lambda console
2. Create a new function or select an existing one
3. Upload the `lambda_deployment_complete.zip` file
4. Set the handler to `lambda_handler.lambda_handler`
5. Configure environment variables for API keys (see below)

### 3. Configure API Keys

Set the following environment variables in your Lambda function:

```
MORALIS_API_KEY=your_moralis_api_key
ALCHEMY_API_KEY=your_alchemy_api_key
NFTSCAN_API_KEY=your_nftscan_api_key
OPENSEA_API_KEY=your_opensea_api_key
NFTGO_API_KEY=your_nftgo_api_key
RESERVOIR_API_KEY=your_reservoir_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```

### 4. Configure API Gateway

1. Create a new REST API in API Gateway
2. Create resources for all the endpoints in `lambda_handler.py`
3. Set up the integration with your Lambda function
4. Enable CORS if needed
5. Deploy the API

## Testing

### Local Testing

```bash
# Test the Lambda handler locally
python test_lambda_package.py
```

### Endpoint Testing

Once deployed, you can test the following endpoints:

#### CDP Wallet Endpoints

- `POST /cdp/wallet/connect` - Connect a wallet with signature verification
- `GET /cdp/wallet/status` - Check wallet connection status
- `POST /cdp/wallet/disconnect` - Disconnect a wallet

#### X402 Payment Endpoints

- `GET /x402/payment/requirements` - Get payment requirements for a resource
- `GET /x402/resource/{resource_id}` - Get resource details
- `POST /x402/payment/submit` - Submit a payment

#### NFT Data Endpoints

- `GET /?address={contract_address}&id={token_id}` - Get NFT data
- `GET /wallet/nfts?wallet_address={address}` - Get NFTs owned by a wallet
- `GET /nft/sentiment?address={contract_address}` - Get NFT sentiment analysis

## Troubleshooting

If you encounter any issues, check the following:

1. CloudWatch logs for error messages
2. Ensure all required files are included in the deployment package
3. Verify all environment variables are set correctly
4. Check API Gateway configuration for proper routes and methods
5. Ensure your Lambda function has appropriate IAM permissions

## License

[MIT License](LICENSE)
