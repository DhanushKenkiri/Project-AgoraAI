# Payment Integration Testing Guide

This guide provides comprehensive instructions for testing your NFT payment integration with both Bedrock agents and direct API calls.

## Test Environment Setup

### 1. Local Environment Setup

First, ensure you have the proper test environment variables set:

```bash
# Set to test environment
export ENVIRONMENT=test
export NETWORK=base-sepolia
export TOKEN_CONTRACT_ADDRESS=0x07865c6E87B9F70255377e024ace6630C1Eaa37F  # Sepolia USDC
```

### 2. Create Test Wallets

For testing, create test wallets with the following test configurations:

- Test ETH wallet: Use a wallet with Sepolia ETH (can be obtained from faucets)
- Test USDC wallet: Use a wallet with Sepolia USDC tokens
- Test CDP wallet: Install the CDP wallet app and create a test account

## Testing Methods

### 1. Direct Lambda Invocation Tests

These tests bypass API Gateway and invoke the Lambda function directly.

#### Test Wallet Connection

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Test wallet connection URL generation
response = lambda_client.invoke(
    FunctionName='your-lambda-function-name',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'connect_wallet'
    })
)

result = json.loads(response['Payload'].read())
print(f"Wallet connection URL: {result.get('connection_url')}")
print(f"State parameter: {result.get('state')}")

# Test wallet connection storage
wallet_address = '0xYourTestWalletAddress'
state = result.get('state')

response = lambda_client.invoke(
    FunctionName='your-lambda-function-name',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'connect_wallet',
        'wallet_address': wallet_address,
        'state': state
    })
)

result = json.loads(response['Payload'].read())
print(f"Connection result: {result}")
```

#### Test Payment Initiation

```python
# Test payment initiation
response = lambda_client.invoke(
    FunctionName='your-lambda-function-name',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'initiate_payment',
        'wallet_address': '0xYourTestWalletAddress',
        'amount': '0.001',
        'currency': 'ETH'
    })
)

result = json.loads(response['Payload'].read())
print(f"Payment initiation result: {result}")
payment_id = result.get('payment_id')
```

#### Test Payment Status

```python
# Test payment status check
response = lambda_client.invoke(
    FunctionName='your-lambda-function-name',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'check_status',
        'payment_id': payment_id
    })
)

result = json.loads(response['Payload'].read())
print(f"Payment status: {result}")
```

### 2. API Gateway Tests

These tests simulate the actual API calls that would be made by the agent or client application.

#### Test Wallet Connection API

```bash
# Generate connection URL
curl -X POST https://your-api-endpoint.execute-api.region.amazonaws.com/prod/wallet/connect \
  -H "Content-Type: application/json" \
  -d '{}'

# Store wallet connection
curl -X POST https://your-api-endpoint.execute-api.region.amazonaws.com/prod/wallet/connect \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xYourTestWalletAddress",
    "state": "state-from-previous-response"
  }'
```

#### Test Payment API

```bash
# Initiate payment
curl -X POST https://your-api-endpoint.execute-api.region.amazonaws.com/prod/payments \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "0.001",
    "currency": "ETH",
    "wallet_address": "0xYourTestWalletAddress",
    "payment_reason": "NFT Data Access Test"
  }'

# Check payment status
curl -X GET "https://your-api-endpoint.execute-api.region.amazonaws.com/prod/payments/status?payment_id=your-payment-id"
```

### 3. X402 Protocol Tests

These tests verify the X402 payment protocol implementation.

#### Test X402 Payment Header

```bash
# First, generate a payment required response
curl -X GET https://your-api-endpoint.execute-api.region.amazonaws.com/prod/premium-nft-data

# This should return a 402 Payment Required with X402 details

# Now create a test X402 payment header (simulated for testing)
PAYMENT_HEADER=$(echo '{
  "scheme": "exact",
  "network": "base-sepolia",
  "x402Version": 1,
  "payload": {
    "type": "native",
    "from": "0xYourTestWalletAddress",
    "to": "0xPaymentRecipientAddress",
    "amount": "1000000000000000",
    "timestamp": '$(date +%s)',
    "signature": "0xSimulatedSignature"
  }
}' | base64)

# Test accessing a protected endpoint with the payment header
curl -X GET https://your-api-endpoint.execute-api.region.amazonaws.com/prod/premium-nft-data \
  -H "X-PAYMENT: $PAYMENT_HEADER"
```

### 4. Bedrock Agent Testing

Use these examples in the Bedrock Agent console to test your payment integration.

#### Test Agent Payment Flow

1. In the Bedrock Agent console, open your agent
2. Start a new test session
3. Test the following conversation flow:

```
User: Show me the whale activity for BAYC collection.

Agent: [Should explain that payment is required and offer payment options]

User: I'll pay with ETH.

Agent: [Should ask for wallet address]

User: My wallet is 0xYourTestWalletAddress

Agent: [Should initiate payment and show processing message]

[Wait for a few seconds]

Agent: [Should show payment confirmation and provide the requested data]
```

## Verification Steps

For each test, verify the following:

### 1. Database Records

Check DynamoDB tables to verify records are being created:

```python
import boto3

