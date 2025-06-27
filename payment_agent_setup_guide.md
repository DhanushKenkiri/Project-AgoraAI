# Setting Up NFT Payment Collaboration Agent in Amazon Bedrock

This document provides detailed instructions for setting up a secure NFT payment collaboration agent in Amazon Bedrock that will work with your existing NFT data Lambda function.

## Prerequisites

- AWS account with access to Amazon Bedrock
- Existing NFT data Lambda function
- Ethereum wallet address to receive payments via X402 protocol
- AWS Lambda, API Gateway, DynamoDB, and KMS permissions
- Base-Sepolia testnet ETH (for testing) or Base/Ethereum Mainnet ETH (for production)

## 1. Deploy the Payment Infrastructure

### Deploy CloudFormation Stack

1. Navigate to the AWS CloudFormation console
2. Click "Create stack" with new resources
3. Upload the `nft_payment_stack.yaml` file
4. Set parameters:
   - Environment: Choose `dev`, `staging`, or `prod`
   - KmsAdminRole: Enter the ARN of a role that can administer KMS keys
5. Click through the stack creation wizard and acknowledge IAM capabilities
6. Wait for stack creation to complete (~5-10 minutes)

### Capture Resource Outputs

After the stack is created, note the following outputs for later use:
- `PaymentApiEndpoint`
- `PaymentLambdaArn`
- `PaymentTableName`

awsawsaws sts get-caller-identity

### Store Configuration in AWS Secrets Manager

1. Navigate to the AWS Secrets Manager console
2. Click "Store a new secret"
3. Select "Other type of secret"
4. Add the following key-value pairs:
   - PAYMENT_ADDRESS: Your Ethereum wallet address that will receive payments (format: 0x...)
   - TOKEN_CONTRACT_ADDRESS: Contract address of the ERC-20 token you'll accept (or leave empty for ETH)
   - NETWORK: The blockchain network to use (base-sepolia for testing, base or ethereum for production)
   - CDP_WALLET_REDIRECT_URL: Your application's redirect URL for wallet connections
   - CDP_PAYMENT_CALLBACK_URL: Your application's callback URL for payment notifications
   - RPC_URL: The RPC endpoint for blockchain interactions (e.g., https://sepolia.base.org)
   - RESOURCE_PRICES: A JSON object mapping resource paths to prices, for example:
     ```json
     {
       "/api/nft/details": {"amount": 0.001, "currency": "ETH"},
       "/api/collection/rarity": {"amount": 0.005, "currency": "ETH"},
       "/api/premium/analysis": {"amount": 0.01, "currency": "USDC"}
     }
     ```
5. Click "Next"
6. Name the secret `nft-payment-credentials-{environment}` (replace {environment} with dev, staging, or prod)
7. Add tags if needed and click through to create the secret
8. Note the ARN of the created secret for the next step

### Update Lambda Environment Variables

1. Navigate to the AWS Lambda console
2. Select your Payment Lambda function
3. Go to the "Configuration" tab and select "Environment variables"
4. Add the following environment variables:
   - SECRETS_MANAGER_ARN: The ARN of the secret created above
   - PAYMENT_LAMBDA_ARN: The ARN from CloudFormation outputs
   - KMS_KEY_ID: The KMS key ID from CloudFormation outputs
   - ENVIRONMENT: dev, staging, or prod
   - TRANSACTION_TABLE_NAME: The DynamoDB table name from CloudFormation outputs (NFTPaymentTransactions-{environment})
   - WALLET_SESSIONS_TABLE: The DynamoDB table for wallet sessions (NFTWalletSessions-{environment})
   - ALERT_EMAIL: Email for payment alerts
   - MAX_PAYMENT_AMOUNT: Maximum allowed payment amount (default: 10.0)
   - MIN_PAYMENT_AMOUNT: Minimum allowed payment amount (default: 0.001)
   - DEFAULT_CURRENCY: Default payment currency (default: ETH)
   - SUPPORTED_CURRENCIES: Comma-separated list of supported currencies (default: ETH,USDC,USDT,DAI)
   - WAITING_TIMEOUT: Payment timeout in seconds (default: 300)
5. Click "Save"

### Update IAM Role

1. Navigate to the IAM console
2. Find the execution role for your Lambda functions
3. Add a policy to allow reading from Secrets Manager:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "secretsmanager:GetSecretValue"
               ],
               "Resource": "arn:aws:secretsmanager:*:*:secret:nft-payment-credentials-*"
           }
       ]
   }
   ```

### Update Code to Use Secure Configuration

1. Replace the original `payment_config.py` with the secure `secure_payment_config.py` version which loads credentials from AWS Secrets Manager
2. Update any imports in your code to use the new configuration module:
   ```python
   # Change this
   from payment_config import load_payment_config
   
   # To this
   from secure_payment_config import load_payment_config
   ```

### Deploy Updated Lambda Code

1. Update your deployment package to include the new files:
   ```bash
   python create_lambda_package.py --include-payment
   ```

2. Deploy the updated Lambda package to both your main NFT data Lambda and the payment Lambda:
   ```bash
   aws lambda update-function-code --function-name YourMainLambdaName --zip-file fileb://lambda_deployment_package.zip
   aws lambda update-function-code --function-name PaymentHandler-dev --zip-file fileb://lambda_deployment_package.zip
   ```

3. Verify environment variables are set:
   ```bash
   aws lambda get-function-configuration --function-name PaymentHandler-dev | jq .Environment.Variables
   ```

## 3. Create Payment Collaboration Agent in Amazon Bedrock

### Create a New Bedrock Agent

1. Navigate to the Amazon Bedrock console
2. Click on "Agents" in the left navigation
3. Click "Create agent"
4. Enter basic details:
   - Name: `NFT Payment Agent`
   - Description: `Collaboration agent for secure NFT payments via CDP Wallet and X402`
   - Choose a foundation model (Claude recommended for financial transactions)
5. Click "Next"

### Configure Agent Instructions

In the agent instructions field, enter the following:

```
You are a specialized payment processing agent for NFT transactions. Your role is to securely handle wallet connections and payment processing using the X402 payment protocol and CDP Wallet. 

