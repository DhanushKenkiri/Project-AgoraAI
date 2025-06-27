# AWS Lambda Deployment Guide for CDP Wallet and X402 Integration

This guide covers the steps to deploy your CDP Wallet and X402 Payment integration to AWS Lambda and configure all necessary resources.

## Prerequisites

1. AWS CLI installed and configured
2. Appropriate AWS permissions (Lambda, CloudFormation, API Gateway, DynamoDB, KMS)
3. Python 3.8+ and pip installed locally
4. Generated deployment package (`cdp_wallet_x402_lambda_package.zip`)

## Deployment Options

Choose one of the following deployment methods:

### Option 1: CloudFormation Deployment (Recommended)

This approach deploys all resources (Lambda, API Gateway, DynamoDB, KMS) in a single template.

1. **Update CloudFormation Template**

   Edit `nft_payment_stack.yaml` to update the Lambda function code:

   ```yaml
   PaymentLambdaFunction:
     Type: AWS::Lambda::Function
     Properties:
       FunctionName: !Sub 'PaymentHandler-${Environment}'
       Handler: lambda_handler.lambda_handler  # Updated handler
       Role: !GetAtt PaymentLambdaRole.Arn
       Code:
         S3Bucket: your-deployment-bucket  # Add your S3 bucket name
         S3Key: cdp_wallet_x402_lambda_package.zip  # Path to your deployment package
       Runtime: python3.9
       Timeout: 60
       MemorySize: 512
       Environment:
         Variables:
           ENVIRONMENT: !Ref Environment
           TRANSACTION_TABLE_NAME: !Ref PaymentTransactionTable
           WALLET_SESSIONS_TABLE: !Ref WalletSessionsTable
           KMS_KEY_ID: !Ref PaymentEncryptionKey
           CDP_WALLET_APP_ID: "your_cdp_app_id_here"
           CDP_API_ENDPOINT: "https://api.cdp.io"
           NETWORK: "base-sepolia"
           TOKEN_CONTRACT_ADDRESS: "0x..."
           RPC_URL: "https://sepolia.base.org"
   ```

2. **Upload Deployment Package to S3**

   ```bash
   aws s3 mb s3://your-deployment-bucket --region us-east-1
   aws s3 cp cdp_wallet_x402_lambda_package.zip s3://your-deployment-bucket/
   ```

3. **Deploy CloudFormation Stack**

   ```bash
   aws cloudformation deploy \
     --template-file nft_payment_stack.yaml \
     --stack-name cdp-x402-payment-stack \
     --parameter-overrides Environment=dev \
     --capabilities CAPABILITY_IAM
   ```

4. **Get API Endpoint**

   ```bash
   aws cloudformation describe-stacks \
     --stack-name cdp-x402-payment-stack \
     --query "Stacks[0].Outputs[?OutputKey=='PaymentApiEndpoint'].OutputValue" \
     --output text
   ```

### Option 2: Direct Lambda Deployment

Use this approach if you already have some AWS resources set up and just want to update the Lambda function.

1. **Create Lambda Function (if it doesn't exist)**

   ```bash
   aws lambda create-function \
     --function-name PaymentHandler-dev \
     --runtime python3.9 \
     --role arn:aws:iam::<account-id>:role/PaymentLambdaRole \
     --handler lambda_handler.lambda_handler \
     --zip-file fileb://cdp_wallet_x402_lambda_package.zip \
     --timeout 60 \
     --memory-size 512
   ```

2. **Update Existing Lambda Function**

   ```bash
   aws lambda update-function-code \
     --function-name PaymentHandler-dev \
     --zip-file fileb://cdp_wallet_x402_lambda_package.zip
   ```

3. **Configure Environment Variables**

   ```bash
   aws lambda update-function-configuration \
     --function-name PaymentHandler-dev \
     --environment "Variables={CDP_WALLET_APP_ID=your_cdp_app_id_here,CDP_API_ENDPOINT=https://api.cdp.io,NETWORK=base-sepolia,TOKEN_CONTRACT_ADDRESS=0x...,RPC_URL=https://sepolia.base.org,TRANSACTION_TABLE_NAME=NFTPaymentTransactions-dev,WALLET_SESSIONS_TABLE=NFTWalletSessions-dev}"
   ```

## Configure API Gateway (If Using Option 2)

If you deployed using Option 2 and need to set up API Gateway:

1. **Create REST API**

   ```bash
   api_id=$(aws apigateway create-rest-api \
     --name "CDP-X402-API" \
     --description "API for CDP Wallet and X402 Payment Integration" \
     --endpoint-configuration "types=REGIONAL" \
     --query "id" --output text)
   ```

2. **Get Root Resource ID**

   ```bash
   root_id=$(aws apigateway get-resources \
     --rest-api-id $api_id \
     --query "items[0].id" \
     --output text)
   ```

3. **Create API Resources**

   ```bash
   # Create CDP Wallet Resource
   cdp_resource=$(aws apigateway create-resource \
     --rest-api-id $api_id \
     --parent-id $root_id \
     --path-part "cdp" \
     --query "id" --output text)
   
   # Create wallet sub-resource
   wallet_resource=$(aws apigateway create-resource \
     --rest-api-id $api_id \
     --parent-id $cdp_resource \
     --path-part "wallet" \
     --query "id" --output text)
   
   # Create X402 Resource
   x402_resource=$(aws apigateway create-resource \
     --rest-api-id $api_id \
     --parent-id $root_id \
     --path-part "x402" \
     --query "id" --output text)
   
   # Create payment sub-resource
   payment_resource=$(aws apigateway create-resource \
     --rest-api-id $api_id \
     --parent-id $x402_resource \
     --path-part "payment" \
     --query "id" --output text)
   ```

4. **Configure Methods and Integrations**

   See the AWS CLI documentation for detailed instructions on setting up methods and integrations with Lambda.

## Testing the Deployment

1. **Test API Endpoints**

   ```bash
   # Test wallet connect endpoint
   curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/cdp/wallet/connect \
     -H "Content-Type: application/json" \
     -d '{"wallet_address": "0x1234...5678"}'
   
   # Test payment requirements endpoint
   curl -X GET "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/x402/payment/requirements?resource=/premium/123"
   ```

2. **Test Using the Demo Page**

   Update the API endpoints in the demo HTML pages to point to your deployed API.

## Troubleshooting

1. **CloudWatch Logs**

   Lambda execution logs are stored in CloudWatch. Check them for errors:
   
   ```bash
   aws logs get-log-events \
     --log-group-name /aws/lambda/PaymentHandler-dev \
     --log-stream-name "latest"
   ```

2. **Common Issues**

   - **CORS Errors**: Add appropriate CORS headers to your API Gateway configuration
   - **Permission Issues**: Check the IAM role attached to Lambda
   - **Cold Start Latency**: Lambda may be slow on first execution, consider using provisioned concurrency
   - **Missing Environment Variables**: Verify all required environment variables are set

3. **Testing Tools**

   - Use Postman or Insomnia for detailed API testing
   - Lambda console allows direct function invocation for testing

## Security Considerations

1. **API Security**

   - Add authentication to API Gateway (API keys, JWT, etc.)
   - Configure appropriate resource policies

2. **Data Protection**

   - Use KMS for encrypting sensitive data
   - Consider enabling field-level encryption

3. **Monitoring**

   - Set up CloudWatch alarms for error rates
   - Enable AWS X-Ray for tracing

## Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)

## Next Steps

After successful deployment:

1. Test the end-to-end flow with real CDP wallets
2. Set up monitoring and alerts
3. Consider staging/production deployment with CI/CD pipeline
