# Wallet Connection Guide for Agents

When interacting with users who need to connect their wallets for CDP transactions, follow these steps:

## 1. Initial User Prompt

When a user asks about wallet connection or making a payment, start by asking them which wallet they prefer:

```
Agent: "To process your payment, you'll need to connect your Ethereum wallet. Would you prefer to use MetaMask or Coinbase Wallet?"
```

## 2. Wallet Selection

Based on the user's response, provide specific instructions:

### For MetaMask:

```
Agent: "Great choice! To connect your MetaMask wallet:

1. Make sure you have the MetaMask browser extension installed
2. Click the 'Connect Wallet' button in the top right corner of our site
3. Select MetaMask from the options
4. Approve the connection request in the MetaMask popup

Once connected, please share your wallet address (starting with 0x) so I can verify the connection."
```

### For Coinbase Wallet:

```
Agent: "Excellent! To connect your Coinbase Wallet:

1. Make sure you have the Coinbase Wallet app installed on your device
2. Click the 'Connect Wallet' button in the top right corner of our site
3. Select Coinbase Wallet from the options
4. Scan the QR code with your Coinbase Wallet app or approve the connection

Once connected, please share your wallet address (starting with 0x) so I can verify the connection."
```

## 3. Verify Connection

Once the user provides their wallet address, use the `wallet_login` function:

```python
result = wallet_login(wallet_address, wallet_type)  # wallet_type is 'metamask' or 'coinbase'
```

Then confirm the connection:

```
Agent: "Perfect! Your wallet has been successfully connected. You can now make CDP transactions."
```

## 4. Handle Transactions

After wallet connection, guide the user through the transaction process:

```
Agent: "Now that your wallet is connected, you can make a payment by:

1. Clicking the 'Pay' button
2. Entering the amount
3. Confirming the transaction in your wallet

Let me know if you need any assistance with this process."
```

## Important Notes:

1. Always be patient and provide clear step-by-step guidance
2. Never ask for private keys or seed phrases
3. If users have trouble connecting, suggest browser/app refreshes first
4. For technical issues, direct users to support (support@example.com)
5. Emphasize that CDP transactions are secure and can be verified on-chain
