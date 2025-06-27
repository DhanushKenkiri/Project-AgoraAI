#!/usr/bin/env python
"""
Script to help update Lambda environment variables for dynamic pricing
"""
import boto3
import json
import argparse

def update_lambda_env(function_name, region='us-east-1'):
    """
    Add or update environment variables for the NFT pricing APIs
    """
    # Get the current Lambda configuration
    lambda_client = boto3.client('lambda', region_name=region)
    response = lambda_client.get_function_configuration(
        FunctionName=function_name
    )
    
    # Get current environment variables
    env_vars = response.get('Environment', {}).get('Variables', {})
    
    # Check if we need to add NFT API keys
    need_reservoir = 'RESERVOIR_API_KEY' not in env_vars
    need_opensea = 'OPENSEA_API_KEY' not in env_vars
    need_nftgo = 'NFTGO_API_KEY' not in env_vars
    
    if need_reservoir or need_opensea or need_nftgo:
        print("Adding NFT API keys to Lambda environment variables...")
        
        # Add placeholders for missing API keys
        if need_reservoir:
            env_vars['RESERVOIR_API_KEY'] = ''
            print("Added RESERVOIR_API_KEY (please set the actual key value in the Lambda console)")
            
        if need_opensea:
            env_vars['OPENSEA_API_KEY'] = ''
            print("Added OPENSEA_API_KEY (please set the actual key value in the Lambda console)")
            
        if need_nftgo:
            env_vars['NFTGO_API_KEY'] = ''
            print("Added NFTGO_API_KEY (please set the actual key value in the Lambda console)")
        
        # Update the Lambda environment variables
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': env_vars
            }
        )
        
        print(f"✅ Lambda function {function_name} environment variables updated")
        print("Please go to the AWS Lambda console to set the actual API key values")
    else:
        print("NFT API keys already exist in Lambda environment variables")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Lambda environment variables for NFT pricing APIs")
    parser.add_argument("--function", required=True, help="Lambda function name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    
    args = parser.parse_args()
    update_lambda_env(args.function, args.region)
