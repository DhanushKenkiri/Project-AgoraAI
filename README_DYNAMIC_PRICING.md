# NFT Payment System with Dynamic Pricing

This system enables NFT-based payments with dynamic pricing based on real-time NFT floor prices and collection metrics. It integrates with the X402 payment protocol and CDP Wallet for secure, non-custodial transactions.

## Architecture

The system consists of:

1. AWS Lambda functions for payment processing
2. DynamoDB tables for transaction and session storage
3. NFT price oracle for real-time pricing
4. AI agent integration for interactive payments
5. CloudFormation stack for infrastructure deployment

## Setup Instructions

### 1. Configure AWS Credentials

Ensure you have AWS credentials with appropriate permissions:

```bash
aws configure
```

### 2. Set up Secrets Manager

Create a secret in AWS Secrets Manager with the following structure:

```json
{
  "NETWORK": "base-sepolia",
  "TOKEN_CONTRACT_ADDRESS": "0xYourTokenContractAddress", 
  "RPC_URL": "https://sepolia.base.org",

  "CDP_WALLET_APP_ID": "your-cdp-wallet-app-id",

  "X402_API_KEY": "your-x402-api-key",
  "X402_API_SECRET": "your-x402-api-secret",
  "X402_MERCHANT_ID": "your-x402-merchant-id",

  "RESERVOIR_API_KEY": "your-reservoir-api-key",
  "OPENSEA_API_KEY": "your-opensea-api-key",
  "NFTGO_API_KEY": "your-nftgo-api-key",

  "RESOURCE_PRICES": "{\"api/nft/details\":{\"amount\":0.001,\"currency\":\"ETH\"},\"api/collection\":{\"amount\":0.005,\"currency\":\"ETH\"}}"
}
```

### 3. Deploy the Stack

Run the deployment script:

```bash
python deploy_dynamic_pricing.py --stack-name nft-payment-stack --environment dev --secrets-arn <your-secret-arn>
```

### 4. Testing the Dynamic Pricing

Use the test script to verify your setup:

```bash
python test_local.py
```

## Using Dynamic Pricing in Your Agent

The system will automatically calculate appropriate prices based on:
- NFT collection floor price
- Collection trading volume
- Data type requested (basic, advanced, premium)

### Example Agent Integration

```python
# Request payment options for a premium NFT collection analysis
response = lambda_client.invoke(
    FunctionName='PaymentHandler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'get_payment_options',
        'payload': {
            'resource_path': 'api/collection/analytics',
            'collection_address': '0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d',
            'data_type': 'premium'
        }
    })
)

# Parse the response which includes payment buttons the agent can present
payment_options = json.loads(response['Payload'].read().decode('utf-8'))

# When user clicks a payment button
payment_response = lambda_client.invoke(
    FunctionName='PaymentHandler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'process_payment_action',
        'payload': {
            'button_action': 'initiate_payment',
            'button_payload': {
                'wallet_address': '0xUserWalletAddress',
                'amount': payment_options['amount'],
                'currency': payment_options['currency'],
                'resource': payment_options['resource'],
                'transaction_id': payment_options['transaction_id']
            }
        }
    })
)
```

## API Reference

### Lambda Functions

- `agent_payment_handler.lambda_handler` - Main entry point for agent integrations
- `x402_payment_handler.lambda_handler` - Handles X402 protocol payment verification

### Dynamic Pricing Features

- `get_payment_options` - Returns payment buttons with dynamically calculated prices
- `get_nft_price` - Gets real-time NFT floor price data
- `initiate_payment` - Processes payment automatically in the background

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| RESERVOIR_API_KEY | API key for Reservoir NFT data | "" |
| OPENSEA_API_KEY | API key for OpenSea NFT data | "" |
| NFTGO_API_KEY | API key for NFTGo NFT data | "" |
| DEFAULT_CURRENCY | Default payment currency | "ETH" |
| SUPPORTED_CURRENCIES | Available payment currencies | "ETH,USDC,USDT,DAI" |

## Monitoring and Maintenance

- CloudWatch alarms will notify of payment errors
- Check Lambda logs for price fetch failures
- Update API keys in Secrets Manager as needed

## License

Copyright (c) 2025
