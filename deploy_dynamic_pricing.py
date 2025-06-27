#!/usr/bin/env python
import argparse
import os
import sys
import subprocess
import boto3
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy the NFT payment Lambda function with dynamic pricing')
    parser.add_argument('--stack-name', type=str, default='nft-payment-stack',
                        help='CloudFormation stack name (default: nft-payment-stack)')
    parser.add_argument('--environment', type=str, default='dev',
                        help='Environment to deploy to (default: dev)')
    parser.add_argument('--region', type=str, default='us-east-1',
                        help='AWS region to deploy to (default: us-east-1)')
    parser.add_argument('--secrets-arn', type=str,
                        help='ARN of the Secrets Manager secret containing API keys')
    return parser.parse_args()

def create_deployment_package():
    """Create a deployment package for the Lambda function"""
    print("Creating Lambda deployment package...")
    try:
        # Run the package creation script
        subprocess.check_call([sys.executable, "create_lambda_package.py"])
        print("✅ Deployment package created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating deployment package: {str(e)}")
        return False

def deploy_cfn_stack(stack_name, environment, region, secrets_arn=None):
    """Deploy the CloudFormation stack"""
    print(f"Deploying CloudFormation stack {stack_name} to {region}...")
    
    # Build the CloudFormation parameters
    parameters = [
        {
            'ParameterKey': 'Environment',
            'ParameterValue': environment
        }
    ]
    
    if secrets_arn:
        parameters.append({
            'ParameterKey': 'SecretsManagerArn',
            'ParameterValue': secrets_arn
        })
    
    try:
        cfn = boto3.client('cloudformation', region_name=region)
        
        # Check if the stack exists
        stack_exists = False
        try:
            cfn.describe_stacks(StackName=stack_name)
            stack_exists = True
        except:
            pass
            
        # Create or update the stack
        with open('nft_payment_stack_fixed.yaml', 'r') as f:
            template_body = f.read()
            
        if stack_exists:
            # Update existing stack
            print(f"Updating existing stack {stack_name}...")
            cfn.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
            )
        else:
            # Create new stack
            print(f"Creating new stack {stack_name}...")
            cfn.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            
        print(f"✅ CloudFormation stack {stack_name} deployment initiated")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying CloudFormation stack: {str(e)}")
        return False

def update_lambda_code(function_name, environment, region):
    """Update the Lambda function code with the deployment package"""
    print(f"Updating Lambda function {function_name}-{environment} code...")
    
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Upload the deployment package
        with open('lambda_deployment.zip', 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=f"{function_name}-{environment}",
                ZipFile=f.read(),
                Publish=True
            )
            
        print(f"✅ Lambda function code updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function code: {str(e)}")
        return False

def update_secrets_manager(secrets_arn, region):
    """Update the Secrets Manager secret with the correct format for dynamic pricing"""
    if not secrets_arn:
        print("⚠️ No Secrets Manager ARN provided, skipping secret update")
        return True
        
    print(f"Updating Secrets Manager secret {secrets_arn}...")
    
    try:
        sm = boto3.client('secretsmanager', region_name=region)
        
        # Get the current secret value
        response = sm.get_secret_value(SecretId=secrets_arn)
        if 'SecretString' in response:
            current_secret = json.loads(response['SecretString'])
        else:
            current_secret = {}
            
        # Ensure the secret has the correct structure for dynamic pricing
        if 'RESOURCE_PRICES' not in current_secret:
            current_secret['RESOURCE_PRICES'] = json.dumps({
                "api/nft/details": {"amount": 0.001, "currency": "ETH"},
                "api/collection": {"amount": 0.005, "currency": "ETH"}
            })
            
        # Check for API keys
        if 'RESERVOIR_API_KEY' not in current_secret:
            print("⚠️ No RESERVOIR_API_KEY found in secret, add it for dynamic NFT pricing")
            
        if 'OPENSEA_API_KEY' not in current_secret:
            print("⚠️ No OPENSEA_API_KEY found in secret, add it for dynamic NFT pricing")
            
        if 'NFTGO_API_KEY' not in current_secret:
            print("⚠️ No NFTGO_API_KEY found in secret, add it for dynamic NFT pricing")
        
        # Update the secret
        sm.put_secret_value(
            SecretId=secrets_arn,
            SecretString=json.dumps(current_secret)
        )
        
        print(f"✅ Secrets Manager secret updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Secrets Manager secret: {str(e)}")
        return False

def main():
    args = parse_args()
    
    # Create deployment package
    if not create_deployment_package():
        return 1
        
    # Deploy CloudFormation stack
    if not deploy_cfn_stack(args.stack_name, args.environment, args.region, args.secrets_arn):
        return 1
    
    # Update Lambda function code
    if not update_lambda_code("PaymentHandler", args.environment, args.region):
        return 1
        
    # Update Secrets Manager secret
    if not update_secrets_manager(args.secrets_arn, args.region):
        return 1
    
    print("\n🚀 Deployment completed successfully! Your NFT payment system with dynamic pricing is ready.")
    print("\nExample API endpoint:")
    print(f"https://<api-id>.execute-api.{args.region}.amazonaws.com/{args.environment}/payment")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
