#!/usr/bin/env python3
"""
AWS Lambda Package Creator for Bedrock Agent Integration
This script creates a Lambda deployment package that includes all files needed
for AWS Bedrock agent integration with the NFT payment system.
"""

import os
import sys
import shutil
import zipfile
import fnmatch
import subprocess
from datetime import datetime

# Define required directories and files
REQUIRED_DIRS = ["apis", "utils", "templates", "static"]
REQUIRED_FILES = [
    "lambda_handler.py",
    "config.py",
    "secure_payment_config.py",
    "x402_payment_handler.py",
    "x402_client.js",
    "wallet_login.py",
    "nft_wallet.py",
    "payment_handler.py",
    "bedrock_agent_adapter.py",
    "bedrock_agent_connector.py",
    "bedrock_agent_config.py",
    "mcp_server.py",
    "aws_mcp_server.py",
    "cdp_wallet_connector.js",
    "cdp_wallet_handler.py",
    "utils/x402_processor.py"
]

# API files that should be included
API_FILES = [
    "__init__.py", 
    "alchemy_api.py", 
    "etherscan_api.py", 
    "moralis_api.py",
    "nftgo_api.py", 
    "nftscan_api.py", 
    "opensea_api.py", 
    "perplexity_api.py", 
    "reservoir_api.py"
]

# Files and directories to exclude
EXCLUDE_LIST = [
    # Package directories and files
    "lambda_package", "package", "deployment.zip", "lambda_deployment.zip",
    "bedrock_deployment.zip", "bedrock_package",
    
    # Python cache directories
    "__pycache__", ".pytest_cache", "*.pyc",
    
    # Scripts and deployment tools
    "create_*.py",
    "update_lambda_config.sh", "deploy_lambda.py",
    "deploy_dynamic_pricing.py", "update_lambda_env.py",
    "deploy_aws_mcp_server.py", "setup_aws_mcp_server.py",
    
    # Test files and configuration
    "test_local.py", "test_config.py", "*_test.py", "test_*.py", "tests",
    "test_wallet_login.py", "test_wallet_login.sh", "test_mcp_server.py",
    "test_aws_mcp_server.py", "agent_wallet_test.py",
    
    # Documentation
    "*.md", "*.rst", "*.txt",
    
    # Environment setup files
    "set_env_vars.ps1", ".env", "*.env",
    
    # CloudFormation templates
    "*.yaml", "*.yml",
    
    # Development files
    ".vscode", ".idea", ".git", ".gitignore", ".github",
    
    # Temp and backup files
    "*.tmp", "*.log", "*.bak", "*.swp", "*.swo"
]

# Files to always include even if they match exclude patterns
INCLUDE_OVERRIDE = [
    "templates/payment.html",
    "templates/wallet.html",
    "static/aws-mcp-client.js",
    "requirements.txt",
    "cdp_wallet_connector.js",
    "x402_client.js",
]

def check_requirements():
    """Check if all required files and directories exist"""
    missing = []
    
    # Check directories
    for dir_name in REQUIRED_DIRS:
        if not os.path.isdir(dir_name):
            missing.append(dir_name)
    
    # Check main files
    for file_name in REQUIRED_FILES:
        if not os.path.isfile(file_name):
            missing.append(file_name)
    
    # Check API files
    for api_file in API_FILES:
        api_path = os.path.join("apis", api_file)
        if not os.path.isfile(api_path):
            missing.append(api_path)
    
    return missing

def should_exclude(path, exclude_patterns, include_override):
    """Determine if a file or directory should be excluded"""
    # Always include files in the override list
    for include_pattern in include_override:
        if fnmatch.fnmatch(path, include_pattern) or path.endswith(include_pattern):
            return False
            
    # Check if the file should be excluded
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    
    return False

def copy_files_with_exclusions(source_dir, target_dir):
    """Copy files from source to target, excluding certain patterns"""
    print(f"\nCopying files from {source_dir} to {target_dir}...")
    
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Track statistics
    copied_files = 0
    excluded_files = 0
    
    # Process all files and directories
    for root, dirs, files in os.walk(source_dir):
        # Calculate relative path from source_dir
        rel_path = os.path.relpath(root, source_dir)
        target_path = os.path.join(target_dir, rel_path) if rel_path != '.' else target_dir
        
        # Create target directory if needed
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        
        # Process files
        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_path, file)
            rel_file_path = os.path.join(rel_path, file) if rel_path != '.' else file
            
            # Check if file should be excluded
            if should_exclude(rel_file_path, EXCLUDE_LIST, INCLUDE_OVERRIDE):
                print(f"  Excluding: {rel_file_path}")
                excluded_files += 1
                continue
            
            # Copy the file
            shutil.copy2(source_file, target_file)
            copied_files += 1
            
        # Update dirs list to avoid processing excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(rel_path, d), EXCLUDE_LIST, [])]
    
    return copied_files, excluded_files

def install_dependencies(package_dir):
    """Install required packages from requirements.txt"""
    print("\nInstalling dependencies...")
    requirements_file = "requirements.txt"
    
    if not os.path.isfile(requirements_file):
        print(f"  Warning: {requirements_file} not found, skipping dependency installation")
        return False
    
    try:
        # Try with '--no-dev' flag first (pip 20.3+)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file, 
             "-t", package_dir, "--no-dev", "--no-cache-dir"],
            shell=False
        )
    except subprocess.CalledProcessError:
        # Fall back to regular install if '--no-dev' is not supported
        print("  Warning: '--no-dev' flag not supported, installing all dependencies")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file, 
             "-t", package_dir, "--no-cache-dir"],
            shell=False
        )
    
    return True

