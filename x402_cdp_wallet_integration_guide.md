# X402 and CDP Wallet Integration Guide

This document provides detailed instructions for obtaining the necessary API credentials and integrating with Coinbase's X402 payment protocol and CDP Wallet for your NFT payment system.

## Understanding X402 and CDP Wallet

### X402 Payment Protocol

X402 is an open standard payments protocol built on HTTP that enables internet-native payments with features like:
- Low minimums (as little as $0.001)
- No percentage-based fees
- 2-second settlement times
- Chain and token agnostic architecture
- Designed for programmatic payments

### CDP Wallet

CDP (Coinbase Developer Platform) Wallet is Coinbase's wallet integration solution that allows your application to connect with users' crypto wallets for payment processing.

## Setting Up X402 Integration

### 1. X402 Implementation Options

The X402 protocol is currently in development and offers several integration paths:

#### Option 1: Self-hosted Implementation

You can run your own X402 facilitator server to handle payment verification and settlement:

1. Clone the X402 repository:
   ```bash
   git clone https://github.com/coinbase/x402.git
   ```

2. Navigate to the implementation directory for your preferred language:
   ```bash
   cd x402/typescript  # or python, go, java
   ```

3. Install dependencies and build:
   ```bash
   # For TypeScript implementation
   pnpm install
   pnpm build
   ```

4. Configure your server implementation:
   - Set up your Ethereum wallet address that will receive payments
   - Configure your preferred network (Base-Sepolia for testing is recommended)

#### Option 2: Use Existing Facilitator Server

As the ecosystem develops, official facilitator servers may become available. Check the [X402 ecosystem page](https://x402.org/ecosystem) for available services.

### 2. X402 Integration Configuration

For the payment server implementation, create a `.env` file with the following:

```
# Server configuration
PORT=3000
# Your Ethereum address to receive payments
PAYMENT_ADDRESS=0xYourEthereumAddressHere
# Network configuration (base-sepolia for testing)
NETWORK=base-sepolia
```

### 3. Resource Server Implementation

For an API that requires payment:

```javascript
// Example Express.js server with X402 middleware
import express from 'express';
import { paymentMiddleware } from '@x402/express';

const app = express();

// Add payment middleware to specific endpoints
app.use(
  paymentMiddleware("0xYourEthereumAddress", { 
    "/premium-nft-data": "$0.01",
    "/premium-nft-art": "$0.05" 
  })
);

// Your API endpoint that requires payment
app.get('/premium-nft-data', (req, res) => {
  // This endpoint will only be accessible after payment
  res.json({
    premium_data: "Your exclusive NFT data here"
  });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

## Setting Up CDP Wallet Integration

Since CDP Wallet's API access might not be publicly available yet, we'll outline the general approach based on our understanding:

### 1. Connecting CDP Wallet

The current implementation in your code creates a CDP Wallet connection URL:

```python
def create_wallet_connection_url(self, callback_url=None, state=None):
    """Create a URL for connecting a CDP wallet"""
    if not state:
        state = str(uuid.uuid4())
        
    # Create query parameters
    params = {
        'callback': callback_url,
        'state': state,
        'timestamp': int(time.time())
    }
    
    # Generate the CDP wallet connection URL
    connect_url = f"cdp://connect?{urlencode(params)}"
    
    return {
        'connection_url': connect_url,
        'state': state
    }
```

This approach uses a deep link format (`cdp://connect`) that is common in mobile wallet connection flows.

### 2. Handling Wallet Integration

For the CDP Wallet integration, your authentication flow should:

1. Generate a connection URL for the user
2. Have the user open this URL in a mobile device with the CDP Wallet app installed
3. Capture the callback when the user approves the connection
4. Store the wallet address and session token for future payment operations

## Secure Credential Management

Until official API credentials are available, prepare your system with secure credential infrastructure:

1. Create a secret in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
       --name nft-payment-credentials-dev \
       --description "NFT Payment Integration Credentials" \
       --secret-string '{"X402_API_KEY":"[placeholder]","X402_API_SECRET":"[placeholder]","CDP_WALLET_APP_ID":"[placeholder]","CDP_WALLET_REDIRECT_URL":"https://your-app.com/wallet-callback"}'
   ```

2. Ensure your Lambda role has permissions to access this secret:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "secretsmanager:GetSecretValue"
               ],
               "Resource": "arn:aws:secretsmanager:*:*:secret:nft-payment-credentials-*"
           }
       ]
   }
   ```

## Payment Flow Implementation

Your current payment flow is well-structured but can be enhanced for X402:

1. **Connect Wallet**: User initiates wallet connection
2. **Initiate Payment**: Generate payment requirements according to X402 protocol
3. **Execute Payment**: User completes payment through CDP Wallet
4. **Verify Payment**: Confirm transaction status through X402 protocol
5. **Deliver Content**: Provide access to the purchased NFT content

## Testing the Integration

Since X402 is an emerging protocol, testing can be done on Base-Sepolia:

1. Set up a test wallet with Base-Sepolia ETH (available from faucets)
2. Deploy a test payment endpoint accepting X402 payments
3. Create a test client that can generate valid payment headers
4. Test the full payment flow in your development environment

## Production Deployment Considerations

When moving to production:

1. Update to mainnet networks (Base, Ethereum) instead of test networks
2. Ensure proper security measures are in place (rate limiting, signature verification)
3. Monitor transaction activity and configure proper alerting
4. Implement robust error handling and user feedback

## Resources

- [X402 GitHub Repository](https://github.com/coinbase/x402)
- [X402 Official Website](https://x402.org/)
- [CDP Documentation](https://docs.cdp.coinbase.com/)

## Next Steps

As the X402 protocol and CDP Wallet APIs continue to evolve:

1. Monitor the [X402 ecosystem page](https://x402.org/ecosystem) for official facilitator services
2. Check for official CDP Wallet API documentation updates
3. Register for developer access when it becomes publicly available
4. Update your implementation as more official tooling becomes available
