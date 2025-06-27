#!/usr/bin/env python
"""
Simple Lambda Deployment Package Creator

This script creates a deployment package (ZIP) for AWS Lambda
containing the necessary files for the application.
"""
import os
import zipfile
import shutil

# Define the files and directories to include
files_to_include = [
    'lambda_handler.py',
    'cdp_wallet_x402_integration.py',
    'config.py',
    'apis',
    'utils'
]

# Output zip file
output_zip = 'lambda_deployment.zip'

def create_deployment_package():
    """
    Create a deployment package (zip) for AWS Lambda
    """
    print("Creating deployment package...")
    
    # Remove existing zip if it exists
    if os.path.exists(output_zip):
        os.remove(output_zip)
        print(f"Removed existing {output_zip}")
    
    # Create a new zip file
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for item in files_to_include:
            if os.path.isfile(item):
                print(f"Adding file: {item}")
                zipf.write(item)
            elif os.path.isdir(item):
                print(f"Adding directory: {item}")
                # Add all files from directory recursively
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if '__pycache__' not in file_path and '.pyc' not in file_path:
                            print(f"  - {file_path}")
                            zipf.write(file_path)
    
    # Get the size of the zip file
    zip_size = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"\nDeployment package created: {output_zip}")
    print(f"Package size: {zip_size:.2f} MB")

if __name__ == "__main__":
    create_deployment_package()