SECURITY GUIDELINES:
1. NEVER ask for private keys or seed phrases
2. ALWAYS verify wallet addresses are valid (0x format, 42 characters)
3. ALWAYS validate transaction amounts
4. NEVER proceed with transactions if there are any security concerns
5. DO NOT provide technical assistance for bypassing security measures
6. ALWAYS warn users about potential scams or suspicious activities
7. ONLY support the following currencies: ETH, USDC, USDT, DAI

TRANSACTION GUIDELINES:
1. The X402 protocol allows for micropayments as low as $0.001 with 2-second settlements and no percentage fees
2. When a user wants to make a payment, guide them through connecting their wallet
3. Explain that payments will be processed on Base (or Base-Sepolia for testing)
4. After payment initiation, provide the payment URL or QR code for completing the transaction
5. Verify transaction status before confirming success
6. Provide transaction IDs and blockchain explorer links for transaction verification
7. Maximum transaction amount is 10 ETH or equivalent

HANDLING USER INTERACTIONS:
1. Be polite and professional at all times
2. Clearly explain the benefits of the X402 protocol (low fees, fast settlement, minimal payments)
3. Provide transaction status updates when requested
4. Answer basic questions about the X402 payment protocol and CDP Wallet
5. If the user asks about transaction details outside your knowledge, direct them to check their wallet or the blockchain explorer
6. If a technical error occurs, provide a reference ID and apologize for the inconvenience

