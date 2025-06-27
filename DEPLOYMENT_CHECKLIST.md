# CDP Wallet and X402 Payment Integration Deployment Checklist

Use this checklist to ensure a complete and successful deployment of your CDP Wallet and X402 Payment Integration.

## Pre-Deployment Preparation

- [ ] Review all code for the CDP Wallet and X402 Payment integration
- [ ] Verify all required files are present in your workspace
- [ ] Ensure unit tests pass locally
- [ ] Configure AWS CLI with appropriate credentials
- [ ] Set up environment variables in your configuration files

## Package Creation

- [ ] Create the deployment package:
  ```bash
  python create_cdp_x402_package.py
  ```
- [ ] Verify the resulting `cdp_wallet_x402_lambda_package.zip` file contains all necessary files
- [ ] Check the size of the package (should be less than 250MB for direct upload)

## AWS Resources Preparation

- [ ] Create an S3 bucket for storing the Lambda package (if using CloudFormation):
  ```bash
  aws s3 mb s3://your-deployment-bucket --region us-east-1
  ```
- [ ] Upload the deployment package to S3:
  ```bash
  aws s3 cp cdp_wallet_x402_lambda_package.zip s3://your-deployment-bucket/
  ```
- [ ] Update CloudFormation template with proper S3 bucket and key references
- [ ] Ensure IAM roles are properly configured

## CloudFormation Deployment

- [ ] Deploy the CloudFormation stack:
  ```bash
  python deploy_to_aws.py --method cloudformation --stack-name cdp-x402-payment-stack --s3-bucket your-deployment-bucket
  ```
- [ ] Monitor the CloudFormation stack creation process
- [ ] Verify all resources are created successfully
- [ ] Save the output API Gateway URL and other resource information

## Direct Lambda Deployment (Alternative)

- [ ] Create or update the Lambda function:
  ```bash
  python deploy_to_aws.py --method direct --function-name PaymentHandler-dev --role-arn <your-role-arn>
  ```
- [ ] Configure environment variables for the Lambda function
- [ ] Set up API Gateway endpoints if needed
- [ ] Configure API Gateway to point to the Lambda function

## Environment Configuration

- [ ] Set environment variables in the deployed Lambda function:
  - [ ] `CDP_WALLET_APP_ID`
  - [ ] `CDP_API_ENDPOINT`
  - [ ] `NETWORK`
  - [ ] `TOKEN_CONTRACT_ADDRESS`
  - [ ] `RPC_URL`
  - [ ] `TRANSACTION_TABLE_NAME`
  - [ ] `WALLET_SESSIONS_TABLE`

## Testing Deployed API

- [ ] Run the API test script:
  ```bash
  python test_deployed_api.py --api-url https://your-api-gateway-url/dev
  ```
- [ ] Verify all endpoints are working correctly:
  - [ ] `/cdp/wallet/connect`
  - [ ] `/cdp/wallet/status`
  - [ ] `/cdp/wallet/sign`
  - [ ] `/cdp/wallet/disconnect`
  - [ ] `/x402/payment/requirements`
  - [ ] `/x402/payment/process`
- [ ] Test with a real CDP wallet if available
- [ ] Verify payment processing works end-to-end

## Monitoring and Alerting Setup

- [ ] Set up CloudWatch monitoring:
  ```bash
  python setup_monitoring.py --function-name PaymentHandler-dev --api-name nft-payment-api-dev --email your@email.com
  ```
- [ ] Verify you receive an email subscription confirmation
- [ ] Confirm the email subscription
- [ ] Check the CloudWatch dashboard has been created
- [ ] Test an alarm by triggering a specific error condition
- [ ] Enable X-Ray tracing if needed
- [ ] Set up scheduled endpoint testing (optional)

## Security Review

- [ ] Enable API Gateway throttling
- [ ] Set up appropriate IAM policies
- [ ] Review Lambda execution role permissions
- [ ] Ensure secrets are properly stored in AWS Secrets Manager or as encrypted environment variables
- [ ] Verify CORS settings if the API will be accessed from browsers

## Frontend Integration

- [ ] Update frontend code with the new API endpoint:
  ```javascript
  const walletHandler = new CDPWalletHandler('https://your-api-gateway-url/dev');
  ```
- [ ] Test wallet connection from the frontend
- [ ] Test message signing from the frontend
- [ ] Test payment processing from the frontend
- [ ] Ensure proper error handling and user feedback

## Documentation

- [ ] Update API documentation with the new endpoints
- [ ] Provide integration guides to frontend developers
- [ ] Document environment variables and configuration settings
- [ ] Include troubleshooting information

## Final Verification

- [ ] Test the complete user flow:
  1. Connect wallet
  2. Check wallet status
  3. Sign a message
  4. Get payment requirements
  5. Process payment
  6. Access protected resource
  7. Disconnect wallet
- [ ] Check CloudWatch logs for any errors or warnings
- [ ] Verify all monitoring is working correctly

## Post-Deployment

- [ ] Set up a regular testing schedule
- [ ] Create a backup strategy for DynamoDB tables
- [ ] Plan for future updates and version control
- [ ] Document the deployment process for future reference

This checklist ensures you've covered all the necessary steps for a successful deployment of your CDP Wallet and X402 Payment Integration.
