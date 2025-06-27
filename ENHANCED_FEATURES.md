# Enhanced Lambda NFT Wallet Features

This document describes the enhanced features added to the Lambda function for NFT wallet integration, image support, and Bedrock Agent integration.

## New Endpoints

### Wallet Management

- **Wallet Connect**
  - Path: `/wallet/connect`
  - Method: `POST`
  - Body: 
    ```json
    {
      "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
      "wallet_type": "metamask"
    }
    ```
  - Headers: `x-session-id` (optional, one will be generated if not provided)
  - Response: Wallet connection details with session ID

- **Wallet Status**
  - Path: `/wallet/status`
  - Method: `GET`
  - Headers: `x-session-id`
  - Response: Current wallet connection status

- **Wallet Disconnect**
  - Path: `/wallet/disconnect`
  - Method: `POST`
  - Headers: `x-session-id`
  - Response: Confirmation of disconnection

### NFT Images

- **Get Wallet NFT Images**
  - Path: `/wallet/nft-images`
  - Method: `GET`
  - Query Parameters: 
    - `wallet_address` or `address`: The wallet address to query
    - `limit` (optional): Number of NFTs to return
  - Headers: `x-session-id` (optional, used if wallet_address not provided)
  - Response: List of NFTs with image URLs and metadata

- **Standard NFT Endpoint with Images**
  - Path: `/wallet/nfts`
  - Method: `GET`
  - Query Parameters: 
    - `wallet_address` or `address`: The wallet address to query
    - `include_images`: Set to "true" to include image URLs
  - Headers: `x-session-id` (optional, used if wallet_address not provided)
  - Response: List of NFTs with optional image URLs

### Image Processing

- **Image Upload**
  - Path: `/image/upload`
  - Method: `POST`
  - Body: 
    ```json
    {
      "image_data": "data:image/jpeg;base64,...",
      "analyze": true
    }
    ```
  - Headers: `x-session-id`
  - Response: Image ID and analysis results if requested

- **Image Retrieval**
  - Path: `/image`
  - Method: `GET`
  - Query Parameters: `id` (Image ID)
  - Response: Image URL and metadata

## Integration with Bedrock Agent

The Bedrock Agent has been enhanced to support:

1. **Wallet operations**: Connect, disconnect, and check wallet status
2. **NFT retrieval**: Get NFTs with rich image information
3. **Image handling**: Upload, analyze, and retrieve images

## Session Management

All endpoints now support persistent session management via the `x-session-id` header. This enables wallet state to be maintained across requests.

## Usage Examples

### Frontend Integration for Wallet Connect

```javascript
// Connect wallet
async function connectWallet(walletAddress) {
  const response = await fetch('https://your-api-url/wallet/connect', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-session-id': sessionId // Optional, can be stored from prior interactions
    },
    body: JSON.stringify({
      wallet_address: walletAddress,
      wallet_type: 'metamask'
    })
  });
  
  const result = await response.json();
  
  // Store the session ID for future requests
  if (result.session_id) {
    sessionId = result.session_id;
    localStorage.setItem('wallet_session_id', sessionId);
  }
  
  return result;
}

// Check wallet status
async function checkWalletStatus() {
  const sessionId = localStorage.getItem('wallet_session_id');
  if (!sessionId) return { connected: false };
  
  const response = await fetch('https://your-api-url/wallet/status', {
    headers: {
      'x-session-id': sessionId
    }
  });
  
  return await response.json();
}

// Get NFTs with images
async function getWalletNFTs() {
  const sessionId = localStorage.getItem('wallet_session_id');
  if (!sessionId) return { error: 'No active wallet session' };
  
  const response = await fetch('https://your-api-url/wallet/nft-images', {
    headers: {
      'x-session-id': sessionId
    }
  });
  
  return await response.json();
}

// Upload an image
async function uploadImage(imageFile) {
  const sessionId = localStorage.getItem('wallet_session_id');
  
  // Convert file to base64
  const reader = new FileReader();
  reader.readAsDataURL(imageFile);
  
  return new Promise((resolve, reject) => {
    reader.onload = async () => {
      const base64data = reader.result;
      
      const response = await fetch('https://your-api-url/image/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': sessionId || ''
        },
        body: JSON.stringify({
          image_data: base64data,
          analyze: true
        })
      });
      
      resolve(await response.json());
    };
    reader.onerror = reject;
  });
}
```

### Using with Bedrock Agent

When using the Bedrock Agent, the same session management will work automatically. You can pass the same `x-session-id` header to maintain wallet context across interactions.

## Deployment

Use the provided deployment script to package and update your Lambda function:

```bash
python deploy_enhanced_lambda.py --function-name YourLambdaFunctionName --region us-west-2
```

## Testing

To test the new endpoints, run:

```bash
python test_endpoints.py
```

This will verify that all endpoints are functioning correctly.

## Requirements

The new modules require:
- AWS S3 bucket for image storage
- Optional: AWS Rekognition for image analysis
- AWS Bedrock Agent for AI capabilities

## Environment Variables

- `IMAGE_BUCKET`: S3 bucket name for image storage (default: 'nft-image-analysis-bucket')
- `IMAGE_EXPIRATION_DAYS`: Number of days before image URLs expire (default: 30)
- `AWS_REGION`: AWS region for S3 and other services