dynamodb = boto3.resource('dynamodb')
transaction_table = dynamodb.Table('NFTPaymentTransactions-test')
wallet_table = dynamodb.Table('NFTWalletSessions-test')

# Check transaction record
response = transaction_table.get_item(Key={'payment_id': 'your-payment-id'})
print(f"Transaction record: {response.get('Item')}")

# Check wallet session
response = wallet_table.get_item(Key={'wallet_address': '0xYourTestWalletAddress'})
print(f"Wallet session: {response.get('Item')}")
```

### 2. Blockchain Verification

For actual blockchain transactions (in test nets), verify the transaction:

```python
import requests

tx_hash = "your-transaction-hash"
explorer_url = f"https://sepolia.basescan.org/tx/{tx_hash}"

print(f"Verify transaction at: {explorer_url}")

# Use blockchain API to verify transaction status
rpc_url = "https://sepolia.base.org"
payload = {
    "jsonrpc": "2.0",
    "method": "eth_getTransactionReceipt",
    "params": [tx_hash],
    "id": 1
}

response = requests.post(rpc_url, json=payload)
receipt = response.json()['result']

if receipt and int(receipt['status'], 16) == 1:
    print("Transaction successful!")
else:
    print("Transaction failed or pending")
```

## Common Issues and Debug Tips

### 1. Payment Verification Failures

If payment verification fails:

1. Check the X402 payment header format
2. Verify the network matches your configuration
3. Ensure wallet addresses are correctly formatted
4. Check timestamp is within allowed window

### 2. DynamoDB Issues

If database operations fail:

1. Verify table names are correct
2. Check IAM permissions for Lambda
3. Ensure the table schema matches expected format

### 3. CDP Wallet Connection Issues

If wallet connections fail:

1. Verify the CDP wallet app is installed correctly
2. Check the callback URL is accessible
3. Ensure state parameter is passed correctly
4. Verify the network/chain ID matches your wallet

### 4. No Transaction Hash

If no transaction hash is returned:

1. Check RPC URL configuration
2. Verify gas settings for test transactions
3. Ensure wallet has sufficient balance
4. Check for network congestion

## End-to-End Test Script

Use this script to perform a complete end-to-end test:

```python
import boto3
import json
import time

def test_full_payment_flow():
    lambda_client = boto3.client('lambda')
    
    # Step 1: Generate wallet connection URL
    print("=== Step 1: Generating wallet connection URL ===")
    response = lambda_client.invoke(
        FunctionName='your-lambda-function',
        InvocationType='RequestResponse',
        Payload=json.dumps({'action': 'connect_wallet'})
    )
    result = json.loads(response['Payload'].read())
    connection_url = result.get('connection_url')
    state = result.get('state')
    
    print(f"Connection URL: {connection_url}")
    print(f"State parameter: {state}")
    
    # Step 2: Simulate wallet connection (manual step in real scenario)
    wallet_address = "0xYourTestWalletAddress"
    print(f"\n=== Step 2: Simulating wallet connection for {wallet_address} ===")
    response = lambda_client.invoke(
        FunctionName='your-lambda-function',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'connect_wallet',
            'wallet_address': wallet_address,
            'state': state
        })
    )
    result = json.loads(response['Payload'].read())
    print(f"Connection result: {result}")
    
    # Step 3: Initiate payment
    print("\n=== Step 3: Initiating payment ===")
    response = lambda_client.invoke(
        FunctionName='your-lambda-function',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'initiate_payment',
            'wallet_address': wallet_address,
            'amount': '0.001',
            'currency': 'ETH',
            'payment_reason': 'Test Payment'
        })
    )
    result = json.loads(response['Payload'].read())
    payment_id = result.get('payment_id')
    print(f"Payment initiation result: {result}")
    print(f"Payment ID: {payment_id}")
    
    # Step 4: Check payment status (may need multiple checks)
    print("\n=== Step 4: Checking payment status ===")
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        attempts += 1
        print(f"Attempt {attempts}/{max_attempts}...")
        
        response = lambda_client.invoke(
            FunctionName='your-lambda-function',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'check_status',
                'payment_id': payment_id
            })
        )
        result = json.loads(response['Payload'].read())
        status = result.get('status')
        print(f"Payment status: {status}")
        
        if status == 'completed':
            print(f"Transaction hash: {result.get('transaction_hash')}")
            print(f"Explorer URL: {result.get('explorer_url')}")
            break
            
        if status == 'failed':
            print(f"Payment failed: {result.get('error')}")
            break
            
        if attempts < max_attempts:
            print("Waiting 5 seconds before checking again...")
            time.sleep(5)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_full_payment_flow()
```

## Production Readiness Tests

Before going to production, perform these additional tests:

1. **Load Testing**: Test with multiple simultaneous payment requests
2. **Error Recovery**: Test system recovery after failures
3. **Security Testing**: Test for common vulnerabilities
4. **Timeout Testing**: Test behavior when transactions take longer than expected
5. **Integration Testing**: Test the full flow with the Bedrock agent

By following this testing guide, you'll ensure your payment integration is robust and ready for production use with your Bedrock agent.
