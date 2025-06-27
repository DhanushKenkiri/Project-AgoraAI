# AWS Bedrock Agent Deployment Guide

This guide explains how to deploy the NFT payment system as an AWS Bedrock agent.

## Package Contents

The `bedrock_deployment.zip` package includes all necessary files for the NFT payment system with Bedrock agent integration:

- Lambda handler with dual support for REST API and Bedrock agent requests
- Wallet login and NFT information functionality
- X402 payment processing
- Model Context Protocol (MCP) server implementation
- UI components for payment and wallet interfaces

## Deployment Steps

### 1. Create or Update Lambda Function

1. Log in to the AWS Management Console
2. Navigate to Lambda service
3. Create a new function or select your existing NFT payment function
4. Upload the `bedrock_deployment.zip` package:
   - Select "Upload from" -> ".zip file"
   - Click "Upload" and select the `bedrock_deployment.zip` file
   - Click "Save"

### 2. Configure Lambda Environment Variables

Set up the following environment variables in your Lambda function:

```
RESERVOIR_API_KEY=your_reservoir_key
OPENSEA_API_KEY=your_opensea_key
NFTGO_API_KEY=your_nftgo_key
MORALIS_API_KEY=your_moralis_key
ALCHEMY_API_KEY=your_alchemy_key
PERPLEXITY_API_KEY=your_perplexity_key
ETHERSCAN_API_KEY=your_etherscan_key

# Payment configuration
MAX_PAYMENT_AMOUNT=10.0
MIN_PAYMENT_AMOUNT=0.001
DEFAULT_CURRENCY=ETH
SUPPORTED_CURRENCIES=ETH,USDC,USDT,DAI
NETWORK=base-sepolia
TOKEN_CONTRACT_ADDRESS=your_token_contract_address
RPC_URL=https://sepolia.base.org
CDP_WALLET_APP_ID=your_cdp_app_id

# DynamoDB tables
TRANSACTION_TABLE_NAME=NFTPaymentTransactions
WALLET_SESSIONS_TABLE=NFTWalletSessions

# Resource pricing
RESOURCE_PRICES={"text_search": 0.001, "image_search": 0.002, "premium_content": 0.005}

# API Gateway domain (for UI popups)
API_GATEWAY_DOMAIN=your-api-id.execute-api.us-east-1.amazonaws.com
```

### 3. Configure Lambda Settings

1. Set the Handler to: `bedrock_agent_adapter.lambda_handler`
2. Set an appropriate timeout (recommended: 30 seconds)
3. Allocate sufficient memory (recommended: 1024+ MB)

### 4. Set Up API Gateway (for REST API access)

1. Create a new API Gateway or use an existing one
2. Create a new resource with `{proxy+}` path
3. Set up an "ANY" method that integrates with your Lambda function
4. Deploy the API to a stage (e.g., "prod")
5. Note the invocation URL

### 5. Set Up AWS Bedrock Agent

1. Navigate to the Amazon Bedrock console
2. Select "Agents" from the left navigation
3. Click "Create agent"
4. Configure the basic settings:
   - Name: `NFTPaymentAgent`
   - Description: `Agent for NFT payment processing and wallet interactions`
   - Model: Select an appropriate foundation model
5. Create an Action Group:
   - Name: `NFTPaymentActions`
   - Description: `Actions for NFT payments and wallet operations`
   - Schema definition: Use the OpenAPI schema defining your endpoints
   - API URL: Your Lambda function's API Gateway URL or ARN
6. In the Action Group, add the following functions:
   - `wallet_login`: Connect a wallet and create a session
   - `get_wallet_info`: Get wallet information
   - `get_wallet_nfts`: Get NFTs owned by a wallet
   - `process_payment`: Process a payment request
   - `check_transaction`: Check transaction status
   - `ui_payment_popup`: Open payment UI popup
   - `ui_wallet_popup`: Open wallet connection UI popup

### 6. Test the Bedrock Agent Integration

1. Navigate to the Lambda console
2. Select your function
3. Create a test event using one of the `bedrockAgentEvents` templates from `test.json`
4. Execute the test and verify the response format is correct
5. Test from the Bedrock agent console as well

## Usage Examples

### Wallet Login via Bedrock Agent

```json
{
  "messageVersion": "1.0",
  "requestBody": {
    "actionGroup": "NFTPaymentActions",
    "apiPath": "/wallet_login",
    "parameters": [
      {
        "name": "wallet_address",
        "value": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
      },
      {
        "name": "wallet_type",
        "value": "metamask"
      }
    ]
  }
}
```

### Get Wallet NFTs via Bedrock Agent

```json
{
  "messageVersion": "1.0",
  "requestBody": {
    "actionGroup": "NFTPaymentActions",
    "apiPath": "/get_wallet_nfts",
    "parameters": [
      {
        "name": "wallet_address",
        "value": "0x5e7eE927ce269023794b231465Ed53D66cbD564b"
      }
    ]
  }
}
```

### Process Payment via Bedrock Agent

```json
{
  "messageVersion": "1.0",
  "requestBody": {
    "actionGroup": "NFTPaymentActions",
    "apiPath": "/process_payment",
    "parameters": [
      {
        "name": "amount",
        "value": "0.005"
      },
      {
        "name": "currency",
        "value": "ETH"
      },
      {
        "name": "payment_reason",
        "value": "NFT analysis"
      },
      {
        "name": "wallet_address",
        "value": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
      }
    ]
  }
}
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all required environment variables are set.
2. **Incorrect Handler**: Verify the handler is set to `bedrock_agent_adapter.lambda_handler`.
3. **Permissions**: Check that Lambda has necessary permissions (IAM role).
4. **Resource Limits**: Increase Lambda memory if you encounter resource constraints.
5. **Response Format Errors**: Ensure your Bedrock agent schema matches the actual responses.

### Checking Logs

- Check CloudWatch logs for errors and debug information
- The Lambda function logs detailed information about requests and errors

### Testing Validation

- Test webhook validation by sending a GET request to `/validate` with the `x-amzn-bedrock-validation-token` header

## Next Steps

- Consider setting up CloudWatch alarms for error monitoring
- Implement more advanced error handling for specific agent scenarios
- Add custom agent instructions in the Bedrock console for optimal user interaction