def clean_python_packages(package_dir):
    """Remove unnecessary files from installed packages to reduce size"""
    print("\nCleaning installed packages...")
    
    # Files and directories that can be safely removed from packages
    patterns_to_remove = [
        # Tests
        "*/tests/*", "*/test/*", "*_test.py", "test_*.py",
        # Documentation
        "*/doc/*", "*/docs/*", "*.md", "*.rst", 
        # Examples
        "*/examples/*", "*/demo/*", 
        # Development files
        "__pycache__", "*.py[cod]", "*$py.class", ".pytest_cache",
        "*.so", ".git", ".github", ".travis.yml",
        # Build related
        "*/build/*", "*.whl", "*.egg-info", "*.dist-info/RECORD",
    ]
    
    removed_count = 0
    removed_size = 0
    
    # Walk through all files in the package directory
    for root, dirs, files in os.walk(package_dir):
        # First handle directories
        dirs_to_remove = []
        for d in dirs:
            dir_path = os.path.join(root, d)
            rel_path = os.path.relpath(dir_path, package_dir)
            
            # Check if directory matches any pattern
            if any(fnmatch.fnmatch(d, pattern) or fnmatch.fnmatch(rel_path, pattern) 
                  for pattern in patterns_to_remove):
                try:
                    size = sum(os.path.getsize(os.path.join(dp, f)) 
                              for dp, dn, fn in os.walk(dir_path) for f in fn)
                    shutil.rmtree(dir_path)
                    removed_size += size
                    removed_count += 1
                    dirs_to_remove.append(d)
                except Exception as e:
                    print(f"  Error removing directory {rel_path}: {e}")
        
        # Remove processed directories from the list
        for d in dirs_to_remove:
            if d in dirs:
                dirs.remove(d)
        
        # Handle files
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, package_dir)
            
            # Check if file matches any pattern
            if any(fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(rel_path, pattern) 
                  for pattern in patterns_to_remove):
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    removed_size += size
                    removed_count += 1
                except Exception as e:
                    print(f"  Error removing file {rel_path}: {e}")
    
    print(f"  Removed {removed_count} unnecessary files ({removed_size/1048576:.2f} MB)")
    return removed_count, removed_size

def create_zip_package(source_dir, zip_name):
    """Create a ZIP file from the package directory"""
    print(f"\nCreating ZIP package: {zip_name}")
    
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the package directory
        file_count = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Create zip path relative to package directory
                arc_name = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arc_name)
                file_count += 1
        
        print(f"  Added {file_count} files to the ZIP package")
    
    # Calculate package size
    zip_size = os.path.getsize(zip_name)
    print(f"  Package size: {zip_size/1048576:.2f} MB")
    
    # Check if the package exceeds Lambda size limits
    if zip_size > 50 * 1024 * 1024:
        print(f"  WARNING: Package exceeds the Lambda size limit of 50 MB!")
    
    return file_count, zip_size

def verify_package(zip_name, required_files):
    """Verify that all required files are in the ZIP package"""
    print(f"\nVerifying package contents...")
    
    with zipfile.ZipFile(zip_name, "r") as zipf:
        # Get list of all files in the ZIP
        zip_files = zipf.namelist()
        
        # Check for required files
        missing = []
        for file in required_files:
            if file not in zip_files and not any(f.endswith(file) for f in zip_files):
                missing.append(file)
        
        if missing:
            print("  WARNING: The following required files are missing from the package:")
            for file in missing:
                print(f"    - {file}")
            return False
        
        print("  All required files are present in the package")
        return True

def main():
    """Main function to create the Lambda package"""
    print("AWS Lambda Package Creator for Bedrock Agent Integration")
    print("=" * 60)
    
    # Define package name
    package_dir = "bedrock_package"
    zip_name = "bedrock_deployment.zip"
    
    # Step 1: Check requirements
    print("\nStep 1: Checking required files and directories...")
    missing = check_requirements()
    if missing:
        print("  ERROR: The following required files or directories are missing:")
        for item in missing:
            print(f"    - {item}")
        return 1
    
    # Step 2: Clean up old packages
    print("\nStep 2: Cleaning up old packages...")
    for item in [package_dir, zip_name]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
    
    # Step 3: Copy files to package directory
    os.makedirs(package_dir)
    copied, excluded = copy_files_with_exclusions(".", package_dir)
    print(f"  Copied {copied} files, excluded {excluded} files")
    
    # Step 4: Install dependencies
    install_dependencies(package_dir)
    
    # Step 5: Clean up Python packages
    clean_python_packages(package_dir)
    
    # Step 6: Create ZIP package
    file_count, zip_size = create_zip_package(package_dir, zip_name)
    
    # Step 7: Verify package
    verification_files = [
        "lambda_handler.py",
        "bedrock_agent_adapter.py",
        "mcp_server.py",
        "aws_mcp_server.py",
        "wallet_login.py",
        "nft_wallet.py",
        "x402_payment_handler.py"
    ]
    verify_package(zip_name, verification_files)
    
    # Show deployment commands
    print("\n" + "=" * 60)
    print("Package created successfully!")
    print(f"Upload {zip_name} to your AWS Lambda function.")
    print("\nAWS CLI command for deployment:")
    print(f"aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --zip-file fileb://{zip_name}")
    
    # Clean up temporary directory
    print("\nCleaning up temporary files...")
    shutil.rmtree(package_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
