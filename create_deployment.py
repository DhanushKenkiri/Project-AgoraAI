#!/usr/bin/env python
"""
Simple script to create an AWS Lambda deployment package with proper error handling.
"""

import os
import sys
import zipfile
import shutil
import subprocess

def clean_directory(directory):
    """Remove directory if it exists"""
    if os.path.exists(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        else:
            os.remove(directory)

def create_deployment_package():
    """Create AWS Lambda deployment package"""
    print("=== Creating Lambda Deployment Package ===")

    # Clean previous deployment artifacts
    deployment_zip = "lambda_deployment.zip"
    if os.path.exists(deployment_zip):
        os.remove(deployment_zip)
        print(f"Removed existing {deployment_zip}")

    # Create zip file
    print("\nCreating zip file...")
    
    with zipfile.ZipFile(deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Core files
        core_files = [
            "lambda_handler.py",
            "config.py",
            "secure_payment_config.py",
            "wallet_login.py",
            "cdp_wallet_handler.py",
            "x402_payment_handler.py",
            "wallet_login_agent_instructions.md",
            "agent_payment_handler.py",
            "agent_payment_integration.py", 
            "dynamic_pricing_agent.py",
            "x402_client.js",
            "cdp_wallet_connector.js"
        ]
        
        for file in core_files:
            if os.path.exists(file):
                print(f"Adding file: {file}")
                zipf.write(file)
            else:
                print(f"Warning: {file} not found")
        
        # Add API modules
        if os.path.exists("apis"):
            for root, _, files in os.walk("apis"):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        print(f"Adding API: {file_path}")
                        zipf.write(file_path)
        else:
            print("Warning: apis directory not found")
            
        # Add utility modules
        if os.path.exists("utils"):
            for root, _, files in os.walk("utils"):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        print(f"Adding utility: {file_path}")
                        zipf.write(file_path)
        else:
            print("Warning: utils directory not found")

    # Print package info
    if os.path.exists(deployment_zip):
        size_mb = os.path.getsize(deployment_zip) / (1024 * 1024)
        print(f"\n✅ Deployment package created: {deployment_zip} ({size_mb:.2f} MB)")
        
        # List contents for verification
        print("\nVerifying zip contents:")
        with zipfile.ZipFile(deployment_zip, 'r') as zipf:
            file_count = len(zipf.namelist())
            print(f"Total files in zip: {file_count}")
            
            # Check key files
            key_files = [
                "lambda_handler.py",
                "utils/x402_processor.py",
                "apis/__init__.py"
            ]
            
            for key_file in key_files:
                if key_file in zipf.namelist():
                    print(f"✓ {key_file} found in package")
                else:
                    print(f"✗ Warning: {key_file} not found in package")
    else:
        print("❌ Failed to create deployment package")
        return False

    return True

if __name__ == "__main__":
    try:
        success = create_deployment_package()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error creating deployment package: {str(e)}")
        sys.exit(1)
