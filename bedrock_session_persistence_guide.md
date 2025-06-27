# AWS Bedrock Agent Session Persistence Guide

This document explains how to implement and deploy session persistence for the AWS Bedrock Agent, allowing it to remember user data like wallet addresses between conversations.

## Overview

The session persistence system consists of:

1. A DynamoDB table to store session data
2. A session manager module for storing/retrieving data
3. Updated Bedrock agent adapter that uses the session manager
4. CloudFormation template for infrastructure deployment

## Implementation Details

### 1. DynamoDB Table Structure

The `NFTBedrockSessions` table uses the following schema:

- **Partition Key**: `session_id` (String) - The unique Bedrock session ID
- **TTL Attribute**: `expiration` (Number) - Unix timestamp for automatic expiration
- **Data Attribute**: `data` (Map) - JSON containing user data, including wallet_address
- **Optional**: `user_id` (String) - For multi-user scenarios

### 2. Session Manager Module

The `session_manager.py` module provides functions for:

- `store_user_data(session_id, user_id, data)` - Store arbitrary user data
- `get_user_data(session_id, user_id)` - Retrieve stored user data
- `store_wallet_address(session_id, wallet_address, user_id)` - Specifically store a wallet address
- `get_wallet_address(session_id, user_id)` - Retrieve a stored wallet address
- `create_dynamodb_table(table_name, region)` - Create the DynamoDB table if needed

### 3. Bedrock Agent Adapter Integration

The Bedrock agent adapter has been updated to:

1. Extract session_id from Bedrock requests
2. Check for stored wallet address before requiring user input
3. Store wallet address when provided by the user
4. Use the stored wallet address in API calls

### 4. Deployment Instructions

#### 4.1. Create the DynamoDB Table

You can create the DynamoDB table using:

1. The CloudFormation template:
   ```
   aws cloudformation deploy --template-file bedrock_sessions_dynamodb.yaml \
     --stack-name bedrock-sessions \
     --parameter-overrides Environment=prod
   ```

2. Or using the provided Python script:
   ```
   python create_bedrock_sessions_table.py NFTBedrockSessions-prod us-east-1
   ```

#### 4.2. Update Lambda Environment Variables

Add the following environment variable to your Lambda function:

- `BEDROCK_SESSIONS_TABLE`: The name of the DynamoDB table (e.g., `NFTBedrockSessions-prod`)

#### 4.3. Update Lambda IAM Policy

Ensure your Lambda function's execution role has the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/NFTBedrockSessions*"
        }
    ]
}
```

#### 4.4. Redeploy Lambda Function

Update your Lambda deployment package to include the new session_manager.py file:

```
python create_bedrock_optimized.py
```

Then upload the new package to AWS Lambda.

## Testing

### Local Testing

Test the session manager functionality locally using:

```
python test_session_manager.py
```

For testing with DynamoDB Local:

```
python test_session_manager.py --local
```

### AWS Testing

Test the integration in AWS by:

1. Invoking the Lambda function directly with a test event that includes a session_id
2. Using the Bedrock agent console to start a new conversation
3. Providing a wallet address and then starting a new conversation to verify it's remembered

## Troubleshooting

1. **Data not persisting**: Check the DynamoDB table for entries matching the session_id.
2. **Lambda permission issues**: Verify IAM permissions for DynamoDB access.
3. **Session not found**: Check if Bedrock agent is passing the same session_id across conversations.

## Security Considerations

1. Session data is stored with a TTL (30 days by default)
2. Table is encrypted with AWS-managed keys
3. IAM policies restrict access to only the Lambda function

## Limitations

1. Different devices/browsers will have different session IDs
2. Users need to be identified across devices if cross-device persistence is needed
