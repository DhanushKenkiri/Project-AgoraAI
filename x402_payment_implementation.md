# X402 Payment Protocol Implementation Guide

This document provides comprehensive implementation details for integrating the X402 payment protocol and CDP Wallet with your NFT payment system.

## Understanding the X402 Protocol

The X402 protocol is an open, chain-agnostic, HTTP-native payment protocol launched by Coinbase. It allows for micropayments as low as $0.001 with 2-second settlements and no percentage-based fees.

### Protocol Workflow

The standard X402 payment workflow follows these steps:

1. **Client requests a resource**: The client makes an HTTP request to a resource server.
2. **Payment Required Response**: The server responds with a `402 Payment Required` status and a `Payment Required Response` JSON object.
3. **Client creates Payment Payload**: The client creates a payment payload based on the server's requirements.
4. **Payment Header**: The client sends the HTTP request with the `X-PAYMENT` header containing the Payment Payload.
5. **Server verifies Payment**: The resource server verifies the payment is valid.
6. **Server fulfills Request**: On successful verification, the server processes the payment and delivers the resource.

## Implementing X402 in Your Lambda Function

### 1. Resource Server Implementation

Your Lambda function should implement the resource server portion of X402:

```python
def lambda_handler(event, context):
    """Main handler for X402 payment protocol integration"""
    
    # Check if payment is required for this resource
    if requires_payment(event):
        # Check if a payment header is provided
        payment_header = get_payment_header(event)
        
        if not payment_header:
            # No payment provided, return 402 Payment Required
            return generate_payment_required_response(event)
        
        # Verify the payment
        verification_result = verify_x402_payment(payment_header, event)
        
        if not verification_result['isValid']:
            # Invalid payment, return 402 again with error
            return generate_payment_required_response(
                event, 
                error=verification_result['invalidReason']
            )
        
        # Payment is valid, settle it if needed
        if verification_result.get('requiresSettlement', True):
            settlement_result = settle_x402_payment(payment_header, event)
            if not settlement_result['success']:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Payment settlement failed'
                    })
                }
        
        # Payment processed, continue with the request
        # Include X-PAYMENT-RESPONSE header with settlement info
        payment_response = generate_payment_response_header(settlement_result)
    
    # Process the main request logic
    response = process_request(event, context)
    
    # Add payment response header if applicable
    if payment_response:
        response['headers']['X-PAYMENT-RESPONSE'] = payment_response
    
    return response
```

### 2. Implementing Payment Required Response

```python
def generate_payment_required_response(event, error=None):
    """Generate a 402 Payment Required response according to X402 protocol specification"""
    
    resource_path = event.get('path', '/premium-nft-data')
    description = f"Payment required for {resource_path}"
    
    # Define payment requirements for different resources
    pricing = {
        '/premium-nft-data': {'amount': 0.01, 'currency': 'ETH'},
        '/exclusive-nft': {'amount': 0.05, 'currency': 'ETH'},
        '/nft-analytics': {'amount': 0.025, 'currency': 'USDC'}
    }
    
    price_info = pricing.get(resource_path, {'amount': 0.01, 'currency': 'ETH'})
    amount = price_info['amount']
    currency = price_info['currency']
    
    # Convert amount to atomic units
    atomic_amount = convert_to_atomic_units(amount, currency)
    
    # Get payment address from config
    payment_address = config.get('PAYMENT_ADDRESS')
    
    # Build the payment requirements object according to X402 protocol spec
    payment_requirements = {
        'scheme': 'exact',
        'network': 'base-sepolia',  # Use base-sepolia for testing
        'maxAmountRequired': atomic_amount,
        'resource': resource_path,
        'description': description,
        'mimeType': 'application/json',
        'payTo': payment_address,
        'maxTimeoutSeconds': 300,
        'asset': config.get('TOKEN_CONTRACT_ADDRESS'),
        'extra': {
            'name': 'NFT Premium Access',
            'version': '1'
        }
    }
    
    # Build the full payment required response
    payment_response = {
        'x402Version': 1,
        'accepts': [payment_requirements],
        'error': error
    }
    
    return {
        'statusCode': 402,  # Payment Required
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps(payment_response)
    }
```

### 3. Verifying Payment Headers

```python
def verify_x402_payment(payment_header, event):
    """Verify an X402 payment header"""
    try:
        # Decode the base64 payment header
        decoded_header = base64.b64decode(payment_header).decode('utf-8')
        payment_data = json.loads(decoded_header)
        
        # Extract scheme and network
        scheme = payment_data.get('scheme')
        network = payment_data.get('network')
        
        # Get payment requirements for this request
        payment_requirements = get_payment_requirements(event)
        
        # For self-verification, implement the verification logic here
        # For facilitator-based verification, call the facilitator API:
        
        verification_request = {
            'x402Version': payment_data.get('x402Version'),
            'paymentHeader': payment_header,
            'paymentRequirements': payment_requirements
        }
        
        # Call facilitator server or implement local verification
        # This is a placeholder for the actual verification logic
        verification_result = {
            'isValid': True,
            'invalidReason': None,
            'requiresSettlement': True
        }
        
        return verification_result
        
    except Exception as e:
        return {
            'isValid': False,
            'invalidReason': f"Error verifying payment: {str(e)}"
        }
```

### 4. Settling Payments

