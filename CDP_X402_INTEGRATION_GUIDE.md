# CDP Wallet and X402 Payment Integration Guide

This guide explains how to integrate CDP wallet connections and X402 payments with your NFT payment system.

## Table of Contents

1. [Overview](#overview)
2. [Backend Setup](#backend-setup)
3. [Frontend Integration](#frontend-integration)
4. [Testing the Integration](#testing-the-integration)
5. [Troubleshooting](#troubleshooting)

## Overview

This integration allows users to:

1. Connect their CDP wallets to your application
2. Sign messages to verify wallet ownership
3. Make X402 payments for premium content or services
4. Access paid resources using the X402 protocol

## Backend Setup

### 1. Environment Variables

Set these environment variables in your Lambda function:

```
CDP_WALLET_APP_ID=your-cdp-wallet-app-id
CDP_API_ENDPOINT=https://api.cdp.io
NETWORK=base-sepolia  # or base, ethereum, ethereum-sepolia
TOKEN_CONTRACT_ADDRESS=your-token-contract-address
RPC_URL=https://sepolia.base.org
```

### 2. Files Required

Ensure the following files are included in your Lambda deployment:

- `cdp_wallet_handler.py`: Core CDP wallet functionality
- `cdp_wallet_connector.js`: Client-side CDP connector
- `cdp_wallet_x402_integration.py`: Integration with wallet login and X402 payments
- `x402_payment_handler.py`: X402 payment protocol handler
- `x402_client.js`: Client-side X402 payment header generation

### 3. DynamoDB Tables

Create DynamoDB tables for session persistence and transaction tracking:

```yaml
WalletSessions:
  Type: AWS::DynamoDB::Table
  Properties:
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: session_id
        AttributeType: S
    KeySchema:
      - AttributeName: session_id
        KeyType: HASH

TransactionTable:
  Type: AWS::DynamoDB::Table
  Properties:
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: transaction_id
        AttributeType: S
    KeySchema:
      - AttributeName: transaction_id
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: expiration
      Enabled: true
```

### 4. API Gateway Setup

Create the following API endpoints in API Gateway:

- **CDP Wallet Endpoints**:
  - `POST /cdp/wallet/connect`: Connect a CDP wallet
  - `GET /cdp/wallet/status`: Check wallet connection status
  - `POST /cdp/wallet/disconnect`: Disconnect a wallet

- **X402 Payment Endpoints**:
  - `GET /x402/payment/requirements`: Get payment requirements for a resource
  - `POST /x402/payment/submit`: Submit a payment for a resource
  - `GET /x402/resource/{resourceId}`: Access a paid resource

Configure CORS for these endpoints to allow access from your frontend application.

## Frontend Integration

### 1. Include the JavaScript Files

Add these files to your frontend application:

```html
<script src="cdp_wallet_integration.js"></script>
```

### 2. Initialize the Wallet Handler

```javascript
const apiEndpoint = 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod';
const cdpWallet = new CDPWalletHandler(apiEndpoint);

// Initialize on page load
window.addEventListener('load', async () => {
    await cdpWallet.initialize();
});
```

### 3. Connect Wallet

```javascript
async function connectWallet() {
    const walletAddress = '0x1234567890abcdef1234567890abcdef12345678'; // User's wallet address
    const result = await cdpWallet.connectWallet(walletAddress);
    
    if (result.success) {
        console.log('Wallet connected:', result.walletAddress);
    } else {
        console.error('Failed to connect wallet:', result.error);
    }
}
```

### 4. Sign Messages

```javascript
async function signMessage() {
    const message = 'I am signing this message to verify wallet ownership';
    const result = await cdpWallet.signMessage(message);
    
    if (result.success) {
        console.log('Signature:', result.signature);
    } else {
        console.error('Failed to sign message:', result.error);
    }
}
```

### 5. Make X402 Payments

```javascript
async function makePayment() {
    // 1. Get payment requirements
    const resourceId = 'premium-content-123';
    const requirementsResult = await cdpWallet.getPaymentRequirements(resourceId);
    
    if (requirementsResult.success) {
        // 2. Make payment
        const amount = requirementsResult.requirements.maxAmountRequired;
        const currency = requirementsResult.requirements.asset;
        const paymentResult = await cdpWallet.makePayment(resourceId, amount, currency);
        
        if (paymentResult.success) {
            console.log('Payment successful:', paymentResult.transactionId);
            
            // 3. Access the paid resource
            const accessResult = await cdpWallet.accessResource(resourceId);
            if (accessResult.success) {
                console.log('Resource accessed:', accessResult.resource);
            }
        }
    }
}
```

## Testing the Integration

### 1. Test Environment

For testing, use the Base Sepolia testnet with test ETH. You can get test tokens from:
- Base Sepolia Faucet: https://www.coinbase.com/faucets/base-sepolia-faucet

### 2. Test Transactions

Test by sending small amounts such as 0.001 ETH for your X402 payments.

### 3. Test Flow

1. Connect wallet
2. Sign a message to verify ownership
3. Check payment requirements for a resource
4. Make a payment
5. Access the paid resource

## Troubleshooting

### Common Issues

1. **Error: "contractAddress is required for NFT data endpoints"**
   - Ensure you're providing a valid contract address in your API calls
   - Check that the TOKEN_CONTRACT_ADDRESS environment variable is set

2. **Wallet Connection Failing**
   - Verify the user's wallet address is valid
   - Check that the CDP_WALLET_APP_ID environment variable is set correctly

3. **Payment Verification Issues**
   - Make sure the payment header format matches the X402 protocol specification
   - Verify that the wallet contains sufficient funds for the payment

4. **Resource Access Denied After Payment**
   - Check that the payment header is being sent correctly in the request
   - Verify that the transaction was successful and confirmed on-chain

### Debugging Tips

1. Enable DEBUG level logging for more detailed information:
```python
logging.basicConfig(level=logging.DEBUG)
```

2. Check CloudWatch Logs for your Lambda function to see detailed error messages

3. Use the transaction IDs to track payment status in your DynamoDB table

## Resources

- [CDP Wallet Documentation](https://docs.cdp.io)
- [X402 Payment Protocol Specification](https://x402.dev/docs)
- [Base Network Documentation](https://docs.base.org)
