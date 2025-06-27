#!/usr/bin/env python3
"""
Create Minimal Lambda Package with Complete Layer
This script creates a minimal Lambda deployment package that should be under 50MB,
and places all dependencies in a Lambda layer.
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

# Files to exclude from the main package
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

def create_directories():
    """Create working directories"""
    # Clean up old directories and files
    for path in ["minimal_package", "complete_layer", "minimal_lambda.zip", "complete_layer.zip"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    # Create new directories
    os.makedirs("minimal_package")
    os.makedirs("complete_layer/python")

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
            shutil.copytree(directory, dest_dir)
            print(f"  Copied directory: {directory}")
            file_count = sum(len(files) for _, _, files in os.walk(dest_dir))
            copied_files += file_count
    
    print_color(f"Total files copied to minimal package: {copied_files}", "green")

def install_dependencies():
    """Install all dependencies to the layer directory"""
    print_color("Installing dependencies to layer...", "blue")
    
    # Make sure pip is available
    try:
        # Install all requirements to the layer directory
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--target", "complete_layer/python", "--no-cache-dir"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Also install boto3 and botocore explicitly (AWS packages)
        cmd = [sys.executable, "-m", "pip", "install", "boto3", "botocore", "--target", "complete_layer/python", "--no-cache-dir"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        print_color("Dependencies installed successfully", "green")
    except subprocess.CalledProcessError as e:
        print_color(f"Error installing dependencies: {e}", "red")
        sys.exit(1)

def create_zip_packages():
    """Create ZIP files for Lambda and Layer"""
    # Create Lambda package ZIP
    print_color("Creating Lambda package ZIP...", "blue")
    with zipfile.ZipFile("minimal_lambda.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("minimal_package"):
            # Skip excluded files
            dirs[:] = [d for d in dirs if not any(exclude in d for exclude in EXCLUDE_FILES)]
            
            for file in files:
                if not any(file.endswith(exclude) for exclude in EXCLUDE_FILES):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "minimal_package")
                    zipf.write(file_path, arcname)
    
    # Create Layer ZIP
    print_color("Creating Layer ZIP...", "blue")
    with zipfile.ZipFile("complete_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("complete_layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "complete_layer")
                zipf.write(file_path, arcname)
    
    # Get file sizes
    lambda_size = os.path.getsize("minimal_lambda.zip") / (1024 * 1024)
    layer_size = os.path.getsize("complete_layer.zip") / (1024 * 1024)
    
    print_color(f"Lambda package size: {lambda_size:.2f} MB", "yellow")
    print_color(f"Layer package size: {layer_size:.2f} MB", "yellow")
    
    if lambda_size > 50:
        print_color("WARNING: Lambda package is larger than the 50 MB limit", "red")
    else:
        print_color("Lambda package is within the 50 MB limit", "green")

def main():
    """Main function"""
    start_time = time.time()
    print_color("Creating minimal Lambda package with complete layer...", "magenta")
    
    create_directories()
    copy_essential_files()
    install_dependencies()
    create_zip_packages()
    
    print_color(f"Completed in {time.time() - start_time:.2f} seconds", "magenta")
    print_color("\nInstructions:", "green")
    print_color("1. Upload complete_layer.zip as a Lambda Layer", "blue")
    print_color("2. Upload minimal_lambda.zip as your Lambda function code", "blue")
    print_color("3. Attach the layer to your Lambda function", "blue")

if __name__ == "__main__":
    main()