```python
def settle_x402_payment(payment_header, event):
    """Settle an X402 payment"""
    try:
        # Decode the payment header
        decoded_header = base64.b64decode(payment_header).decode('utf-8')
        payment_data = json.loads(decoded_header)
        
        # Get payment requirements
        payment_requirements = get_payment_requirements(event)
        
        # For facilitator-based settlement, call the facilitator API:
        settlement_request = {
            'x402Version': payment_data.get('x402Version'),
            'paymentHeader': payment_header,
            'paymentRequirements': payment_requirements
        }
        
        # This would be replaced with an actual API call to the facilitator
        # For now, we just simulate a successful settlement
        
        payment_id = f"x402_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        tx_hash = f"0x{uuid.uuid4().hex}"
        
        # Record the payment in DynamoDB
        store_transaction_record({
            'payment_id': payment_id,
            'tx_hash': tx_hash,
            'scheme': payment_data.get('scheme'),
            'network': payment_data.get('network'),
            'amount': payment_requirements.get('maxAmountRequired'),
            'resource': payment_requirements.get('resource'),
            'status': 'completed',
            'created_at': int(time.time())
        })
        
        return {
            'success': True,
            'payment_id': payment_id,
            'tx_hash': tx_hash,
            'network': payment_data.get('network')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error settling payment: {str(e)}"
        }
```

### 5. Generating Payment Response Headers

```python
def generate_payment_response_header(settlement_result):
    """Generate X-PAYMENT-RESPONSE header value"""
    response_data = {
        'success': settlement_result.get('success'),
        'txHash': settlement_result.get('tx_hash'),
        'networkId': settlement_result.get('network')
    }
    
    # Base64 encode the JSON response
    encoded_response = base64.b64encode(
        json.dumps(response_data).encode()
    ).decode()
    
    return encoded_response
```

## CDP Wallet Integration

CDP Wallet integration requires creating deeplinks for wallet connections and payments:

### 1. Wallet Connection

```python
def create_wallet_connection_url(callback_url=None, state=None):
    """Create a deeplink URL for connecting CDP wallet"""
    if not state:
        state = str(uuid.uuid4())
    
    # Build the query parameters
    params = {
        'callback': callback_url or os.environ.get('CDP_CALLBACK_URL'),
        'state': state,
        'app_id': config.get('CDP_WALLET_APP_ID', ''),
        'timestamp': int(time.time())
    }
    
    # Generate the wallet connection deeplink
    connect_url = f"cdp://connect?{urlencode(params)}"
    
    return {
        'connection_url': connect_url,
        'state': state
    }
```

### 2. Payment Request

```python
def create_payment_url(recipient, amount, currency, reference=None):
    """Create a CDP wallet payment URL"""
    if not reference:
        reference = str(uuid.uuid4())
    
    # Build the payment parameters
    params = {
        'recipient': recipient,
        'amount': amount,
        'currency': currency,
        'reference': reference,
        'app_id': config.get('CDP_WALLET_APP_ID', ''),
        'callback': os.environ.get('CDP_PAYMENT_CALLBACK_URL')
    }
    
    # Generate the payment URL
    payment_url = f"cdp://pay?{urlencode(params)}"
    
    return {
        'payment_url': payment_url,
        'reference': reference
    }
```

## Integration in Amazon Bedrock Agent

When configuring your Bedrock agent:

1. **Action Schema**: Define an action group for payment operations that maps to your Lambda function:

```json
{
  "actionGroupName": "PaymentProcessing",
  "description": "Handle NFT payments using the X402 protocol",
  "apiSchema": {
    "actions": [
      {
        "name": "InitiatePayment",
        "description": "Start a payment for NFT content",
        "parameters": {
          "type": "object",
          "properties": {
            "resource": {
              "type": "string",
              "description": "Resource path to access"
            },
            "wallet_address": {
              "type": "string",
              "description": "User's wallet address"
            }
          },
          "required": ["resource"]
        }
      },
      {
        "name": "ConnectWallet",
        "description": "Connect a CDP wallet",
        "parameters": {
          "type": "object",
          "properties": {
            "callback_url": {
              "type": "string",
              "description": "URL to redirect after wallet connection"
            }
          }
        }
      },
      {
        "name": "CheckPaymentStatus",
        "description": "Check status of a payment",
        "parameters": {
          "type": "object",
          "properties": {
            "payment_id": {
              "type": "string",
              "description": "Payment identifier to check"
            }
          },
          "required": ["payment_id"]
        }
      }
    ]
  }
}
```

2. **Agent Instructions**: Include clear guidelines on payment processing:

```
You are a payment processing agent for NFT transactions using the X402 protocol and CDP Wallet.

When processing payments:
1. First check if the user has connected their wallet
2. If no wallet is connected, provide the wallet connection URL
3. Once wallet is connected, generate payment requirements for the requested resource
4. Provide the payment URL for the user to complete the transaction
5. Allow the user to check payment status

Always prioritize security and validate all payment details before proceeding.
```

## Security Best Practices

1. **Validate Signatures**: Always validate cryptographic signatures in payment payloads
2. **Prevent Replay Attacks**: Use nonces and timestamps in payment requests
3. **Verify Chain IDs**: Ensure transactions are on the expected blockchain network
4. **Encrypt Sensitive Data**: Use KMS for storing private keys and credentials
5. **Implement Rate Limiting**: Prevent abuse with proper API rate limiting
6. **Monitor Transactions**: Set up alerting for suspicious payment patterns

## Testing and Development

For development and testing:

1. Use Base-Sepolia testnet for X402 protocol testing
2. Create test wallets with small amounts of test ETH
3. Implement proper logging for payment flows
4. Use AWS X-Ray for transaction tracing
5. Create a sandbox environment for payment testing

## Conclusion

The X402 payment protocol offers a powerful way to implement internet-native micropayments in your NFT application. By following this implementation guide, you can provide secure, low-cost payment options with minimal friction for your users.

As the X402 ecosystem continues to develop, watch for official facilitator services that can simplify the verification and settlement processes even further.
