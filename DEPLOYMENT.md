# NFT Payment Lambda Deployment Guide

This guide explains how to deploy the NFT payment Lambda function to AWS.

## Prerequisites

1. AWS CLI installed and configured
2. Python 3.7+ installed

## Deployment Steps

### 1. Create Lambda Package

Run the following command to create the Lambda deployment package:

```bash
python create_lambda_package.py
```

This will create a `lambda_deployment.zip` file containing all the necessary files for the Lambda function.

### 2. Deploy to AWS Lambda

#### Option 1: Deploy using AWS CLI

```bash
aws lambda update-function-code \
    --function-name YOUR_FUNCTION_NAME \
    --zip-file fileb://lambda_deployment.zip
```

#### Option 2: Deploy using deploy_lambda.py script

First, install boto3:

```bash
pip install boto3
```

Then, create an environment variables JSON file (example provided in `example_env_vars.json`).

Finally, run the deployment script:

```bash
python deploy_lambda.py --function YOUR_FUNCTION_NAME --region us-east-1 --env-file example_env_vars.json
```

### Environment Variables

The following environment variables should be set in your AWS Lambda function:

| Variable | Description | Example |
|----------|-------------|---------|
| ENVIRONMENT | Environment name | prod |
| RESERVOIR_API_KEY | API key for Reservoir | your_api_key |
| OPENSEA_API_KEY | API key for OpenSea | your_api_key |
| NFTGO_API_KEY | API key for NFTGO | your_api_key |
| MORALIS_API_KEY | API key for Moralis | your_api_key |
| ALCHEMY_API_KEY | API key for Alchemy | your_api_key |
| ETHERSCAN_API_KEY | API key for Etherscan | your_api_key |
| PERPLEXITY_API_KEY | API key for Perplexity | your_api_key |
| MAX_PAYMENT_AMOUNT | Maximum payment amount | 10.0 |
| MIN_PAYMENT_AMOUNT | Minimum payment amount | 0.001 |
| DEFAULT_CURRENCY | Default currency | ETH |
| SUPPORTED_CURRENCIES | Supported currencies | ETH,USDC,USDT,DAI |
| NETWORK | Blockchain network | base-sepolia |
| TOKEN_CONTRACT_ADDRESS | X402 token contract address | 0x123... |
| RPC_URL | RPC URL for blockchain | https://sepolia.base.org |
| CDP_WALLET_APP_ID | CDP Wallet app ID | your_app_id |
| TRANSACTION_TABLE_NAME | DynamoDB table for transactions | NFTPaymentTransactions-prod |
| WALLET_SESSIONS_TABLE | DynamoDB table for wallet sessions | NFTWalletSessions-prod |
| RESOURCE_PRICES | JSON string of resource prices | {"text_search": 0.001} |

## Troubleshooting

- If you encounter issues with API keys, make sure they are correctly set in the environment variables.
- For any Lambda deployment issues, check CloudWatch logs for errors.
