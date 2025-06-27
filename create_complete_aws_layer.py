#!/usr/bin/env python3
"""
Create Complete AWS Layer Package
This script creates a dedicated AWS SDK layer with complete boto3 and botocore packages,
ensuring that all components including botocore.docs are properly included.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import time
from pathlib import Path

def print_color(text, color):
    """Print colored text to console"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

# Define the essential source code files to include in the main package
ESSENTIAL_FILES = [
    "lambda_handler.py",
    "bedrock_agent_adapter.py", 
    "bedrock_agent_connector.py",
    "bedrock_agent_config.py",
    "config.py",
    "secure_payment_config.py",
    "payment_handler.py",
    "x402_payment_handler.py",
    "payment_config.py",
    "cdp_wallet_connector.js"  # Include any JS files needed
]

# Define directories to include (will copy the entire directory)
ESSENTIAL_DIRS = [
    "apis",
    "utils",
    "static",
    "templates"
]

# Files to exclude from packages
EXCLUDE_FILES = [
    "__pycache__",
    "*.pyc",
    "*.pyd",
    "*.pyo",
    "test_*.py",
    "create_*.py",
    "*.zip",
    "*.md",
    "layer",
    "lambda_package",
    "package"
]

# AWS SDK dependencies to be installed in the AWS layer
AWS_DEPENDENCIES = [
    "boto3",
    "botocore",
    "s3transfer",
    "jmespath"  # Required by boto3
]

def create_directories():
    """Create working directories"""
    # Clean up old directories and files
    for path in ["minimal_package", "aws_layer", "app_dependencies", "minimal_lambda.zip", "aws_layer.zip", "app_layer.zip"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    # Create new directories
    os.makedirs("minimal_package")
    os.makedirs("aws_layer/python")
    os.makedirs("app_dependencies/python")

def copy_essential_files():
    """Copy only essential code files to the minimal package"""
    print_color("Copying essential files to minimal package...", "blue")
    copied_files = 0
    
    # Copy individual files
    for file in ESSENTIAL_FILES:
        if os.path.exists(file):
            dest_path = os.path.join("minimal_package", file)
            # Create directories if needed
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file, dest_path)
            copied_files += 1
            print(f"  Copied: {file}")
    
    # Copy directories
    for directory in ESSENTIAL_DIRS:
        if os.path.exists(directory):
            dest_dir = os.path.join("minimal_package", directory)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(directory, dest_dir)
            print(f"  Copied directory: {directory}")
            file_count = sum(len(files) for _, _, files in os.walk(dest_dir))
            copied_files += file_count
    
    print_color(f"Total files copied to minimal package: {copied_files}", "green")

def install_aws_dependencies():
    """Install AWS SDK dependencies to the AWS layer directory"""
    print_color("Installing AWS SDK dependencies to AWS layer...", "blue")
    
    try:
        # Install AWS SDK packages to the AWS layer directory
        for package in AWS_DEPENDENCIES:
            cmd = [sys.executable, "-m", "pip", "install", package, "--target", "aws_layer/python", "--upgrade", "--no-cache-dir"]
            print(f"Running: {' '.join(cmd)}")
            subprocess.check_call(cmd)
        
        print_color("AWS SDK dependencies installed successfully", "green")
    except subprocess.CalledProcessError as e:
        print_color(f"Error installing AWS SDK dependencies: {e}", "red")
        sys.exit(1)

def install_app_dependencies():
    """Install application dependencies to the app layer directory"""
    print_color("Installing application dependencies to app layer...", "blue")
    
    try:
        # Install all requirements except AWS SDK to the app layer directory
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--target", "app_dependencies/python", "--no-cache-dir"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Remove AWS SDK packages from app layer if they were installed
        for package in AWS_DEPENDENCIES:
            package_dir = os.path.join("app_dependencies/python", package)
            if os.path.exists(package_dir):
                print(f"Removing {package} from app layer (will be in AWS layer)")
                shutil.rmtree(package_dir)
        
        print_color("Application dependencies installed successfully", "green")
    except subprocess.CalledProcessError as e:
        print_color(f"Error installing application dependencies: {e}", "red")
        sys.exit(1)

def create_zip_packages():
    """Create ZIP files for Lambda and Layers"""
    # Create Lambda package ZIP
    print_color("Creating Lambda package ZIP...", "blue")
    with zipfile.ZipFile("minimal_lambda.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("minimal_package"):
            # Skip excluded files
            dirs[:] = [d for d in dirs if not any(exclude in d for exclude in EXCLUDE_FILES)]
            
            for file in files:
                if not any(file.endswith(exclude[1:]) if exclude.startswith("*.") else exclude in file for exclude in EXCLUDE_FILES):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "minimal_package")
                    zipf.write(file_path, arcname)
    
    # Create AWS Layer ZIP
    print_color("Creating AWS Layer ZIP...", "blue")
    with zipfile.ZipFile("aws_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("aws_layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "aws_layer")
                zipf.write(file_path, arcname)
    
    # Create App Layer ZIP
    print_color("Creating App Layer ZIP...", "blue")
    with zipfile.ZipFile("app_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("app_dependencies"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "app_dependencies")
                zipf.write(file_path, arcname)
    
    # Get file sizes
    lambda_size = os.path.getsize("minimal_lambda.zip") / (1024 * 1024)
    aws_layer_size = os.path.getsize("aws_layer.zip") / (1024 * 1024)
    app_layer_size = os.path.getsize("app_layer.zip") / (1024 * 1024)
    
    print_color(f"Lambda package size: {lambda_size:.2f} MB", "yellow")
    print_color(f"AWS Layer package size: {aws_layer_size:.2f} MB", "yellow")
    print_color(f"App Layer package size: {app_layer_size:.2f} MB", "yellow")
    
    if lambda_size > 50:
        print_color("WARNING: Lambda package is larger than the 50 MB limit", "red")
    else:
        print_color("Lambda package is within the 50 MB limit", "green")

def main():
    """Main function"""
    start_time = time.time()
    print_color("Creating Lambda package with dedicated AWS SDK layer...", "magenta")
    
    create_directories()
    copy_essential_files()
    install_aws_dependencies()
    install_app_dependencies()
    create_zip_packages()
    
    print_color(f"Completed in {time.time() - start_time:.2f} seconds", "magenta")
    print_color("\nInstructions:", "green")
    print_color("1. Upload aws_layer.zip as a Lambda Layer named 'aws-sdk-layer'", "blue")
    print_color("2. Upload app_layer.zip as a Lambda Layer named 'app-dependencies-layer'", "blue")
    print_color("3. Upload minimal_lambda.zip as your Lambda function code", "blue")
    print_color("4. Attach both layers to your Lambda function", "blue")
    print_color("5. Make sure the layers are in this order: aws-sdk-layer first, then app-dependencies-layer", "yellow")

if __name__ == "__main__":
    main()
