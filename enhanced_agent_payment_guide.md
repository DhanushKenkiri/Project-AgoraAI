# Enhanced Agent Payment Guide

This document provides comprehensive examples and guidelines for implementing payment flows in AI agents using the X402 payment protocol and CDP wallet integration.

## Payment Flow Architecture

The payment system consists of these key components:

1. **X402 Payment Protocol** - A protocol for requesting and verifying blockchain payments
2. **CDP Wallet Integration** - Direct connection to user wallets for frictionless payments
3. **Lambda Handler** - AWS Lambda function handling payment requests and verification
4. **Bedrock Agent Integration** - Seamless connection to Amazon Bedrock agents

## Example Dialog Flows

### Basic Payment Flow

**User:** "Can you show me floor price data for Bored Ape Yacht Club?"

**Agent:** 
```
I can provide detailed floor price data for the Bored Ape Yacht Club NFT collection, but this requires a payment of 0.002 ETH (or approximately $5 in USDC).

[Pay 0.002 ETH] [Pay 5.00 USDC] [Pay 5.00 USDT]

Would you like to proceed with one of these payment options?
```

**User:** *clicks "Pay 5.00 USDC"*

**Agent:**
```
I've updated your payment option to USDC. The payment will be 5.00 USDC.

To process your payment, I'll need your wallet address. This is where you'll receive any potential benefits or returns from this transaction.

Please provide your wallet address.
```

**User:** "My wallet address is 0x1234abcd..."

**Agent:**
```
Thank you. I'll process the payment of 5.00 USDC to wallet address 0x1234abcd...

Payment has been initiated and is processing in the background. You'll receive a notification once the transaction completes.

While we wait, can you tell me what specific floor price metrics you're interested in? For example, I can show 24-hour changes, 7-day trends, or compare with similar collections.
```

**User:** "I'd like to see the 7-day trend."

**Agent:**
```
Great! I'll include the 7-day trend in the data once the payment is processed.

✅ Good news! Your payment of 5.00 USDC has been successfully processed. Transaction hash: 0xdef456...

Here's the floor price data for Bored Ape Yacht Club including the 7-day trend:

📊 **BAYC Floor Price Data**:
- Current floor: 32.75 ETH
- 24h change: +0.55 ETH (+1.7%)
- 7-day trend: ⬆️ Increased from 30.25 ETH (+8.3%)
- 30-day volatility: Medium (±5%)
- Total sales volume (7d): 412.8 ETH
- Average sale price (7d): 33.15 ETH

You can view your transaction on the blockchain: https://sepolia.basescan.org/tx/0xdef456...

Is there anything else you'd like to know about this collection?
```

### CDP Wallet Connect Flow

**User:** "I want to check my NFT portfolio value, but I haven't connected my wallet yet."

**Agent:**
```
To check your NFT portfolio value, I'll need to connect to your wallet. I support CDP wallets for secure, permissionless connections.

[Connect CDP Wallet]

Would you like to connect your wallet now?
```

**User:** *clicks "Connect CDP Wallet"*

**Agent:**
```
Great! Please scan this QR code with your CDP wallet app or click the link below:

[QR CODE IMAGE]
cdp://connect?callback=https://api.example.com/wallet/callback&state=1234567890&timestamp=1685431200

Once you approve the connection in your wallet app, I'll be able to view your NFT holdings without any permissions to transfer assets.
```

**User:** "I've connected my wallet."

**Agent:**
```
Connection successful! I've detected your wallet address 0xabcd1234...

Analyzing your NFT portfolio...

📊 **Your NFT Portfolio Value**:
- Total estimated value: 3.45 ETH (~$8,625)
- Number of collections: 5
- Total NFTs: 12
- Most valuable collection: CryptoPunks (2.1 ETH)

Would you like to see a breakdown by collection or analyze any specific NFTs in your portfolio?
```

### Advanced Payment Flow with Options

**User:** "I need detailed whale analytics for Azuki collection."

**Agent:**
```
I can provide detailed whale analytics for the Azuki collection. This premium data requires a payment. You have several options:

**Basic Analytics**: 0.001 ETH ($2.50)
- Top 10 whale movements
- Basic holder distribution 

**Advanced Analytics**: 0.005 ETH ($12.50)
- Complete whale tracking data
- Wallet clustering analysis
- Future price impact prediction
- Historical correlation with price

Which package would you prefer?
```

**User:** "I'll go with the Advanced Analytics package."

**Agent:**
```
Great choice! The Advanced Analytics package provides comprehensive whale data for Azuki.

The payment will be 0.005 ETH (approximately $12.50).

[Pay with ETH] [Pay with USDC (~$12.50)] [Pay with USDT (~$12.50)]

Please select your preferred payment method.
```

