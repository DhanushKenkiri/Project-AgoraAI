"""
Deployment script for bundling and deploying the enhanced Lambda function

This script:
1. Creates a deployment package with all required modules
2. Uploads it to Lambda
3. Updates the function configuration
"""

import os
import sys
import subprocess
import shutil
import zipfile
import json
import boto3

def run_command(command):
    """Run a shell command and return the output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {result.stderr}")
        return None
    return result.stdout.strip()

def create_package(output_dir="deployment_package"):
    """Create the Lambda deployment package"""
    print("\n=== Creating Lambda deployment package ===")
    
    # Make sure the output directory exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Copy the essential files
    essential_files = [
        "lambda_handler.py",
        "config.py",
        "session_manager.py",
        "enhanced_wallet_login.py",
        "image_processor.py",
        "nft_image_processor.py",
        "bedrock_integration.py",
        "bedrock_agent_adapter.py",
        "bedrock_agent_connector.py",
        "bedrock_agent_config.py",
        "x402_payment_handler.py",
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(output_dir, file))
            print(f"Copied {file}")
        else:
            print(f"Warning: {file} not found, skipping")
    
    # Copy directories
    dirs_to_copy = ["apis", "utils"]
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            shutil.copytree(dir_name, os.path.join(output_dir, dir_name))
            print(f"Copied directory {dir_name}")
        else:
            print(f"Warning: Directory {dir_name} not found, skipping")
    
    # Try to copy optional files if they exist
    optional_files = [
        "wallet_login.py", 
        "nft_wallet.py"
    ]
    
    for file in optional_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(output_dir, file))
            print(f"Copied optional file {file}")
    
    # Create the zip file
    zip_filename = "lambda_deployment.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    print(f"Created {zip_filename}")
    return zip_filename

def deploy_to_lambda(zip_filename, function_name, region=None):
    """Deploy the package to an AWS Lambda function"""
    print(f"\n=== Deploying to Lambda function: {function_name} ===")
    
    # Try to get the AWS region from environment or config
    if not region:
        region = os.environ.get('AWS_REGION')
    
    if not region:
        try:
            import boto3
            session = boto3.session.Session()
            region = session.region_name
        except:
            region = "us-west-2"  # Default region
    
    if not region:
        print("Error: Could not determine AWS region. Please provide it as an argument.")
        return False
    
    # Check if AWS CLI is installed
    if shutil.which("aws"):
        # Upload using AWS CLI
        cmd = f"aws lambda update-function-code --function-name {function_name} --zip-file fileb://{zip_filename} --region {region}"
        output = run_command(cmd)
        if output:
            print("Lambda function code updated successfully!")
            print("\nChecking for function memory and timeout settings...")
            
            # Check current configuration
            cmd = f"aws lambda get-function-configuration --function-name {function_name} --region {region}"
            config_output = run_command(cmd)
            
            if config_output:
                try:
                    config = json.loads(config_output)
                    current_memory = config.get('MemorySize', 128)
                    current_timeout = config.get('Timeout', 3)
                    
                    recommended_memory = 1024  # 1GB is good for NFT/image processing
                    recommended_timeout = 30   # 30 seconds to handle image processing
                    
                    if current_memory < recommended_memory or current_timeout < recommended_timeout:
                        print(f"Current settings: Memory={current_memory}MB, Timeout={current_timeout}s")
                        print(f"Recommended settings: Memory={recommended_memory}MB, Timeout={recommended_timeout}s")
                        print("\nUpdating Lambda configuration with recommended settings...")
                        
                        update_cmd = f"aws lambda update-function-configuration --function-name {function_name} --memory-size {recommended_memory} --timeout {recommended_timeout} --region {region}"
                        update_output = run_command(update_cmd)
                        if update_output:
                            print("Lambda function configuration updated successfully!")
                    else:
                        print(f"Current settings are adequate: Memory={current_memory}MB, Timeout={current_timeout}s")
                        
                except Exception as e:
                    print(f"Error parsing Lambda configuration: {str(e)}")
            
            return True
    else:
        print("AWS CLI not found. Installing boto3 and using it to update the Lambda function...")
        
        try:
            # Try using boto3
            import boto3
            lambda_client = boto3.client('lambda', region_name=region)
            
            with open(zip_filename, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            print("Lambda function code updated successfully using boto3!")
            
            # Check and update configuration if needed
            config = lambda_client.get_function_configuration(FunctionName=function_name)
            current_memory = config.get('MemorySize', 128)
            current_timeout = config.get('Timeout', 3)
            
            recommended_memory = 1024  # 1GB is good for NFT/image processing
            recommended_timeout = 30   # 30 seconds to handle image processing
            
            if current_memory < recommended_memory or current_timeout < recommended_timeout:
                print(f"Current settings: Memory={current_memory}MB, Timeout={current_timeout}s")
                print(f"Recommended settings: Memory={recommended_memory}MB, Timeout={recommended_timeout}s")
                print("\nUpdating Lambda configuration with recommended settings...")
                
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    MemorySize=recommended_memory,
                    Timeout=recommended_timeout
                )
                print("Lambda function configuration updated successfully!")
            else:
                print(f"Current settings are adequate: Memory={current_memory}MB, Timeout={current_timeout}s")
                
            return True
            
        except Exception as e:
            print(f"Error deploying using boto3: {str(e)}")
            return False
    
    print("Failed to deploy to Lambda")
    return False

def main():
    """Main function"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Package and deploy Lambda function')
    parser.add_argument('--function-name', default=os.environ.get('LAMBDA_FUNCTION_NAME', ''),
                        help='Name of the Lambda function to update')
    parser.add_argument('--region', default=os.environ.get('AWS_REGION', ''),
                        help='AWS region of the Lambda function')
    parser.add_argument('--package-only', action='store_true',
                        help='Only create the package without deploying')
    
    args = parser.parse_args()
    
    # Create the package
    zip_filename = create_package()
    
    # Deploy if requested
    if not args.package_only:
        if not args.function_name:
            print("Error: Lambda function name is required. Provide it with --function-name")
            return 1
        
        deploy_success = deploy_to_lambda(zip_filename, args.function_name, args.region)
        if not deploy_success:
            return 1
    else:
        print(f"\nPackage created: {zip_filename}")
        print("Not deploying as --package-only was specified")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
