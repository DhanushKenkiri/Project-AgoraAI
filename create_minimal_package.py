#!/usr/bin/env python3
"""
Minimal AWS Lambda Package Creator

This script creates the smallest possible Lambda deployment package by:
1. Moving ALL dependencies to a Lambda layer
2. Including only essential code files in the main package
"""

import os
import sys
import shutil
import zipfile
import subprocess
import time

# Define colors for terminal output
def color_print(message, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['end']}")

# Define essential code files (only Python files, no dependencies)
ESSENTIAL_FILES = [
    # Main handler files
    "lambda_handler.py",
    "bedrock_agent_adapter.py",
    "bedrock_agent_connector.py",
    "bedrock_agent_config.py",
    "payment_handler.py",
    "x402_payment_handler.py",
    "payment_config.py",
    "secure_payment_config.py",
    "config.py",
    "cdp_wallet_connector.js",
    "cdp_wallet_handler.py",
]

# Essential directories (will copy only .py files)
ESSENTIAL_DIRS = [
    "apis",
    "utils",
]

def clean_directory(dir_path):
    """Remove directory if it exists"""
    if os.path.exists(dir_path):
        color_print(f"Cleaning up {dir_path}...", "blue")
        shutil.rmtree(dir_path)

def create_minimal_lambda_package():
    """Create a minimal Lambda package with only essential code files"""
    # Clean up previous packages
    clean_directory("minimal_lambda")
    if os.path.exists("minimal_lambda_code.zip"):
        os.remove("minimal_lambda_code.zip")
    
    # Create the minimal package directory
    os.makedirs("minimal_lambda", exist_ok=True)
    
    # Copy essential files
    color_print("\nCopying essential files to minimal package:", "green")
    copied_files = 0
    
    # Copy essential files in root directory
    for filename in ESSENTIAL_FILES:
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join("minimal_lambda", filename))
            color_print(f"  ✓ {filename}", "cyan")
            copied_files += 1
        else:
            color_print(f"  ✗ {filename} (not found)", "yellow")
    
    # Copy essential directories (only .py files)
    for directory in ESSENTIAL_DIRS:
        if os.path.exists(directory):
            os.makedirs(os.path.join("minimal_lambda", directory), exist_ok=True)
            # Walk through directory
            for root, dirs, files in os.walk(directory):
                # Create equivalent subdirectory in minimal_lambda
                rel_path = os.path.relpath(root, ".")
                dest_dir = os.path.join("minimal_lambda", rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copy only Python files
                for file in files:
                    if file.endswith(".py"):
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(dest_dir, file)
                        shutil.copy2(src_file, dst_file)
                        copied_files += 1
            color_print(f"  ✓ {directory}/ (Python files only)", "cyan")
        else:
            color_print(f"  ✗ {directory}/ (not found)", "yellow")

    # Create __init__.py files to ensure directories are treated as packages
    for directory in ESSENTIAL_DIRS:
        init_path = os.path.join("minimal_lambda", directory, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write("# Auto-generated __init__.py to ensure directory is treated as a package\n")

    # Create templates and static directories if needed
    for special_dir in ["templates", "static"]:
        if os.path.exists(special_dir):
            dest_dir = os.path.join("minimal_lambda", special_dir)
            shutil.copytree(special_dir, dest_dir, dirs_exist_ok=True)
            color_print(f"  ✓ {special_dir}/ (copied)", "cyan")
    
    # Create the ZIP file
    color_print("\nCreating minimal Lambda package ZIP file...", "green")
    with zipfile.ZipFile("minimal_lambda_code.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("minimal_lambda"):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, "minimal_lambda")
                zipf.write(file_path, rel_path)
    
    # Check the size of the ZIP file
    size_mb = os.path.getsize("minimal_lambda_code.zip") / (1024 * 1024)
    color_print(f"\nMinimal Lambda package size: {size_mb:.2f} MB", "green")
    if size_mb < 50:
        color_print("✓ The package is below the 50MB Lambda direct upload limit!", "green")
    else:
        color_print("✗ The package is still above the 50MB limit. Further optimization needed.", "red")

    color_print(f"\nFiles copied to the minimal package: {copied_files}", "blue")
    
    return "minimal_lambda_code.zip"

def create_comprehensive_layer():
    """Create a comprehensive layer with ALL dependencies"""
    # Clean up previous packages
    clean_directory("full_layer")
    if os.path.exists("full_layer.zip"):
        os.remove("full_layer.zip")
    
    # Create the layer directory structure
    os.makedirs("full_layer/python", exist_ok=True)
    
    color_print("\nInstalling ALL dependencies to layer...", "green")
    try:
        # Install all requirements to the layer directory
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-t", "full_layer/python"],
            stderr=subprocess.STDOUT
        )
        color_print("✓ Dependencies installed successfully", "green")
    except subprocess.CalledProcessError as e:
        color_print(f"✗ Failed to install dependencies: {str(e)}", "red")
        return None
    
    # Create the ZIP file
    color_print("\nCreating comprehensive layer ZIP file...", "green")
    with zipfile.ZipFile("full_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("full_layer"):
            for file in files:
                file_path = os.path.join(root, file)
                # Make the relative path start from full_layer, not python
                rel_path = os.path.relpath(file_path, "full_layer")
                zipf.write(file_path, rel_path)
    
    # Check the size of the ZIP file
    size_mb = os.path.getsize("full_layer.zip") / (1024 * 1024)
    color_print(f"\nComprehensive layer size: {size_mb:.2f} MB", "blue")
    
    return "full_layer.zip"

if __name__ == "__main__":
    color_print("======================================================", "purple")
    color_print("  MINIMAL AWS LAMBDA PACKAGE & COMPREHENSIVE LAYER CREATOR", "purple")
    color_print("======================================================", "purple")
    
    start_time = time.time()
    
    # Create minimal Lambda package
    color_print("\n[Step 1] Creating minimal Lambda package...", "purple")
    lambda_package = create_minimal_lambda_package()
    
    # Create comprehensive layer
    color_print("\n[Step 2] Creating comprehensive layer...", "purple")
    layer_package = create_comprehensive_layer()
    
    # Summary
    color_print("\n======================================================", "purple")
    color_print("  DEPLOYMENT PACKAGE CREATION COMPLETE", "purple")
    color_print("======================================================", "purple")
    
    if lambda_package and layer_package:
        color_print(f"\nMinimal Lambda package: {lambda_package}", "green")
        color_print(f"Comprehensive layer: {layer_package}", "green")
        
        color_print("\nDeployment steps:", "yellow")
        color_print("1. Upload the layer first:", "white")
        color_print("   - Go to AWS Lambda > Layers > Create layer", "white")
        color_print(f"   - Upload {layer_package} as a new layer named 'bedrock-agent-dependencies'", "white")
        color_print("   - Select compatible runtime Python 3.11", "white")
        
        color_print("\n2. Upload the Lambda function code:", "white")
        color_print("   - Go to your Lambda function > Code", "white")
        color_print(f"   - Upload {lambda_package}", "white")
        
        color_print("\n3. Attach the layer to your Lambda function:", "white")
        color_print("   - Go to your Lambda function > Configuration > Layers", "white")
        color_print("   - Add layer > Custom layers > Select 'bedrock-agent-dependencies'", "white")
        
    else:
        color_print("\nPackage creation failed. Please check the errors above.", "red")
    
    elapsed_time = time.time() - start_time
    color_print(f"\nTotal time: {elapsed_time:.2f} seconds", "blue")