When handling payments, follow this exact sequence:
1. Detect payment intent from user query
2. Request wallet connection if not already connected
3. Validate payment details (amount, currency, NFT contract, token ID)
4. Provide payment requirements using the X402 protocol format
5. Generate and share the payment URL for completing the transaction
6. Guide user to complete payment in their wallet
7. Verify transaction completion on the blockchain
8. Confirm successful payment and provide transaction details and receipt
```

### Create Action Group

1. In the "Action groups" section, click "Add action group"
2. Enter basic details:
   - Name: `X402PaymentProcessing`
   - Description: `Handles secure NFT payments via X402 payment protocol`

3. Create a new action with the following details:
   - Name: `ProcessPayment`
   - Description: `Processes an NFT payment using X402 protocol`
   - API method: POST
   - API URL: Use the `PaymentApiEndpoint` from CloudFormation outputs
   - Request parameters:
     ```json
     {
       "action": {
         "type": "string",
         "required": true,
         "description": "The payment action to perform: connect_wallet, initiate_payment, confirm_payment, check_status, payment_required_response"
       },
       "wallet_address": {
         "type": "string",
         "required": false,
         "description": "The user's wallet address starting with 0x"
       },
       "resource": {
         "type": "string",
         "required": false,
         "description": "The resource path being requested"
       },
       "amount": {
         "type": "number",
         "required": false,
         "description": "Payment amount in ETH or other currency"
       },
       "currency": {
         "type": "string",
         "required": false,
         "description": "Currency code (ETH, USDC, USDT, DAI)"
       },
       "nft_contract": {
         "type": "string",
         "required": false,
         "description": "The NFT contract address"
       },
       "nft_token_id": {
         "type": "string",
         "required": false,
         "description": "The NFT token ID"
       },
       "payment_id": {
         "type": "string",
         "required": false,
         "description": "Payment ID for status checks or confirmations"
       },
       "transaction_hash": {
         "type": "string",
         "required": false,
         "description": "Blockchain transaction hash"
       }
     }
     ```
   - Response parameters:
     ```json
     {
       "success": {
         "type": "boolean",
         "description": "Whether the payment action was successful"
       },
       "error": {
         "type": "string",
         "description": "Error message if the action failed"
       },
       "payment_id": {
         "type": "string",
         "description": "The unique payment identifier"
       },
       "payment_url": {
         "type": "string",
         "description": "URL for completing the payment"
       },
       "paymentRequirements": {
         "type": "object",
         "description": "X402 payment requirements object"
       },
       "status": {
         "type": "string",
         "description": "Payment status (pending, completed, failed)"
       },
       "wallet_address": {
         "type": "string",
         "description": "The user's wallet address"
       },
       "transaction_hash": {
         "type": "string",
         "description": "The blockchain transaction hash"
       },
       "explorer_url": {
         "type": "string",
         "description": "Blockchain explorer URL to view transaction"
       }
     }
     ```

4. Add Lambda integration:
   - AWS Lambda function ARN: Use the `PaymentLambdaArn` from CloudFormation outputs
   - Provide necessary Lambda permissions

5. Click "Add"

### Configure API Schema

1. In the "API schema" section, paste the following OpenAPI schema:

```yaml
openapi: 3.0.0
info:
  title: X402 Payment API
  description: API for processing NFT payments via X402 payment protocol
  version: '1.0'
