"""
This script creates a fixed Lambda deployment package that ensures all necessary files are included,
especially the secure_payment_config.py which is causing import errors.
"""
import os
import subprocess
import shutil
import zipfile
import sys

def build_deployment_package():
    """Build a Lambda deployment package with all required files"""
    
    print("Creating fixed Lambda deployment package...")
    
    # Remove existing package directory and zip if they exist
    if os.path.exists("fixed_package"):
        print("Removing existing package directory...")
        shutil.rmtree("fixed_package")
    
    if os.path.exists("lambda_fixed_deployment.zip"):
        print("Removing existing deployment zip...")
        os.remove("lambda_fixed_deployment.zip")
    
    # Create a fresh directory for dependencies
    os.makedirs("fixed_package")
    
    # Define the list of essential files we need to include
    essential_files = [
        "lambda_handler.py",
        "config.py",
        "secure_payment_config.py",
        "payment_config.py",
        "payment_handler.py",
        "x402_payment_handler.py",
        "x402_client.js",
        "cdp_wallet_connector.js"
    ]
    
    # Define essential directories
    essential_dirs = [
        "apis",
        "utils"
    ]
    
    # Copy essential directories
    for directory in essential_dirs:
        if os.path.exists(directory):
            print(f"Copying directory: {directory}")
            shutil.copytree(directory, f"fixed_package/{directory}")
        else:
            print(f"Warning: Directory {directory} not found")
    
    # Copy essential files
    for file in essential_files:
        if os.path.exists(file):
            print(f"Copying file: {file}")
            shutil.copy2(file, f"fixed_package/{file}")
        else:
            print(f"Warning: File {file} not found")
    
    # Check for optional enhanced modules and include them if they exist
    optional_files = [
        "enhanced_wallet_login.py",
        "image_processor.py",
        "nft_image_processor.py",
        "bedrock_integration.py",
        "session_manager.py",
        "wallet_login.py",
        "nft_wallet.py",
        "agent_payment_integration.py",
        "dynamic_pricing_agent.py",
        "bedrock_agent_adapter.py",
        "aws_mcp_server.py",
        "mcp_server.py"
    ]
    
    for file in optional_files:
        if os.path.exists(file):
            print(f"Copying optional file: {file}")
            shutil.copy2(file, f"fixed_package/{file}")    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        # Try to install dependencies in a more Windows-friendly way
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt", 
            "-t", "fixed_package", 
            "--no-cache-dir"
        ])
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        print("Continuing with packaging without dependencies...")
    
    # Create the deployment ZIP file
    print("\nCreating deployment ZIP file...")
    with zipfile.ZipFile("lambda_fixed_deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("fixed_package"):
            for file in files:
                file_path = os.path.join(root, file)
                # Make sure the relative path is correct for Lambda
                zipf.write(
                    file_path, 
                    os.path.relpath(file_path, "fixed_package")
                )
    
    # Verify key files are in the zip
    print("\nVerifying deployment package...")
    with zipfile.ZipFile("lambda_fixed_deployment.zip", "r") as zipf:
        zip_files = zipf.namelist()
        for file in essential_files:
            if file in zip_files:
                print(f"✓ {file} is in the package")
            else:
                print(f"✗ ERROR: {file} is missing from the package")
        
        # Check for secure_payment_config.py specifically
        if "secure_payment_config.py" in zip_files:
            print("✓ secure_payment_config.py is properly included in the package")
        else:
            print("✗ ERROR: secure_payment_config.py is missing!")
    
    print(f"\nDeployment package created: lambda_fixed_deployment.zip")
    print("Upload this file to your AWS Lambda function")

if __name__ == "__main__":
    build_deployment_package()
