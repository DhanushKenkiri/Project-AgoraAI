# CDP Wallet Connection and X402 Payment Setup Guide

This guide explains how to set up and implement CDP wallet connection with signature verification and X402 payment processing in your Lambda-based NFT payment system.

## Prerequisites

1. An AWS Lambda function (already deployed)
2. API Gateway configuration for RESTful endpoints
3. CDP Wallet App ID (from Coinbase Developer Platform)
4. X402 configuration (network, token contract address, etc.)

## Backend Setup (AWS Lambda)

### 1. Configure Environment Variables

Add these environment variables to your Lambda function:

```
CDP_WALLET_APP_ID=your_cdp_app_id_here
CDP_API_ENDPOINT=https://api.cdp.io
NETWORK=base-sepolia  # Use appropriate network
TOKEN_CONTRACT_ADDRESS=0x...  # Contract address for token payments
RPC_URL=https://sepolia.base.org  # RPC endpoint for the network
```

### 2. Verify Files

Ensure the following files are included in your Lambda deployment package:

- `cdp_wallet_handler.py` - CDP wallet connection functions
- `cdp_wallet_x402_integration.py` - Unified endpoint handler
- `x402_payment_handler.py` - X402 payment protocol implementation
- `utils/x402_processor.py` - Utility for X402 payment processing
- `lambda_handler.py` - Main entry point with route handling

### 3. Test the Lambda Function Locally

```bash
python test_cdp_x402_integration.py
```

## Frontend Integration

### 1. Include Required JavaScript Files

```html
<!-- CDP Wallet and X402 Integration -->
<script src="/static/cdp_wallet_integration.js"></script>
<script src="/static/x402_client.js"></script>
```

### 2. Initialize the CDP Wallet Handler

```javascript
// Initialize CDP wallet handler with your API endpoint
const walletHandler = new CDPWalletHandler('https://your-api-gateway-url');

// Initialize wallet connection
await walletHandler.initialize();
```

### 3. Connect to CDP Wallet

```javascript
// Connect wallet when user clicks connect button
document.getElementById('connect-wallet').addEventListener('click', async () => {
  try {
    const result = await walletHandler.connectWallet();
    if (result.success) {
      console.log('Wallet connected:', result.walletAddress);
      // Update UI to show connected state
    }
  } catch (error) {
    console.error('Wallet connection error:', error);
  }
});
```

### 4. Sign Messages with CDP Wallet

```javascript
// Sign a message with the connected wallet
async function signMessage(message) {
  try {
    const signature = await walletHandler.signMessage(message);
    return signature;
  } catch (error) {
    console.error('Signature error:', error);
    return null;
  }
}
```

### 5. Make X402 Payments

```javascript
// Process payment when user clicks pay button
document.getElementById('pay-button').addEventListener('click', async () => {
  try {
    // 1. Get payment requirements
    const resource = '/premium-content/123';
    const requirements = await walletHandler.getPaymentRequirements(resource);
    
    // 2. Process payment
    const paymentResult = await walletHandler.processPayment(requirements, resource);
    
    if (paymentResult.success) {
      console.log('Payment successful');
      // Access the protected resource
      const content = await walletHandler.getProtectedResource(resource);
      // Update UI with the content
    }
  } catch (error) {
    console.error('Payment error:', error);
  }
});
```

## API Endpoints

The integration provides these RESTful endpoints:

### CDP Wallet Endpoints

- `POST /cdp/wallet/connect` - Connect a CDP wallet
- `GET /cdp/wallet/status` - Check wallet connection status
- `POST /cdp/wallet/disconnect` - Disconnect a CDP wallet
- `POST /cdp/wallet/sign` - Sign a message with the wallet

### X402 Payment Endpoints

- `GET /x402/payment/requirements` - Get payment requirements for a resource
- `POST /x402/payment/process` - Process an X402 payment
- `GET /x402/protected-resource/{resource_id}` - Access a protected resource after payment

## Testing the Integration

1. Use the demo page at `/templates/cdp_wallet_demo.html`
2. Connect your CDP wallet
3. Sign a test message
4. Test payment for a protected resource

## Troubleshooting

### Common Issues

1. **Wallet Connection Fails**
   - Check that CDP_WALLET_APP_ID is correctly set
   - Verify the user has CDP wallet extension installed

2. **Signature Verification Fails**
   - Ensure the message format matches what's expected
   - Check for any encoding/decoding issues

3. **X402 Payment Fails**
   - Verify network configuration matches your token
   - Check RPC_URL is accessible from Lambda
   - Ensure TOKEN_CONTRACT_ADDRESS is correct

## Security Best Practices

1. Always verify signatures server-side
2. Implement rate limiting for wallet connection attempts
3. Use session tokens with appropriate expiration
4. Store sensitive keys in AWS Secrets Manager
5. Validate and sanitize all user input

## Additional Resources

- [CDP Wallet Documentation](https://docs.cdp.io)
- [X402 Protocol Reference](https://x402.dev/docs)
- [Ethereum Signature Verification Guide](https://ethereum.org/en/developers/docs/apis/json-rpc/#eth_sign)