paths:
  /payment:
    post:
      summary: Process a payment request
      description: Handles wallet connections and X402 payments
      operationId: processPayment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                action:
                  type: string
                  enum: [connect_wallet, initiate_payment, confirm_payment, check_status, payment_required_response]
                  description: The payment action to perform
                resource:
                  type: string
                  description: The resource path being requested
                wallet_address:
                  type: string
                  pattern: '^0x[a-fA-F0-9]{40}$'
                  description: The user's wallet address
                amount:
                  type: number
                  minimum: 0.0001
                  maximum: 100
                  description: Payment amount
                currency:
                  type: string
                  enum: [ETH, USDC, USDT, DAI]
                  description: Currency code
                nft_contract:
                  type: string
                  pattern: '^0x[a-fA-F0-9]{40}$'
                  description: NFT contract address
                nft_token_id:
                  type: string
                  description: NFT token ID
                payment_id:
                  type: string
                  description: Payment identifier
                transaction_hash:
                  type: string
                  description: Blockchain transaction hash
              required:
                - action
      responses:
        '200':
          description: Successful operation
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    description: Whether the operation was successful
                  error:
                    type: string
                    description: Error message if unsuccessful
                  payment_id:
                    type: string
                    description: Unique payment identifier
                  payment_url:
                    type: string
                    description: URL for completing payment
                  paymentRequirements:
                    type: object
                    description: X402 payment requirements object
                    properties:
                      x402Version:
                        type: integer
                        description: X402 protocol version
                      accepts:
                        type: array
                        description: List of acceptable payment methods
                        items:
                          type: object
                  status:
                    type: string
                    description: Payment status
                    enum: [pending, completed, failed]
                  wallet_address:
                    type: string
                    description: User's wallet address
                  transaction_hash:
                    type: string
                    description: Blockchain transaction hash
                  explorer_url:
                    type: string
                    description: URL to view transaction on blockchain explorer
        '402':
          description: Payment required
          content:
            application/json:
              schema:
                type: object
                properties:
                  x402Version:
                    type: integer
                  accepts:
                    type: array
                    items:
                      type: object
                  error:
                    type: string
        '400':
          description: Invalid request
        '500':
          description: Server error
