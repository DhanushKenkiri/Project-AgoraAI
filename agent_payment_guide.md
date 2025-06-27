# Agent Payment Example Guide

This document provides example prompts and responses that show how the AI agent should interact with users when collecting payment information.

## Example Dialog Flow for Payments

### 1. User requests content that requires payment

**User:** "I need to view details of the NFT collection XYZ"

**Agent:** 
```
I can help you view the details of NFT collection XYZ, but this requires a payment of 0.005 ETH.

[Pay 0.005 ETH] [Pay with USDC] [Pay with USDT]

Would you like to proceed with the payment?
```

### 2. User selects payment method

**User:** *clicks "Pay with USDC"*

**Agent:**
```
I've updated your payment option to USDC. The payment will be 15.00 USDC.

[Pay 15.00 USDC]

Please provide the wallet address where you would like to receive any potential returns or benefits from this transaction.
```

### 3. User provides wallet address

**User:** "Here's my wallet address: 0x1234abcd..."

**Agent:**
```
Thank you. I'll process the payment of 15.00 USDC to wallet address 0x1234abcd...

Payment has been initiated in the background and will be processed automatically. You'll be notified once the transaction is complete.

Is there anything specific about the NFT collection XYZ you'd like to know once the payment is processed?
```

### 4. Payment completes

**Agent:**
```
Good news! Your payment of 15.00 USDC has been successfully processed. Transaction hash: 0xabc123...

Here are the details of NFT collection XYZ:
[Collection details...]

You can view the transaction on the blockchain explorer: https://sepolia.basescan.org/tx/0xabc123...
```

### 5. Returning user with stored wallet

**User:** "I want to view market analysis of Bored Ape Yacht Club"

**Agent:**
```
I can provide detailed market analysis of Bored Ape Yacht Club, but this requires a payment of 0.005 ETH.

I'll use your previously connected wallet (0x1234abcd...) for the payment.

[Pay 0.005 ETH] [Pay with USDC] [Pay with USDT] [Use different wallet]

Would you like to proceed with the payment?
```

**User:** *clicks "Pay 0.005 ETH"*

**Agent:**
```
Thank you. I'll process the payment of 0.005 ETH using your connected wallet 0x1234abcd...

Payment has been initiated in the background and will be processed automatically. You'll be notified once the transaction is complete.

While we wait, is there any specific aspect of the Bored Ape Yacht Club market you're most interested in (floor price trends, sales volume, etc.)?
```

**User:** "I'm interested in the floor price trends"

**Agent:**
```
Good news! Your payment of 0.005 ETH has been successfully processed. Transaction hash: 0xdef456...

Here's the floor price analysis for Bored Ape Yacht Club:
[Market analysis details...]

The floor price has increased 12% over the past month, with the current floor at 30.5 ETH. Here's a visualization of the trend:

![Floor Price Trend](https://example.com/floor-price-chart.png)

You can view the transaction on the blockchain explorer: https://etherscan.io/tx/0xdef456...
```

## Example Dialog Flow for Non-Payment Interactions

### 1. General NFT question (no wallet required)

**User:** "What is an NFT?"

**Agent:**
```
An NFT (Non-Fungible Token) is a digital asset that represents ownership of a unique item or piece of content on the blockchain. Unlike cryptocurrencies such as Bitcoin, NFTs are not interchangeable with each other, making each one unique.

NFTs can represent digital art, music, videos, virtual real estate, game items, collectibles, and more. The blockchain technology ensures that ownership history is transparent and verifiable.

Would you like to know more about how NFTs work or how to buy/sell them?
```

### 2. User asks about a specific collection (no wallet required)

**User:** "Tell me about the Azuki collection"

**Agent:**
```
Azuki is a popular anime-inspired NFT collection featuring 10,000 unique characters with distinctive traits. The collection launched in January 2022 and quickly gained popularity for its high-quality artwork and strong community.

Key facts about Azuki:
- Collection size: 10,000 NFTs
- Blockchain: Ethereum
- Current floor price: 8.2 ETH
- Total trading volume: Over 350,000 ETH

The project expanded beyond just digital collectibles with physical merchandise, events, and plans for metaverse integration.

Would you like to see recent marketplace data for Azuki or learn about similar collections?
```

## Guidelines for Agent Payment Flow

1. **Always display payment options as buttons** to make it easy for users to select.

2. **Show alternative payment currencies** when available.

3. **Never redirect users away from the conversation** - all payments are processed in the background.

4. **Check for a stored wallet address first** before asking the user. Only request wallet address when not found in session storage.

5. **Remember wallet addresses across conversations** using session persistence.

6. **Notify the user when payment starts** and when it completes.

7. **Provide transaction details after completion** including transaction hash and explorer link.

8. **Continue the conversation naturally** after payment processing.

9. **Don't require wallet address for non-payment queries** - wallet connection should be optional for informational requests.

## Response Templates

### Payment Required Template
```
I can help with [user request], but this requires a payment of [amount] [currency].

[Pay button] [Alternative currency buttons]

Would you like to proceed with the payment?
```

### Payment Processing Template
```
Thank you. I'll process the payment of [amount] [currency] to wallet address [wallet_address].

Payment has been initiated in the background and will be processed automatically. You'll be notified once the transaction is complete.

[Continue conversation...]
```

### Payment Completion Template
```
Good news! Your payment of [amount] [currency] has been successfully processed. Transaction hash: [tx_hash]

[Provide requested information/service]

You can view the transaction on the blockchain explorer: [explorer_link]
```
