# Testing the NFT Payment Lambda Implementation

This guide explains how to test your NFT payment Lambda function using the provided test files.

## 1. Local Testing

The `test_lambda_local.py` script allows you to test the Lambda function locally before deploying it to AWS.

### Prerequisites

- Python 3.7+
- All required dependencies installed

### Running Local Tests

1. Make sure all the environment variables are properly set (or use the mock environment in `test.json`)
2. Run the test script:

```bash
python test_lambda_local.py
```

3. Select a test to run or choose 'all' to run all tests

### Test Data

The `test.json` file contains:

- `testEvents`: Various API requests to test different endpoints
- `simulatedResponses`: Mock API responses for testing
- `lambdaContext`: Mock Lambda context object
- `mockEnvironment`: Mock environment variables for testing

## 2. AWS Lambda Console Testing

You can use the `lambda_test_events.json` file to create test events in the AWS Lambda Console.

### Using Test Events in AWS Lambda Console

1. Go to the AWS Lambda Console
2. Open your Lambda function
3. Click on the "Test" tab
4. Create a new test event
5. Copy one of the events from `lambda_test_events.json` and paste it into the event JSON editor
6. Save the test event
7. Click "Test" to run the test

### Available Test Events

- `basicNFTQuery`: Query NFT data for a collection
- `collectionPriceQuery`: Get floor price for a collection
- `paymentRequest`: Initialize a payment request
- `cdpWalletConnect`: Connect to CDP Wallet
- `dynamicPriceQuery`: Calculate dynamic pricing
- `nftTransactionQuery`: Check transaction status
- `multiCollectionAnalysis`: Analyze multiple collections
- `nftSentimentAnalysis`: Get sentiment analysis for a collection
- `webSearchQuery`: Search for NFT-related information
- `nftRarityCheck`: Check rarity of an NFT
- `gasEstimation`: Get current gas prices

## 3. API Gateway Testing

Once deployed with API Gateway, you can test the API endpoints using curl or Postman.

### Example curl command for NFT query:

```bash
curl -X POST https://your-api-gateway-url/nft/query?includeMetadata=true \
  -H "Content-Type: application/json" \
  -d '{"collection":"bored-ape-yacht-club","chain":"ethereum"}'
```

### Example curl command for payment initialization:

```bash
curl -X POST https://your-api-gateway-url/payment/init \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"amount":"0.005","currency":"ETH","paymentReason":"NFT analysis","x402":{"payment_type":"x402","wallet_address":"0x742d35Cc6634C0532925a3b844Bc454e4438f44e","redirect_url":"https://example.com/success"}}'
```

## Troubleshooting

### Common Issues:

1. **Missing Environment Variables**: Ensure all required environment variables are set.
2. **API Key Issues**: Check that all NFT API keys are valid and properly configured.
3. **Lambda Timeout**: If testing complex operations, consider increasing the Lambda timeout setting.
4. **Permission Issues**: Ensure the Lambda execution role has all necessary permissions.
5. **Memory Limitations**: For operations involving large NFT datasets, consider increasing the Lambda memory allocation.

If you encounter specific errors in the response, check CloudWatch Logs for detailed error messages.
