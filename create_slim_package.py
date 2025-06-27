#!/usr/bin/env python3
"""
Slim Lambda Package Creator for AWS Direct Upload

This script creates a minimal Lambda deployment package by:
1. Moving most dependencies to a layer
2. Keeping only essential code in the main package
3. Aggressively cleaning up unnecessary files
"""

import os
import sys
import shutil
import zipfile
import fnmatch
import subprocess
import time
from datetime import datetime

# Define essential files that must stay in the main package
ESSENTIAL_FILES = [
    "lambda_handler.py",
    "x402_payment_handler.py",
    "payment_handler.py",
    "secure_payment_config.py",
    "bedrock_agent_adapter.py",
    "bedrock_agent_connector.py",
    "bedrock_agent_config.py",
    "config.py"
]

# Core directories that need to be in the main package
ESSENTIAL_DIRS = [
    "apis",
    "utils"
]

# Define dependencies to include in the layer
DEPENDENCIES = [
    "requests",
    "boto3",
    "botocore",
    "fastapi", 
    "uvicorn", 
    "mangum", 
    "pydantic", 
    "jinja2", 
    "aiofiles",
    "python_multipart",
    "starlette",
    "typing_extensions",
    "certifi",
    "charset_normalizer",
    "idna",
    "urllib3",
    "jmespath",
    "s3transfer",
    "python_dateutil",
    "six",
    "click",
    "h11",
    "annotated_types",
    "MarkupSafe",
    "typing_inspection",
    "pydantic_core",
    "colorama",
    "anyio",
    "sniffio"
]

# Clean up patterns to reduce size
CLEANUP_PATTERNS = [
    "**/__pycache__/*",
    "**/*.pyc",
    "**/*.pyd",
    "**/*.pyo",
    "**/*.dist-info/*",
    "**/*-info/*",
    "**/tests/*",
    "**/test/*",
    "**/*.md",
    "**/*.txt",
    "**/*.rst",
    "**/*.c",
    "**/*.h",
    "**/*.cpp",
    "**/*.hpp",
    "**/examples/*",
    "**/docs/*",
    "**/.git*",
    "**/.pytest_cache/*",
    "**/__pycache__",
    "**/.coverage",
    "**/*.ipynb"
]

def print_heading(text):
    """Print a heading with decorative formatting."""
    print("\n" + "=" * 70)
    print(f"{text}")
    print("=" * 70)

def print_status(text):
    """Print a status message."""
    print(f"[INFO] {text}")

def clean_directory(directory, patterns):
    """
    Clean a directory by removing files matching patterns.
    """
    cleaned_files = 0
    cleaned_size = 0
    
    for pattern in patterns:
        for root, dirs, files in os.walk(directory):
            # Clean files matching pattern
            for name in fnmatch.filter(files, pattern.replace("**", "*")):
                file_path = os.path.join(root, name)
                try:
                    file_size = os.path.getsize(file_path)
                    cleaned_size += file_size
                    os.remove(file_path)
                    cleaned_files += 1
                except (OSError, PermissionError) as e:
                    print(f"Failed to remove {file_path}: {e}")
                    
            # Clean directories matching pattern (if pattern ends with /*)
            if pattern.endswith("/*") or "**/" in pattern:
                dir_pattern = pattern.replace("/*", "").replace("**/", "*")
                for name in fnmatch.filter(dirs[:], dir_pattern):
                    dir_path = os.path.join(root, name)
                    try:
                        dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                  for dirpath, dirnames, filenames in os.walk(dir_path)
                                  for filename in filenames)
                        cleaned_size += dir_size
                        shutil.rmtree(dir_path)
                        cleaned_files += 1
                        # Prevent walk from going into removed directory
                        dirs.remove(name)
                    except (OSError, PermissionError) as e:
                        print(f"Failed to remove directory {dir_path}: {e}")
    
    return cleaned_files, cleaned_size / (1024 * 1024)  # Return size in MB

