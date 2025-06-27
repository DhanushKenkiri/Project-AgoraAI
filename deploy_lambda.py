#!/usr/bin/env python
"""
Deploys the NFT payment Lambda package to AWS
"""
import argparse
import boto3
import os
import json
import sys

def deploy_lambda_package(function_name, region, profile=None, env_vars=None):
    """
    Deploy the lambda_deployment.zip package to the specified AWS Lambda function
    """
    # Check if the deployment package exists
    if not os.path.exists('lambda_deployment.zip'):
        print("❌ Error: lambda_deployment.zip not found. Run create_lambda_package.py first.")
        return False
    
    # Create a boto3 session with the specified profile
    if profile:
        session = boto3.Session(profile_name=profile, region_name=region)
    else:
        session = boto3.Session(region_name=region)
    
    # Create a Lambda client
    lambda_client = session.client('lambda')
    
    try:
        # Update the function code
        print(f"Updating Lambda function code: {function_name}")
        with open('lambda_deployment.zip', 'rb') as zip_file:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read(),
                Publish=True
            )
        
        # If environment variables are provided, update the configuration
        if env_vars:
            print(f"Updating Lambda environment variables")
            
            # Get current configuration to merge with new variables
            current_config = lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            
            # Get current environment or create empty dict if none exists
            current_env = current_config.get('Environment', {}).get('Variables', {})
            
            # Merge with new environment variables (preserving existing ones)
            merged_env = {**current_env, **env_vars}
            
            # Update the function configuration
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={
                    'Variables': merged_env
                }
            )
        
        print(f"✅ Successfully deployed to Lambda function: {function_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying to Lambda: {str(e)}")
        return False

def ensure_nft_api_vars(env_vars):
    """Add placeholders for NFT API keys if they don't exist"""
    for key in ['RESERVOIR_API_KEY', 'OPENSEA_API_KEY', 'NFTGO_API_KEY']:
        if key not in env_vars:
            env_vars[key] = ''
    return env_vars

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Lambda package to AWS")
    parser.add_argument("--function", required=True, help="Lambda function name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--profile", help="AWS profile to use (optional)")
    parser.add_argument("--env-file", help="JSON file with environment variables (optional)")
    
    args = parser.parse_args()
    
    env_vars = None
    if args.env_file:
        try:
            with open(args.env_file, 'r') as f:
                env_vars = json.load(f)
                # Ensure NFT API keys exist
                env_vars = ensure_nft_api_vars(env_vars)
        except Exception as e:
            print(f"Error loading environment variables: {str(e)}")
            sys.exit(1)
    
    success = deploy_lambda_package(args.function, args.region, args.profile, env_vars)
    sys.exit(0 if success else 1)