```

### Test the Agent

1. Click "Preview" to test the agent
2. Try the following test prompts:
   - "I want to buy an NFT"
   - "Connect my wallet"
   - "Make a payment of 0.1 ETH for NFT with contract 0x1234...5678 and token ID 123"
   - "Check the status of my payment"

### Create Advanced Prompt Templates

Create the following prompt templates for common payment scenarios:

1. **Wallet Connection Prompt:**
   ```
   I need to help the user connect their CDP wallet.
   
   User has requested to: {{user_request}}
   
   I should guide them through the wallet connection process using the CDP Wallet integration.
   
   Steps to include:
   1. Explain why wallet connection is needed
   2. Provide the wallet connection URL
   3. Explain how to complete the connection in their wallet app
   4. Verify the connection was successful
   ```

2. **Payment Initiation Prompt:**
   ```
   I need to help the user initiate an NFT payment.
   
   Payment details:
   - NFT Contract: {{contract_address}}
   - Token ID: {{token_id}}
   - Amount: {{amount}} {{currency}}
   - Wallet: {{wallet_address}}
   
   Steps to include:
   1. Confirm the payment details
   2. Warn about verifying the contract address
   3. Provide the payment URL
   4. Explain how to approve the transaction in their wallet
   5. Inform about gas fees and processing time
   ```

3. **Payment Confirmation Prompt:**
   ```
   I need to verify a completed NFT payment.
   
   Transaction details:
   - Payment ID: {{payment_id}}
   - Transaction Hash: {{transaction_hash}}
   
   Steps to include:
   1. Check and report the transaction status
   2. Provide confirmation details if successful
   3. Suggest troubleshooting steps if failed
   4. Offer links to view the transaction on the blockchain
   ```

## 4. Integrate with Main NFT Agent

### Configure Collaboration

1. In your main NFT data agent settings, navigate to "Collaborations"
2. Click "Add collaboration"
3. Select the NFT Payment Agent
4. Define collaboration parameters:
   - Name: `PaymentProcessing`
   - Description: `Handles NFT payments securely`
   - Trigger keywords: payment, buy, purchase, wallet, connect wallet, pay, transaction

### Define Hand-off Criteria

Configure when your NFT data agent should hand off to the payment agent:

1. Create the following utterance patterns:
   - "I want to buy this NFT"
   - "How do I pay for this NFT"
   - "Connect my wallet"
   - "Process payment for *"
   - "Check my payment status"
   - "Verify my transaction"

2. Ensure the main agent knows to hand off payment-related queries

## 5. Security Recommendations

1. **Enable CloudTrail Logging**: Monitor all API calls to the payment Lambda function
   ```bash
   aws cloudtrail create-trail --name PaymentAuditTrail --s3-bucket-name your-secure-bucket --is-multi-region-trail
   aws cloudtrail start-logging --name PaymentAuditTrail
   ```

2. **Set Up CloudWatch Alarms**: Monitor for suspicious payment activity
   ```bash
   aws cloudwatch put-metric-alarm --alarm-name HighValuePaymentAlert \
     --metric-name InvokeCount \
     --namespace AWS/Lambda \
     --statistic Sum \
     --period 60 \
     --threshold 5 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 1 \
     --dimensions Name=FunctionName,Value=PaymentHandler-prod \
     --alarm-actions arn:aws:sns:region:account-id:PaymentAlerts
   ```

3. **Implement IP-Based Rate Limiting**: Add a usage plan in API Gateway
   ```bash
   aws apigateway create-usage-plan --name PaymentRateLimiting \
     --throttle burstLimit=10,rateLimit=2 \
     --quota limit=100,period=DAY
   ```

4. **Enable AWS WAF**: Protect against common web exploits
   ```bash
   aws wafv2 create-web-acl --name PaymentAPIProtection \
     --scope REGIONAL \
     --default-action Allow={} \
     --rules file://payment-waf-rules.json
   ```

5. **Configure DynamoDB Encryption**: Ensure all payment data is encrypted
   ```bash
   aws dynamodb update-table --table-name NFTPaymentTransactions-prod \
     --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=key-id
   ```

6. **Setup Secret Rotation**: Configure automatic rotation for your API keys
   ```bash
   aws secretsmanager create-secret --name nft-payment-credentials-rotation \
     --secret-string '{"rotationSchedule":"30d"}' \
     --description "Configuration for payment API key rotation"
   
   aws secretsmanager rotate-secret --secret-id nft-payment-credentials-prod \
     --rotation-lambda-arn arn:aws:lambda:region:account-id:function:SecretRotationLambda \
     --rotation-rules '{"AutomaticallyAfterDays": 30}'
   ```

7. **Implement VPC Endpoints**: For secure communication between services
   ```bash
   aws ec2 create-vpc-endpoint --vpc-id your-vpc-id \
     --service-name com.amazonaws.region.secretsmanager \
     --vpc-endpoint-type Interface
   
   aws ec2 create-vpc-endpoint --vpc-id your-vpc-id \
     --service-name com.amazonaws.region.dynamodb \
     --vpc-endpoint-type Gateway
   ```

8. **Setup AWS Config Rules**: Monitor for compliance
   ```bash
   aws configservice put-config-rule --config-rule file://config-rules.json
   ```

9. **Enable AWS GuardDuty**: For intelligent threat detection
   ```bash
   aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES
   ```

10. **Implement Least Privilege IAM Policies**: Review and refine IAM permissions regularly
    ```bash
    aws iam generate-service-last-accessed-details --arn arn:aws:iam::account-id:role/PaymentLambdaRole
    ```

## 6. Deployment Verification Checklist

Before going live, verify the following:

- [ ] Payment Lambda has necessary permissions to access Secrets Manager
- [ ] KMS encryption is properly configured for sensitive data
- [ ] DynamoDB table exists and is encrypted
- [ ] API Gateway endpoints are secured with WAF and proper authorization
- [ ] CloudWatch alarms are configured for anomaly detection
- [ ] All API keys and secrets are properly stored in AWS Secrets Manager (NOT in code or environment variables)
- [ ] Lambda environment variables point to correct Secret ARNs
- [ ] Secret rotation policy is configured
- [ ] Test transactions complete successfully
- [ ] Error handling works correctly without exposing sensitive information
- [ ] Transaction records are properly stored and encrypted
- [ ] CloudTrail logging is enabled with proper retention period
- [ ] Rate limiting is in place to prevent abuse
- [ ] VPC endpoints are configured for private AWS service access
- [ ] Agent handoff works correctly with proper authentication
- [ ] Payment validation logic is functioning with proper input sanitization
- [ ] Secret access is properly logged and monitored
- [ ] Network security groups restrict access appropriately
- [ ] Lambda functions run in private subnets when possible

## 7. Monitoring and Maintenance

1. **Regular Security Reviews**: Schedule monthly security reviews
2. **API Key Rotation**: Rotate X402 and CDP Wallet API keys quarterly
3. **Dependency Updates**: Keep all libraries updated to patch security vulnerabilities
4. **Transaction Audits**: Regularly audit transaction records for anomalies
5. **Performance Monitoring**: Set up dashboards to monitor payment processing times and success rates

## Support and Troubleshooting

Contact information for support:
- X402 Protocol Support: Visit the [X402 GitHub repository](https://github.com/coinbase/x402/issues)
- CDP Wallet Support: Visit [Coinbase Developer documentation](https://docs.cdp.coinbase.com/)
- Internal Support: nft-payments-support@yourcompany.com

Common troubleshooting steps:
1. Check CloudWatch logs for specific error messages
2. Verify your Ethereum wallet address is correctly configured
3. Check network connectivity to blockchain nodes
4. Verify wallet addresses are in the correct format
5. Check transaction status on the blockchain explorer for Base or Base-Sepolia

## 8. X402 and CDP Wallet Integration Verification

After deploying your payment infrastructure, verify the X402 and CDP Wallet integration using these steps:

### Verify Environment Configuration

1. Check that all required environment variables are set:
   ```bash
   aws lambda get-function-configuration --function-name PaymentHandler-dev | jq .Environment.Variables
   ```

2. Verify secrets are accessible:
   ```bash
   aws lambda invoke --function-name PaymentHandler-dev --payload '{"action":"test_config"}' output.json
   cat output.json
   ```

### Test Wallet Connection Flow

1. Test the wallet connection flow:
   ```bash
   aws lambda invoke --function-name PaymentHandler-dev --payload '{"action":"connect_wallet"}' connect_wallet_output.json
   cat connect_wallet_output.json
   ```

2. Verify the response includes a valid wallet connection URL.

### Test Payment Flow

1. Test a payment required response:
   ```bash
   aws lambda invoke --function-name PaymentHandler-dev --payload '{"action":"payment_required_response", "resource":"/api/nft/details"}' payment_required_output.json
   cat payment_required_output.json
   ```

2. Verify the response includes a valid X402 payment requirements object with the correct:
   - X402 protocol version (should be 1)
   - Network configuration (base-sepolia for testing)
   - Payment address
   - Resource pricing

3. Test payment initiation:
   ```bash
   aws lambda invoke --function-name PaymentHandler-dev --payload '{"action":"initiate_payment", "wallet_address":"0x123...", "amount":0.001, "currency":"ETH", "resource":"/api/nft/details"}' initiate_payment_output.json
   cat initiate_payment_output.json
   ```

4. Verify transaction records are stored in DynamoDB:
   ```bash
   aws dynamodb scan --table-name NFTPaymentTransactions-dev
   ```

### Common X402 Integration Issues

If you encounter issues, check the following:

1. **Network Configuration**: Ensure the NETWORK setting in Secrets Manager matches a supported X402 network:
   - base-sepolia (recommended for testing)
   - base (for production)
   - ethereum-sepolia (for Ethereum testnet)
   - ethereum (for Ethereum mainnet)

2. **RPC URL Connectivity**: Verify the RPC endpoint is accessible and supports the necessary JSON-RPC methods for transaction verification.

3. **CDP Wallet Redirect URL**: Make sure the CDP_WALLET_REDIRECT_URL is properly set and configured to handle the OAuth-like wallet connection flow.

4. **Resource Pricing**: Verify RESOURCE_PRICES is a valid JSON object with proper pricing information.

5. **Payment Transaction Timeouts**: If transactions are timing out, check the WAITING_TIMEOUT setting (default is 300 seconds).
