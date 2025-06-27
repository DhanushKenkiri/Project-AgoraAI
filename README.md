# NFT Payment System Using X402 Protocol and CDP Wallet

This repository contains a secure payment system for NFT transactions using Coinbase's X402 payment protocol and CDP Wallet integration, built on AWS Lambda and Amazon Bedrock.

## Overview

The system enables micropayments for NFT content using X402, an open HTTP-native payment protocol, and connects to users' wallets through CDP Wallet integration.

### Key Components

- **X402 Payment Protocol**: Enables micropayments as low as $0.001 with 2-second settlements and no percentage fees
- **CDP Wallet Integration**: Allows users to securely connect their crypto wallets
- **AWS Serverless Infrastructure**: Lambda functions, API Gateway, DynamoDB, and KMS for secure payment processing
- **Amazon Bedrock Agent**: AI assistant that guides users through the payment process

## Implementation Files

- `payment_handler.py`: Lambda handler implementing X402 payment protocol
- `secure_payment_config.py`: Secure credential management using AWS Secrets Manager
- `x402_client.js`: Client-side implementation for creating X402 payment headers
- `utils/payment_integration.py`: Helper methods for payment and wallet integration
- `x402_payment_implementation.md`: Detailed implementation guide
- `x402_cdp_wallet_integration_guide.md`: Guide for X402 and CDP Wallet setup
- `payment_agent_setup_guide.md`: Instructions for setting up the Bedrock agent
- `nft_payment_stack.yaml`: CloudFormation template for deploying the infrastructure

## Getting Started

1. Deploy the infrastructure using the CloudFormation template
2. Configure AWS Secrets Manager with your Ethereum wallet address
3. Deploy the Lambda code
4. Set up the Amazon Bedrock agent following the guides

## Testing

For testing purposes, use the Base-Sepolia testnet:
1. Get test ETH from a Base-Sepolia faucet
2. Configure your payment address in Secrets Manager
3. Use the test endpoints to verify the payment flow

## Security Features

- KMS encryption for sensitive data
- AWS Secrets Manager for credential storage
- Input validation for all payment requests
- Transaction monitoring and alerts
- Rate limiting to prevent abuse

## Further Resources

- [X402 GitHub Repository](https://github.com/coinbase/x402)
- [X402 Official Website](https://x402.org/)
- [CDP Documentation](https://docs.cdp.coinbase.com/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
