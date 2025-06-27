# AWS Bedrock Agent Enhanced Implementation Guide

This guide explains the changes made to improve the Bedrock agent integration, focusing on:

1. Making wallet address optional for non-payment queries
2. Implementing rich media responses through REST API
3. Setting up proper AWS Console configurations

## 1. Changes for Optional Wallet Address

### Problem Solved:
Previously, the agent required a wallet address for every query, even those unrelated to payments. This was not user-friendly for a multipurpose agent.

### Implementation Details:

#### 1.1. Updated Handler Functions
The handler functions in `bedrock_agent_adapter.py` were modified to make wallet address optional for non-payment operations:

- `wallet_login_with_session`: Now checks if this is a connection request or just a status check
- `get_wallet_info_with_session`: Added `is_required` parameter to make wallet optional
- `get_wallet_nfts_with_session`: Returns a friendly message for non-wallet users
- `process_payment_with_session`: Still requires wallet address but provides clearer error messages

#### 1.2. Response Enhancements
Responses now include additional fields to help the front-end understand the state:

- `wallet_connected`: Boolean indicating if a wallet is connected
- `needs_wallet`: Boolean indicating if wallet is required for this operation
- `payment_required`: Boolean for payment operations

## 2. Enhanced REST API with Rich Media Support

### Problem Solved:
The original implementation only supported plain text communication. The new implementation enables rich media responses including images and formatted text.

### Implementation Details:

#### 2.1. New Enhanced Bedrock API
Created `enhanced_bedrock_api.py` which:
- Handles REST API requests for the Bedrock agent
- Supports rich media responses
- Maintains session persistence
- Extracts media content from responses

#### 2.2. HTML Client Implementation
Created a comprehensive HTML client (`templates/bedrock_chat_client.html`) that:
- Provides a modern chat interface
- Supports image uploads
- Maintains session persistence using localStorage
- Displays wallet connection status
- Renders markdown and rich content from the agent
- Shows typing indicators and other UI enhancements

#### 2.3. Media Handling
The new implementation supports:
- Image extraction from markdown
- Payment buttons for transactions
- Code block rendering
- Formatted text with markdown

## 3. AWS Console Implementation Steps

Follow these steps to deploy the enhanced integration:

### 3.1. Create DynamoDB Table for Sessions

1. Go to the AWS Console and open the DynamoDB service
2. Click "Create table"
3. Enter table details:
   - Table name: `NFTBedrockSessions-prod` (or your preferred environment suffix)
   - Partition key: `session_id` (String)
4. Under "Table settings", select "Customize settings"
5. Enable "TTL" and set the TTL attribute to `expiration`
6. Click "Create table"

### 3.2. Update Lambda Function Configuration

1. Go to the AWS Lambda console
2. Select your existing Lambda function
3. Add the following environment variables:
   - `BEDROCK_SESSIONS_TABLE`: The name of the DynamoDB table you created (e.g., `NFTBedrockSessions-prod`)
   - `BEDROCK_REGION`: Your AWS region (e.g., `ap-south-1`)
   - `BEDROCK_AGENT_ID`: Your Bedrock agent ID

### 3.3. Update IAM Permissions

1. In the Lambda console, go to the "Configuration" tab
2. Select "Permissions"
3. Click on the execution role to open it in the IAM console
4. Add the following policy to the role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/NFTBedrockSessions*"
        }
    ]
}
```

### 3.4. Deploy Updated Code

1. Create the updated deployment package:

```powershell
python create_bedrock_optimized.py
```

2. Upload the package to AWS Lambda:

```powershell
aws lambda update-function-code --function-name YourLambdaFunction --zip-file fileb://bedrock_lambda_code.zip
```

### 3.5. Configure API Gateway for Rich Media

1. Go to the API Gateway console
2. Select your existing API or create a new one
3. Add the following routes:
   - `/chat` - POST method pointing to your Lambda function
   - `/upload` - POST method pointing to your Lambda function
4. Configure CORS settings:
   - Under "CORS", enable CORS for all origins
   - Allow the following headers: `Content-Type`, `Authorization`
   - Allow the following methods: `GET`, `POST`, `OPTIONS`
5. Deploy the API:
   - Click "Deploy API"
   - Select a stage or create a new one
   - Note the invoke URL for your client

### 3.6. Set Up AWS Bedrock Agent

1. Go to the AWS Bedrock console
2. Select "Agents" from the left menu
3. Create or modify your agent:
   - Enable session persistence in the agent configuration
   - Configure action groups to match your Lambda function
   - Ensure the agent has permissions to invoke your Lambda function
4. Deploy the agent
5. Test the agent in the AWS Bedrock console

### 3.7. Host the HTML Client

1. Create an S3 bucket to host the client:
   - Go to the S3 console
   - Click "Create bucket"
   - Enter a bucket name and select your region
   - Enable "Static website hosting" under the "Properties" tab
   - Set the index document to `bedrock_chat_client.html`
2. Upload the HTML client:
   - Update the `apiEndpoint` in the HTML file to your API Gateway URL
   - Upload the file to the S3 bucket

## 4. Testing the Implementation

### 4.1. End-to-End Testing

1. Open the HTML client in a web browser
2. Test the following scenarios:
   - General query (no wallet required)
   - NFT collection information (optional wallet)
   - Payment request (required wallet)
   - Image upload and analysis

### 4.2. Session Persistence Testing

1. Connect a wallet in the chat interface
2. Close the browser and reopen it
3. Verify that the agent remembers your wallet address
4. Try a payment operation to confirm wallet auto-retrieval

## 5. Troubleshooting

### 5.1. Lambda Execution Issues

If the Lambda function fails to execute:
1. Check CloudWatch Logs for error messages
2. Verify the execution role has proper permissions
3. Ensure all required dependencies are included in the deployment package

### 5.2. API Gateway Issues

If API requests fail:
1. Test the API directly using Postman or curl
2. Check CORS settings if requests fail from the browser
3. Verify the Lambda integration is configured correctly

### 5.3. Bedrock Agent Issues

If the agent doesn't respond as expected:
1. Test the agent directly in the AWS Bedrock console
2. Check the agent action group configuration
3. Review the agent's knowledge base and prompt templates

### 5.4. Session Persistence Issues

If the agent doesn't remember wallet addresses:
1. Check the DynamoDB table for session records
2. Verify the session ID is being passed correctly
3. Confirm the Lambda has permissions to access DynamoDB
