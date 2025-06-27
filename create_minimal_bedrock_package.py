#!/usr/bin/env python3
"""
Minimal AWS Lambda Package Creator for Bedrock Agent Integration

This script creates a minimal Lambda deployment package that includes only
essential files for the Bedrock agent integration, helping stay under size limits.
"""

import os
import sys
import shutil
import zipfile
import fnmatch

# Define essential Python files that should be included in the main package
ESSENTIAL_FILES = [
    "lambda_handler.py",
    "bedrock_agent_adapter.py",
    "bedrock_agent_connector.py", 
    "bedrock_agent_config.py",
    "session_manager.py",
    "wallet_login.py",
    "nft_wallet.py",
    "payment_handler.py",
    "x402_payment_handler.py"
]

# Define essential directories that should be included with their contents
ESSENTIAL_DIRS = [
    "apis",
    "utils"
]

# Define files and directories to exclude from the package
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    "tests",
    "test_*.py",
    "*_test.py",
    "*.md",
    "*.txt",
    "*.yaml",
    "*.yml",
    "*.zip",
    "create_*.py",
    "deploy_*.py",
    "update_*.py"
]

def should_exclude(path):
    """Check if a file or directory should be excluded based on patterns"""
    filename = os.path.basename(path)
    return any(fnmatch.fnmatch(filename, pattern) for pattern in EXCLUDE_PATTERNS)

def create_package_directory(package_dir):
    """Create the package directory, removing it if it already exists"""
    if os.path.exists(package_dir):
        print(f"Removing existing {package_dir}...")
        shutil.rmtree(package_dir)
    
    print(f"Creating {package_dir}...")
    os.makedirs(package_dir)

def copy_essential_files(source_dir, package_dir):
    """Copy essential files to the package directory"""
    print("Copying essential files...")
    file_count = 0
    
    for file_path in ESSENTIAL_FILES:
        source_path = os.path.join(source_dir, file_path)
        target_path = os.path.join(package_dir, file_path)
        
        if os.path.isfile(source_path):
            # Create the directory structure if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(source_path, target_path)
            print(f"  Copied {file_path}")
            file_count += 1
        else:
            print(f"  Warning: Essential file {file_path} not found")
    
    return file_count

def copy_essential_dirs(source_dir, package_dir):
    """Copy essential directories to the package directory"""
    print("Copying essential directories...")
    dir_count = 0
    file_count = 0
    
    for dir_name in ESSENTIAL_DIRS:
        source_path = os.path.join(source_dir, dir_name)
        target_path = os.path.join(package_dir, dir_name)
        
        if os.path.isdir(source_path):
            # Create the target directory
            os.makedirs(target_path, exist_ok=True)
            dir_count += 1
            
            # Walk the directory and copy files
            for root, dirs, files in os.walk(source_path):
                # Skip directories that match exclude patterns
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                
                # Process files
                for file in files:
                    if should_exclude(file):
                        continue
                    
                    file_source = os.path.join(root, file)
                    # Calculate the relative path from the source directory
                    rel_path = os.path.relpath(file_source, source_path)
                    file_target = os.path.join(target_path, rel_path)
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(file_target), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(file_source, file_target)
                    file_count += 1
        else:
            print(f"  Warning: Essential directory {dir_name} not found")
    
    print(f"  Copied {dir_count} directories containing {file_count} files")
    return dir_count, file_count

def create_zip_package(package_dir, zip_name):
    """Create a ZIP package from the directory"""
    print(f"Creating ZIP package: {zip_name}")
    
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Create relative path for the ZIP
                rel_path = os.path.relpath(file_path, package_dir)
                
                # Add to the ZIP
                zipf.write(file_path, rel_path)
                file_count += 1
                
        print(f"  Added {file_count} files to the ZIP")
    
    # Get and display the size
    zip_size = os.path.getsize(zip_name)
    print(f"  ZIP size: {zip_size / (1024 * 1024):.2f} MB")
    
    # Check if within Lambda size limits
    if zip_size > 50 * 1024 * 1024:
        print("  WARNING: ZIP exceeds the direct upload limit of 50 MB for Lambda")
        
    return file_count, zip_size

def main():
    """Main function to create the minimal package"""
    print("Creating Minimal Bedrock Lambda Package")
    print("=" * 60)
    
    # Setup paths
    source_dir = "."
    package_dir = "minimal_bedrock_package"
    zip_name = "minimal_bedrock_lambda.zip"
    
    # Create package directory
    create_package_directory(package_dir)
    
    # Copy files and directories
    file_count = copy_essential_files(source_dir, package_dir)
    dir_count, dir_file_count = copy_essential_dirs(source_dir, package_dir)
    
    # Create the ZIP package
    total_files, zip_size = create_zip_package(package_dir, zip_name)
    
    # Clean up
    print("Cleaning up...")
    shutil.rmtree(package_dir)
    
    print("\n" + "=" * 60)
    print(f"Package created successfully: {zip_name}")
    print(f"Total files: {total_files}")
    print(f"Package size: {zip_size / (1024 * 1024):.2f} MB")
    print("\nNext steps:")
    print("1. Upload this ZIP file to AWS Lambda")
    print("2. Configure your Lambda function to use the uploaded package")
    print("=" * 60)
    
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
