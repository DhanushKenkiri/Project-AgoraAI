# Dynamic NFT Pricing System - Setup Guide

This guide explains how to set up and use the dynamic NFT pricing system with your Lambda function using environment variables.

## Quick Start

1. **Set Environment Variables in Lambda**

Add these environment variables to your Lambda function:

```
RESERVOIR_API_KEY=your-reservoir-api-key
OPENSEA_API_KEY=your-opensea-api-key
NFTGO_API_KEY=your-nftgo-api-key
```

2. **Deploy Updated Code**

Ensure the latest code is deployed to your Lambda function, including:
- `dynamic_pricing_agent.py`
- Updated `agent_payment_handler.py`
- Modified `secure_payment_config.py`

3. **Test It Out**

You can test locally by:

```powershell
# Set environment variables
. .\set_env_vars.ps1

# Run the test script
python test_local.py
```

## Example API Usage

### Get Dynamic Price for NFT Collection

```json
{
  "action": "get_payment_options",
  "payload": {
    "resource_path": "api/collection/analytics",
    "collection_address": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
    "data_type": "premium"
  }
}
```

### Get NFT Floor Price Directly

```json
{
  "action": "get_nft_price",
  "payload": {
    "collection_address": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d"
  }
}
```

### Process Payment with NFT Data

```json
{
  "action": "initiate_payment",
  "payload": {
    "wallet_address": "0xYourWalletAddress",
    "amount": 0.05,
    "currency": "ETH",
    "resource": "api/collection/analytics",
    "collection_address": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
    "transaction_id": "tx_12345"
  }
}
```

## API Keys

- **Reservoir API** (https://docs.reservoir.tools/reference/overview): The primary source for NFT floor prices
- **OpenSea API** (https://docs.opensea.io/reference/api-overview): Used as a fallback
- **NFTGo API** (https://developer.nftgo.io/docs): Used as a second fallback

You'll need to obtain API keys from these services to get the most accurate NFT pricing.

## Testing the API Keys

Run this command to test if your API keys are working:

```powershell
python -c "import requests; print(requests.get('https://api.reservoir.tools/collections/v5?limit=1', headers={'x-api-key': 'your-reservoir-api-key'}).json())"
```

## Updating Lambda Environment Variables

You can use the provided script to add the necessary environment variables to your Lambda function:

```powershell
python update_lambda_env.py --function YourLambdaFunctionName --region us-east-1
```

This will add placeholder variables that you can then update in the AWS Console with your actual API keys.
