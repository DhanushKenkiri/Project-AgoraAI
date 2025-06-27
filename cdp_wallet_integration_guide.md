# CDP Wallet Integration Guide for Bedrock Agents

This step-by-step guide explains how to integrate CDP wallet payments with your Amazon Bedrock agent using the Lambda function handler.

## 1. Prerequisites

- Amazon Bedrock agent already set up
- AWS Lambda function deployed with the payment handler code
- DynamoDB tables for transaction and wallet session tracking
- AWS Secrets Manager secret containing payment configuration

## 2. Configure Environment Variables

Set the following environment variables in your Lambda function:

```
SECRETS_MANAGER_ARN=arn:aws:secretsmanager:region:account-id:secret:your-secret-name
AWS_REGION=us-east-1  # Or your preferred region
TRANSACTION_TABLE_NAME=NFTPaymentTransactions
WALLET_SESSIONS_TABLE=NFTWalletSessions
DEFAULT_CURRENCY=ETH
SUPPORTED_CURRENCIES=ETH,USDC,USDT,DAI
ENVIRONMENT=prod  # or dev, stage, etc.
```

## 3. Set Up Secrets in AWS Secrets Manager

Create a secret in AWS Secrets Manager with the following structure:

```json
{
  "NETWORK": "base-sepolia",
  "TOKEN_CONTRACT_ADDRESS": "0x1234abcd...",
  "RPC_URL": "https://sepolia.base.org",
  "CDP_WALLET_APP_ID": "your-cdp-wallet-app-id",
  "RESERVOIR_API_KEY": "your-reservoir-api-key",
  "OPENSEA_API_KEY": "your-opensea-api-key",
  "NFTGO_API_KEY": "your-nftgo-api-key",
  "RESOURCE_PRICES": "{\"premium-nft-data\": {\"amount\": 0.001, \"currency\": \"ETH\"}, \"/analytics/whales\": {\"amount\": 0.005, \"currency\": \"ETH\"}}"
}
```

## 4. Configure DynamoDB Tables

### Transaction Table Structure

Create a DynamoDB table with the following attributes:
- Partition key: `payment_id` (String)
- Sort key: None
- Additional fields:
  - `tx_hash` (String)
  - `from_address` (String)
  - `to_address` (String)
  - `amount` (String)
  - `currency` (String)
  - `timestamp` (Number)
  - `network` (String)
  - `status` (String)
  - `created_at` (Number)

### Wallet Sessions Table Structure

Create a DynamoDB table with the following attributes:
- Partition key: `wallet_address` (String)
- Sort key: None
- Additional fields:
  - `session_token` (String)
  - `state` (String)
  - `created_at` (Number)
  - `expires_at` (Number)
  - `status` (String)

## 5. Integration Steps with Bedrock Agent

### Step 1: Create Action Group

Create an action group in your Bedrock Agent with the following API schema:

```yaml
openapi: 3.0.0
info:
  title: NFT Payment API
  version: 1.0.0
  description: API for handling NFT payments and wallet connections
paths:
  /payments:
    post:
      operationId: initiatePayment
      summary: Initiate a payment to a user-specified address
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - amount
                - wallet_address
              properties:
                amount:
                  type: string
                  description: Payment amount
                currency:
                  type: string
                  description: Payment currency (ETH, USDC, etc.)
                wallet_address:
                  type: string
                  description: User's wallet address
                payment_reason:
                  type: string
                  description: Reason for payment
      responses:
        '200':
          description: Payment initiated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  payment_id:
                    type: string
                  payment_url:
                    type: string
                  qr_code:
                    type: string
                  amount:
                    type: string
                  currency:
                    type: string
  /wallet/connect:
    post:
      operationId: connectWallet
      summary: Generate a wallet connection URL or store wallet connection
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                wallet_address:
                  type: string
                  description: User's wallet address (if already connected)
                state:
                  type: string
                  description: State parameter for security verification
      responses:
        '200':
          description: Wallet connection successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  connection_url:
                    type: string
                  state:
                    type: string
                  qr_data:
                    type: string
  /payments/status:
    get:
      operationId: checkPaymentStatus
      summary: Check the status of a payment
      parameters:
        - name: payment_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Payment status retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  status:
                    type: string
                  payment_id:
                    type: string
                  transaction_hash:
                    type: string
                  explorer_url:
                    type: string
```

### Step 2: Connect Action Group to Lambda Function

1. In the Bedrock Agent console, select your action group
2. Under "Lambda function", select your deployed Lambda function
3. Save the action group configuration

### Step 3: Add Agent Prompts

Add the following sample prompts to your agent to handle payment flows:

#### Payment Request Prompt
```
When a user requests premium NFT data that requires payment, explain that payment is required and offer payment options.

User: Can I see the whale movement analysis for Azuki?
Agent: I can provide detailed whale movement analysis for Azuki, but this requires a payment of 0.005 ETH (or approximately $12.50 in USDC).

[Pay 0.005 ETH] [Pay with USDC] [Pay with USDT]

Would you like to proceed with one of these payment options?
```

#### Wallet Request Prompt
```
When a user agrees to pay, ask for their wallet address.

User: I'll pay with USDC.
Agent: Great choice! For the payment of 12.50 USDC, I'll need your wallet address. This is where you'll receive any potential benefits or returns from this transaction.

Please provide your wallet address.
```

#### Payment Processing Prompt
```
Once you have the wallet address, initiate payment using the Action Group API and inform the user.

User: My wallet is 0x1234abcd...
Agent: Thank you. I'll process the payment of 12.50 USDC to wallet address 0x1234abcd...

Payment has been initiated and is processing in the background. You'll receive a notification once the transaction completes.

While we wait, is there any specific aspect of the whale movement analysis you're particularly interested in?
```

## 6. Testing the Integration

1. Test wallet connection:
   - Use the `/wallet/connect` endpoint without a wallet_address to generate a connection URL
   - Scan the QR code with a CDP wallet app
   - Call `/wallet/connect` again with the wallet_address to store the connection

2. Test payment flow:
   - Call the `/payments` endpoint with amount, currency, wallet_address
   - Check payment status with `/payments/status?payment_id={id}`
   - Verify that transaction records are created in DynamoDB

## 7. Error Handling

Implement error handling for these common scenarios:

1. Invalid wallet address format
2. Payment amount outside allowed range
3. Unsupported currency
4. Network connectivity issues
5. Payment verification failures

Add appropriate error messages in your agent prompts to handle these scenarios gracefully.

## 8. Security Considerations

1. Implement rate limiting on payment endpoints
2. Use IAM roles with least privilege for Lambda execution
3. Encrypt sensitive data in transit and at rest
4. Implement input validation for all payment parameters
5. Set up monitoring and alerting for unusual payment activity

## 9. Production Readiness Checklist

- [ ] Comprehensive testing with multiple wallet types and payment methods
- [ ] Error handling for all edge cases
- [ ] Logging and monitoring setup
- [ ] Performance optimization for high concurrency
- [ ] Security audit completed
- [ ] User documentation and guides prepared
- [ ] Backup and recovery procedures documented
- [ ] Compliance with relevant regulations verified
