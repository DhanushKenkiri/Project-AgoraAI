#!/usr/bin/env python
"""
Simple script to deploy the lambda_deployment.zip to AWS Lambda using AWS CLI
"""
import os
import subprocess
import sys
import json
import argparse

def deploy_with_aws_cli(function_name, region, profile=None, env_file=None):
    """Deploy the Lambda package using AWS CLI"""
    # Check if lambda_deployment.zip exists
    if not os.path.exists("lambda_deployment.zip"):
        print("❌ Error: lambda_deployment.zip not found. Run create_lambda_package.py first.")
        return False
    
    # Build AWS CLI command
    aws_command = ["aws"]
    if profile:
        aws_command.extend(["--profile", profile])
    if region:
        aws_command.extend(["--region", region])
    
    aws_command.extend([
        "lambda", "update-function-code",
        "--function-name", function_name,
        "--zip-file", "fileb://lambda_deployment.zip"
    ])
    
    # Execute the command
    print(f"Deploying code to Lambda function: {function_name}")
    try:
        result = subprocess.run(aws_command, check=True, capture_output=True, text=True)
        print(f"✅ Successfully deployed Lambda code: {function_name}")
        
        # If env file is provided, update environment variables
        if env_file:
            update_env_variables(function_name, env_file, profile, region)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e.stderr}")
        return False

def update_env_variables(function_name, env_file, profile=None, region=None):
    """Update Lambda environment variables from a JSON file"""
    # Load environment variables from file
    try:
        with open(env_file, 'r') as f:
            env_vars = json.load(f)
    except Exception as e:
        print(f"❌ Error loading environment variables file: {str(e)}")
        return False
    
    # Format environment variables for AWS CLI
    env_vars_str = json.dumps({"Variables": env_vars})
    
    # Build AWS CLI command
    aws_command = ["aws"]
    if profile:
        aws_command.extend(["--profile", profile])
    if region:
        aws_command.extend(["--region", region])
    
    aws_command.extend([
        "lambda", "update-function-configuration",
        "--function-name", function_name,
        "--environment", env_vars_str
    ])
    
    # Execute the command
    print(f"Updating environment variables for: {function_name}")
    try:
        result = subprocess.run(aws_command, check=True, capture_output=True, text=True)
        print(f"✅ Successfully updated environment variables")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update environment variables: {e.stderr}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Lambda package to AWS using AWS CLI")
    parser.add_argument("--function", required=True, help="Lambda function name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--profile", help="AWS profile to use (optional)")
    parser.add_argument("--env-file", help="JSON file with environment variables (optional)")
    
    args = parser.parse_args()
    
    success = deploy_with_aws_cli(args.function, args.region, args.profile, args.env_file)
    sys.exit(0 if success else 1)
