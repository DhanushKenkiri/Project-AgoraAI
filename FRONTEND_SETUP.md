# Fixing "contractAddress is required" Error and Frontend Setup

This guide explains how to fix the "contractAddress is required" error and set up the frontend for your NFT payment system.

## Understanding the Error

The error "contractAddress is required" occurs because the Lambda function expects a `contractAddress` parameter in the event object, but it's missing in your request.

### Solution

There are two ways to address this issue:

1. **Update your API requests to include contractAddress**:
   - For NFT queries: Include the collection's contract address
   - For payment requests: Include the X402 token contract address
   
2. **Modify the Lambda handler** to look for the contract address in different locations:
   
   ```python
   # In lambda_handler.py
   def lambda_handler(event, context):
       # Extract parameters from various possible locations
       contract_address = None
       
       # Parse body if it exists
       if 'body' in event:
           body = event['body']
           if isinstance(body, str):
               try:
                   body_json = json.loads(body)
                   # Try to find contractAddress in body
                   contract_address = body_json.get('contractAddress')
                   
                   # Check in x402 object if it exists
                   if not contract_address and 'x402' in body_json:
                       contract_address = body_json['x402'].get('contract_address')
               except:
                   pass
       
       # If still not found, check directly in event
       if not contract_address:
           contract_address = event.get('contractAddress')
           
       # Validation
       if not contract_address:
           return {
               'statusCode': 400,
               'body': json.dumps({'error': 'contractAddress is required'})
           }
       
       # Rest of your lambda handler...
   ```

## Frontend Setup for AI Input and Login

The frontend implementation includes:

1. **User Authentication**
2. **CDP Wallet Integration**
3. **NFT Collection Search**
4. **Payment Processing**

### Files Included

1. **`frontend_integration.js`**: JavaScript class that handles all frontend functionality
2. **`nft_payment_ui.html`**: Sample HTML implementation with UI elements
3. **`cdp_wallet_connector.js`**: JavaScript class for CDP wallet integration

### Setup Instructions

1. **Update API Endpoint**:
   - In `frontend_integration.js`, replace the API endpoint with your actual API Gateway URL:
     ```javascript
     const apiEndpoint = 'https://your-api-gateway-url.execute-api.region.amazonaws.com/prod';
     ```

2. **Update X402 Token Contract Address**:
   - In `frontend_integration.js`, update the token contract address in the `getTokenContractAddress()` method:
     ```javascript
     return "0x123456789abcdef123456789abcdef123456789a"; // Replace with actual contract address
     ```

3. **Host the Frontend Files**:
   - Upload the HTML and JavaScript files to your web server or hosting service
   - Make sure CORS is properly configured on your API Gateway to allow requests from your frontend domain

### Key Features

1. **Login System**:
   - User authentication with JWT tokens
   - Token storage in localStorage for persistent sessions

2. **Wallet Connection**:
   - Integration with CDP Wallet
   - Secure session management
   - Transaction signing

3. **NFT Search Interface**:
   - Collection search with contract address input
   - Display of collection information and floor price

4. **Payment Processing**:
   - X402 payment protocol integration
   - CDP Wallet for transaction signing
   - Payment confirmation and transaction registration

### Testing the Implementation

1. Open `nft_payment_ui.html` in your browser
2. Log in using the login form
3. Connect your CDP Wallet
4. Search for an NFT collection (make sure to input the contract address)
5. Initiate a payment for premium analysis
6. Check that the payment is processed correctly

### Troubleshooting

1. **"contractAddress is required" error**:
   - Make sure the contract address is included in all API requests
   - Check the browser console for API request details

2. **Wallet connection issues**:
   - Ensure CDP Wallet extension is installed
   - Check browser console for connection errors

3. **Payment processing failures**:
   - Verify the X402 token contract address is correct
   - Check that the user has sufficient funds for the payment

4. **CORS errors**:
   - Configure your API Gateway to allow requests from your frontend domain
   - Add the appropriate CORS headers to your Lambda responses