def create_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def main():
    """Main function to create the slim Lambda package."""
    start_time = time.time()
    
    print_heading("Slim AWS Lambda Package Creator - Optimized for < 50MB Direct Upload")
    
    # Create directories for code and layer
    main_dir = "lambda_slim_code"
    layer_dir = "lambda_slim_layer/python"
    
    # Clean up from previous runs
    for dir_path in [main_dir, "lambda_slim_layer"]:
        if os.path.exists(dir_path):
            print_status(f"Removing existing directory: {dir_path}")
            shutil.rmtree(dir_path)
    
    for zip_file in ["lambda_slim_code.zip", "lambda_slim_layer.zip"]:
        if os.path.exists(zip_file):
            print_status(f"Removing existing zip: {zip_file}")
            os.remove(zip_file)
    
    # Create fresh directories
    create_directory(main_dir)
    create_directory(layer_dir)
    
    # Install all dependencies to the layer directory
    print_status(f"Installing dependencies to layer: {', '.join(DEPENDENCIES)}")
    cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-t", layer_dir] + DEPENDENCIES
    subprocess.run(cmd, check=True)
    
    # Copy essential files to main directory
    print_status("Copying essential files to main package")
    for filename in ESSENTIAL_FILES:
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join(main_dir, filename))
            print(f"  + {filename}")
        else:
            print(f"  ! {filename} not found")
    
    # Copy essential directories to main directory
    for dirname in ESSENTIAL_DIRS:
        if os.path.exists(dirname):
            dest_dir = os.path.join(main_dir, dirname)
            shutil.copytree(dirname, dest_dir)
            print(f"  + {dirname}/")
        else:
            print(f"  ! {dirname}/ not found")
    
    # Clean up both directories to reduce size
    print_status("Cleaning up unnecessary files")
    main_cleaned_count, main_cleaned_mb = clean_directory(main_dir, CLEANUP_PATTERNS)
    layer_cleaned_count, layer_cleaned_mb = clean_directory(layer_dir, CLEANUP_PATTERNS)
    print(f"  - Removed {main_cleaned_count} files/dirs from main package ({main_cleaned_mb:.2f} MB)")
    print(f"  - Removed {layer_cleaned_count} files/dirs from layer ({layer_cleaned_mb:.2f} MB)")
    
    # Create the main code zip file
    print_status("Creating main Lambda package zip")
    with zipfile.ZipFile("lambda_slim_code.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(main_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, main_dir))
    
    # Create the layer zip file
    print_status("Creating Lambda layer zip")
    with zipfile.ZipFile("lambda_slim_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("lambda_slim_layer"):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, "lambda_slim_layer"))
    
    # Get size information
    main_zip_size = os.path.getsize("lambda_slim_code.zip") / (1024 * 1024)
    layer_zip_size = os.path.getsize("lambda_slim_layer.zip") / (1024 * 1024)
    
    print_heading("Package Creation Complete")
    print(f"Main package: lambda_slim_code.zip ({main_zip_size:.2f} MB)")
    print(f"Layer package: lambda_slim_layer.zip ({layer_zip_size:.2f} MB)")
    
    # Check if main package is within direct upload limit
    if main_zip_size < 50:
        print("\n✓ SUCCESS: Main package is under the 50 MB direct upload limit!")
    else:
        print("\n✗ WARNING: Main package is still over the 50 MB limit!")
        print("  You'll need to use S3 to upload this package.")
    
    # Provide deployment instructions
    print_heading("Deployment Instructions")
    print("1. Upload the layer first:")
    print("   aws lambda publish-layer-version --layer-name slim-agent-dependencies \\")
    print("      --zip-file fileb://lambda_slim_layer.zip")
    print("\n2. Note the LayerVersionArn from the response, then:")
    print("   aws lambda update-function-code --function-name YOUR_FUNCTION_NAME \\")
    print("      --zip-file fileb://lambda_slim_code.zip")
    print("\n3. Attach the layer to your function:")
    print("   aws lambda update-function-configuration --function-name YOUR_FUNCTION_NAME \\")
    print("      --layers [LayerVersionArn]")
    
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