**User:** *clicks "Pay with USDC (~$12.50)"*

**Agent:**
```
You've selected USDC payment. The amount will be 12.50 USDC.

Please provide the wallet address where you would like to receive any potential returns or benefits.
```

**User:** "Here's my wallet: 0x9876fedc..."

**Agent:**
```
Thank you. I'll process your payment of 12.50 USDC to wallet 0x9876fedc...

Payment processing has started in the background. This typically takes 15-30 seconds to complete.

While we wait, I can explain that the whale analytics will include detailed tracking of large holder behaviors, clustering analysis to identify coordinated movements, and potential price impact assessments based on historical patterns.
```

*[After payment processing completes]*

**Agent:**
```
✅ Great news! Your payment of 12.50 USDC has been successfully processed.
Transaction hash: 0x789abc...

📊 **Azuki Whale Analytics Report**:

1. **Top Whale Movements (Last 7 Days)**:
   - 3 whales accumulated +125 Azuki NFTs
   - 1 whale liquidated 52 Azuki NFTs
   - Net whale accumulation: +73 NFTs

2. **Wallet Clustering Analysis**:
   - 5 connected whale wallets identified
   - Coordinated buying detected in wallet group A
   - Significant holding: 3.2% of total supply controlled by top whale

3. **Price Impact Prediction**:
   - Current accumulation pattern suggests +15-20% price movement potential
   - Historical correlation: 78% accuracy between this pattern and price increases

4. **Holder Distribution Changes**:
   - Diamond hands (held >6 months): +2.3%
   - Short-term holders: -1.7%
   - Trend indicates strengthening holder conviction

You can view your transaction on the blockchain: https://sepolia.basescan.org/tx/0x789abc...

Would you like me to analyze any specific aspect of this data in more detail?
```

## Implementation Guidelines

### 1. Payment Request Best Practices

- **Be transparent about costs upfront** - Always state the exact price and what the user will get.
- **Offer multiple payment options** - Always include ETH and stable coin options.
- **Explain the value** - Clearly state what premium features or data the payment unlocks.
- **Provide tiered options** when appropriate - Basic and premium packages.

### 2. User Experience Guidelines

- **Keep users in the conversation** - Never send users to external payment sites.
- **Show payment progress** - Clearly indicate when payment is processing/complete.
- **Continue providing value** - Engage users while payment processes in the background.
- **Provide transaction receipts** - Always include transaction hash and blockchain explorer link.

### 3. Technical Integration Notes

- Use the `X402PaymentProcessor` class for all payment operations
- Verify payments with `verify_x402_payment()` method
- Process payments in background using the `settle_x402_payment()` method
- Store transaction records in DynamoDB for auditing
- Track payment status with unique payment IDs
- Support both EIP-3009 token transfers and native ETH payments

### 4. Response Templates

#### Payment Request Template
```
I can help with [specific user request], but this requires a payment of [amount] [currency].

[Payment option buttons]

Would you like to proceed with payment?
```

#### Wallet Request Template
```
To process your payment, I'll need your wallet address. This is where you'll receive any potential benefits or returns.

Please provide your wallet address.
```

#### Payment Processing Template
```
Thank you. I'll process the payment of [amount] [currency] to wallet address [wallet].

Payment processing has started in the background. This typically takes 15-30 seconds to complete.

[Continue conversation while waiting]
```

#### Payment Completion Template
```
✅ Good news! Your payment of [amount] [currency] has been successfully processed.
Transaction hash: [tx_hash]

[Provide the requested premium content/service]

You can view your transaction on the blockchain: [explorer_link]

[Continue conversation with follow-up questions]
```

## Error Handling

### Failed Payment Template
```
I'm sorry, but there was an issue processing your payment: [error_message]

You have not been charged. Would you like to try again with a different payment method?

[Alternative payment options]
```

### Insufficient Funds Template
```
I noticed there might be insufficient funds in your wallet for this transaction.

You can:
1. Try again with a lower amount
2. Use a different token for payment
3. Add funds to your wallet and try again

Would you like to proceed with one of these options?
```

## Security and Privacy Considerations

1. **Never store private keys** or wallet seed phrases.
2. **Minimize wallet address retention** - Only store what's necessary for transaction processing.
3. **Use secure, authenticated endpoints** for all payment-related API calls.
4. **Encrypt sensitive payment data** using AWS KMS.
5. **Implement rate limiting** to prevent payment-related abuse.
6. **Log payment attempts** for security monitoring.
