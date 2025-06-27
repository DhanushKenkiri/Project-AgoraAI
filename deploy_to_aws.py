#!/usr/bin/env python
"""
CDP Wallet and X402 Payment Integration - AWS Lambda Deployment Script

This script helps deploy the CDP Wallet and X402 Payment integration to AWS Lambda
using either CloudFormation or direct Lambda deployment methods.
"""
import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime

def check_aws_cli():
    """Check if AWS CLI is installed and configured"""
    try:
        result = subprocess.run(['aws', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode != 0:
            print("Error: AWS CLI is not installed or not in PATH")
            print("Please install AWS CLI: https://aws.amazon.com/cli/")
            sys.exit(1)
            
        # Check if AWS is configured
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode != 0:
            print("Error: AWS CLI is not configured properly")
            print("Please run 'aws configure' to set up your AWS credentials")
            sys.exit(1)
            
        account_info = json.loads(result.stdout)
        print(f"AWS CLI is configured for account: {account_info['Account']}")
        return account_info
        
    except FileNotFoundError:
        print("Error: AWS CLI is not installed")
        print("Please install AWS CLI: https://aws.amazon.com/cli/")
        sys.exit(1)

def check_deployment_package():
    """Check if deployment package exists"""
    package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "cdp_wallet_x402_lambda_package.zip")
    
    if not os.path.exists(package_path):
        print("Error: Deployment package not found")
        print("Please run create_cdp_x402_package.py first to create the deployment package")
        sys.exit(1)
        
    size_mb = os.path.getsize(package_path) / (1024 * 1024)
    print(f"Deployment package found: cdp_wallet_x402_lambda_package.zip ({size_mb:.2f} MB)")
    return package_path

def upload_to_s3(package_path, bucket_name, region="us-east-1"):
    """Upload deployment package to S3"""
    # Create bucket if it doesn't exist
    try:
        subprocess.run([
            'aws', 's3api', 'head-bucket',
            '--bucket', bucket_name,
            '--region', region
        ], capture_output=True, check=False)
    except:
        print(f"Creating S3 bucket: {bucket_name}")
        subprocess.run([
            'aws', 's3', 'mb',
            f's3://{bucket_name}',
            '--region', region
        ], check=True)
    
    # Upload package
    print(f"Uploading deployment package to s3://{bucket_name}/")
    result = subprocess.run([
        'aws', 's3', 'cp',
        package_path,
        f's3://{bucket_name}/cdp_wallet_x402_lambda_package.zip',
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"Error uploading to S3: {result.stderr}")
        sys.exit(1)
        
    print("Upload successful")
    return f"s3://{bucket_name}/cdp_wallet_x402_lambda_package.zip"

def deploy_cloudformation(template_file, stack_name, s3_bucket, environment="dev", region="us-east-1"):
    """Deploy using CloudFormation"""
    print(f"Deploying CloudFormation stack: {stack_name}")
    
    # Check if stack exists
    result = subprocess.run([
        'aws', 'cloudformation', 'describe-stacks',
        '--stack-name', stack_name,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        action = "Updating"
    else:
        action = "Creating"
    
    print(f"{action} CloudFormation stack...")
    result = subprocess.run([
        'aws', 'cloudformation', 'deploy',
        '--template-file', template_file,
        '--stack-name', stack_name,
        '--parameter-overrides', f'Environment={environment}',
        '--capabilities', 'CAPABILITY_IAM',
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"Error deploying CloudFormation stack: {result.stderr}")
        sys.exit(1)
    
    # Get stack outputs
    print("Getting stack outputs...")
    result = subprocess.run([
        'aws', 'cloudformation', 'describe-stacks',
        '--stack-name', stack_name,
        '--query', 'Stacks[0].Outputs',
        '--output', 'json',
        '--region', region
    ], capture_output=True, text=True, check=True)
    
    outputs = json.loads(result.stdout)
    
    # Format and display outputs
    print("\n=== Deployment Outputs ===")
    output_dict = {}
    for output in outputs:
        key = output['OutputKey']
        value = output['OutputValue']
        output_dict[key] = value
        print(f"{key}: {value}")
    
    # Save outputs to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"deployment_outputs_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(output_dict, f, indent=2)
    
    print(f"\nOutputs saved to {output_file}")
    return output_dict

def direct_lambda_deploy(package_path, function_name, role_arn, environment_vars, region="us-east-1"):
    """Deploy directly to Lambda"""
    # Check if function exists
    result = subprocess.run([
        'aws', 'lambda', 'get-function',
        '--function-name', function_name,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        # Update existing function
        print(f"Updating existing Lambda function: {function_name}")
        result = subprocess.run([
            'aws', 'lambda', 'update-function-code',
            '--function-name', function_name,
            '--zip-file', f'fileb://{package_path}',
            '--region', region
        ], capture_output=True, text=True, check=False)
    else:
        # Create new function
        print(f"Creating new Lambda function: {function_name}")
        result = subprocess.run([
            'aws', 'lambda', 'create-function',
            '--function-name', function_name,
            '--runtime', 'python3.9',
            '--role', role_arn,
            '--handler', 'lambda_handler.lambda_handler',
            '--zip-file', f'fileb://{package_path}',
            '--timeout', '60',
            '--memory-size', '512',
            '--region', region
        ], capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"Error deploying Lambda function: {result.stderr}")
        sys.exit(1)
    
    # Update configuration
    print("Updating function configuration...")
    env_vars_json = json.dumps({"Variables": environment_vars})
    result = subprocess.run([
        'aws', 'lambda', 'update-function-configuration',
        '--function-name', function_name,
        '--environment', env_vars_json,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"Error updating function configuration: {result.stderr}")
    
    print(f"Lambda function {function_name} deployed successfully")
    
    # Get function details
    result = subprocess.run([
        'aws', 'lambda', 'get-function',
        '--function-name', function_name,
        '--region', region,
        '--output', 'json'
    ], capture_output=True, text=True, check=True)
    
    function_details = json.loads(result.stdout)
    function_arn = function_details['Configuration']['FunctionArn']
    
    print(f"Function ARN: {function_arn}")
    return function_arn

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Deploy CDP Wallet and X402 Payment Integration to AWS Lambda'
    )
    
    parser.add_argument(
        '--method', 
        choices=['cloudformation', 'direct'], 
        default='cloudformation',
        help='Deployment method (cloudformation or direct)'
    )
    
    parser.add_argument(
        '--stack-name', 
        default='cdp-x402-payment-stack',
        help='CloudFormation stack name (for cloudformation method)'
    )
    
    parser.add_argument(
        '--s3-bucket', 
        default='',
        help='S3 bucket for deployment package (required for cloudformation method)'
    )
    
    parser.add_argument(
        '--function-name', 
        default='PaymentHandler-dev',
        help='Lambda function name (for direct method)'
    )
    
    parser.add_argument(
        '--role-arn', 
        default='',
        help='IAM role ARN for Lambda (required for direct method if creating new function)'
    )
    
    parser.add_argument(
        '--environment', 
        default='dev',
        help='Deployment environment (dev, staging, prod)'
    )
    
    parser.add_argument(
        '--region', 
        default='us-east-1',
        help='AWS region for deployment'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    print("=== CDP Wallet and X402 Payment Integration - AWS Lambda Deployment ===")
    
    # Parse arguments
    args = parse_arguments()
    
    # Check AWS CLI
    account_info = check_aws_cli()
    
    # Check deployment package
    package_path = check_deployment_package()
    
    # Deploy based on method
    if args.method == 'cloudformation':
        if not args.s3_bucket:
            # Use default bucket name based on account ID
            account_id = account_info['Account']
            args.s3_bucket = f"cdp-x402-deployment-{account_id}-{args.region}"
            print(f"Using default S3 bucket name: {args.s3_bucket}")
        
        # Upload package to S3
        s3_path = upload_to_s3(package_path, args.s3_bucket, args.region)
        
        # Update CloudFormation template
        template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "nft_payment_stack.yaml")
        
        # Deploy CloudFormation
        outputs = deploy_cloudformation(
            template_file, 
            args.stack_name, 
            args.s3_bucket, 
            args.environment,
            args.region
        )
        
    elif args.method == 'direct':
        if not args.role_arn:
            print("Warning: No IAM role ARN provided, will only work for updating existing functions")
        
        # Environment variables
        env_vars = {
            "ENVIRONMENT": args.environment,
            "CDP_WALLET_APP_ID": "your_cdp_app_id_here",
            "CDP_API_ENDPOINT": "https://api.cdp.io",
            "NETWORK": "base-sepolia",
            "TOKEN_CONTRACT_ADDRESS": "0x...",
            "RPC_URL": "https://sepolia.base.org",
            "TRANSACTION_TABLE_NAME": f"NFTPaymentTransactions-{args.environment}",
            "WALLET_SESSIONS_TABLE": f"NFTWalletSessions-{args.environment}"
        }
        
        # Deploy directly to Lambda
        function_arn = direct_lambda_deploy(
            package_path, 
            args.function_name, 
            args.role_arn,
            env_vars,
            args.region
        )
    
    print("\n=== Deployment Complete ===")
    print("Please update any frontend configurations to point to your new API endpoints")
    
if __name__ == "__main__":
    main()
