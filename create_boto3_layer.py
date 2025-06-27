#!/usr/bin/env python3
"""
Create AWS Lambda Layer for boto3 dependencies
This script creates a Lambda layer that includes boto3, botocore and their dependencies.
"""

import os
import shutil
import subprocess
import zipfile
import sys
import tempfile
import platform

# Define the layer directory structure
LAYER_DIR = "boto3_layer"
PYTHON_LIB_DIR = os.path.join(LAYER_DIR, "python")

def create_boto3_layer():
    """Create a Lambda layer with boto3 and dependencies"""
    print("Creating boto3 Lambda layer...")
    
    # Clean up any existing layer dir
    if os.path.exists(LAYER_DIR):
        print(f"Removing existing {LAYER_DIR} directory")
        shutil.rmtree(LAYER_DIR)
    
    # Create the layer directory structure
    os.makedirs(PYTHON_LIB_DIR, exist_ok=True)
    
    # Create requirements file
    requirements_file = os.path.join(LAYER_DIR, "requirements.txt")
    with open(requirements_file, "w") as f:
        f.write("boto3==1.34.23\nbotocore==1.34.23\n")
    
    # Install packages into the layer directory
    print("Installing boto3 and dependencies...")
    
    pip_cmd = [sys.executable, "-m", "pip", "install", 
               "-r", requirements_file, 
               "-t", PYTHON_LIB_DIR, 
               "--no-cache-dir"]
    
    # Print the command we're running
    print(f"Running: {' '.join(pip_cmd)}")
    
    try:
        subprocess.check_call(pip_cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    
    # Create the layer ZIP file
    layer_zip = "boto3_layer.zip"
    if os.path.exists(layer_zip):
        os.remove(layer_zip)
    
    print(f"Creating {layer_zip}...")
    with zipfile.ZipFile(layer_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(LAYER_DIR):
            for file in files:
                # Skip __pycache__ directories and .pyc files
                if "__pycache__" in root or file.endswith(".pyc"):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, LAYER_DIR)
                zipf.write(file_path, arcname)
    
    print(f"Layer created successfully: {layer_zip}")
    print(f"Layer size: {os.path.getsize(layer_zip) / (1024 * 1024):.2f} MB")
    
    return True

def fix_bedrock_package():
    """Update the existing bedrock_deployment.zip to remove boto3 dependency"""
    if not os.path.exists("bedrock_deployment.zip"):
        print("bedrock_deployment.zip not found, skipping fix")
        return False
    
    print("Fixing bedrock_deployment.zip to use the Lambda layer...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Extract the existing package
        with zipfile.ZipFile("bedrock_deployment.zip", "r") as zipf:
            zipf.extractall(tmp_dir)
        
        # Create a new modified requirements.txt without boto3 and botocore
        req_file = os.path.join(tmp_dir, "requirements.txt")
        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                requirements = f.read().splitlines()
            
            # Filter out boto3 and botocore
            filtered_requirements = []
            for req in requirements:
                if not req.startswith("boto3") and not req.startswith("botocore"):
                    filtered_requirements.append(req)
            
            # Write the filtered requirements back
            with open(req_file, "w") as f:
                f.write("\n".join(filtered_requirements))
        
        # Create the updated ZIP file
        updated_zip = "bedrock_deployment_fixed.zip"
        with zipfile.ZipFile(updated_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    # Skip boto3 and botocore directories
                    if "boto3" in root or "botocore" in root:
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zipf.write(file_path, arcname)
    
    print(f"Updated package created: {updated_zip}")
    print(f"Package size: {os.path.getsize(updated_zip) / (1024 * 1024):.2f} MB")
    return True

if __name__ == "__main__":
    if create_boto3_layer():
        fix_bedrock_package()
        print("\nInstructions:")
        print("1. Upload boto3_layer.zip as a Lambda Layer in AWS Console")
        print("2. Upload bedrock_deployment_fixed.zip as your Lambda function code")
        print("3. Attach the boto3 layer to your Lambda function")
    else:
        print("Failed to create boto3 layer")
