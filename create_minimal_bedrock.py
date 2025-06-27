#!/usr/bin/env python3
"""
Minimal AWS Lambda Package Creator for Bedrock Agent Integration

This script creates a minimal Lambda deployment package by:
1. Including only essential code files in the main package
2. Moving all dependencies to layers
3. Splitting dependencies into separate layers if needed
4. Cleaning up unnecessary files to reduce package sizes
"""

import os
import sys
import shutil
import zipfile
import fnmatch
import subprocess
from datetime import datetime

# Define the minimum files needed for Lambda function
ESSENTIAL_FILES = [
    "lambda_handler.py",
    "bedrock_agent_adapter.py",
    "bedrock_agent_connector.py",
    "session_manager.py",
    "wallet_login.py",
    "x402_payment_handler.py",
    "nft_wallet.py",
    "enhanced_bedrock_api.py",
    "apis/__init__.py",
    "utils/__init__.py"
]

# API files that should be included
API_ESSENTIAL_FILES = [
    "apis/__init__.py", 
    "apis/alchemy_api.py", 
    "apis/etherscan_api.py"
]

# Files and directories to exclude from both main package and layer
EXCLUDE_LIST = [
    # Package directories and files
    "lambda_package", "package", "deployment.zip", "lambda_deployment.zip",
    "bedrock_deployment.zip", "bedrock_package", "layer.zip", "layer",
    "bedrock_lambda_*.zip", "bedrock_layer_*.zip",
    
    # Python cache directories
    "__pycache__", ".pytest_cache", "*.pyc",
    
    # Scripts and deployment tools
    "create_*.py",
    "update_lambda_config.sh", "deploy_lambda.py",
    
    # Test files and configuration
    "test_local.py", "test_*.py", "tests",
    
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

def should_include_file(file_path):
    """Determine if a file should be included in the main package"""
    # Check if file is in the essential list
    for essential in ESSENTIAL_FILES:
        if file_path.endswith(essential) or file_path == essential:
            return True
            
    # Check if file is an essential API file
    for api_file in API_ESSENTIAL_FILES:
        if file_path.endswith(api_file) or file_path == api_file:
            return True
            
    return False

def should_exclude(path, exclude_patterns):
    """Determine if a file or directory should be excluded"""
    # Check if the file should be excluded
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    
    return False

def copy_essential_files(source_dir, target_dir):
    """Copy only essential files to the target directory"""
    print(f"\nCopying essential files to {target_dir}...")
    
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Track statistics
    copied_files = 0
    
    # Create needed subdirectories
    for essential in ESSENTIAL_FILES:
        if '/' in essential:
            subdir = os.path.join(target_dir, os.path.dirname(essential))
            if not os.path.exists(subdir):
                os.makedirs(subdir)
    
    # Copy essential files
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            source_file = os.path.join(root, file)
            rel_path = os.path.relpath(source_file, source_dir)
            
            if should_exclude(rel_path, EXCLUDE_LIST):
                continue
                
            if should_include_file(rel_path):
                # Create target directory if needed
                target_file_dir = os.path.dirname(os.path.join(target_dir, rel_path))
                if not os.path.exists(target_file_dir):
                    os.makedirs(target_file_dir)
                
                # Copy the file
                target_file = os.path.join(target_dir, rel_path)
                shutil.copy2(source_file, target_file)
                copied_files += 1
                print(f"  Copied: {rel_path}")
    
    print(f"  Copied {copied_files} essential files")
    return copied_files

def create_requirements_file(layer_dir, requirements_list):
    """Create a requirements.txt file with the specified packages"""
    req_path = os.path.join(layer_dir, "requirements.txt")
    with open(req_path, "w") as f:
        for req in requirements_list:
            f.write(f"{req}\n")
    
    return req_path

def install_dependencies(layer_dir, requirements_file=None, packages=None):
    """Install required packages to the specified directory"""
    print(f"\nInstalling dependencies to {layer_dir}...")
    
    # Create target directory if needed
    target_dir = os.path.join(layer_dir, "python")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-t", target_dir, "--no-cache-dir"]
        
        if requirements_file:
            cmd.extend(["-r", requirements_file])
            print(f"  Installing dependencies from {requirements_file}")
        elif packages:
            cmd.extend(packages)
            print(f"  Installing packages: {', '.join(packages)}")
        else:
            print("  No dependencies specified")
            return False
            
        subprocess.check_call(cmd, shell=False)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  Error installing dependencies: {str(e)}")
        return False

def clean_python_packages(package_dir):
    """Remove unnecessary files from installed packages to reduce size"""
    print(f"\nCleaning installed packages in {package_dir}...")
    
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
    
    # Skip if directory doesn't exist or doesn't contain "python"
    if not os.path.exists(package_dir):
        return 0, 0
        
    python_dir = os.path.join(package_dir, "python") if os.path.exists(os.path.join(package_dir, "python")) else package_dir
    
    # Walk through all files in the package directory
    for root, dirs, files in os.walk(python_dir):
        # First handle directories
        dirs_to_remove = []
        for d in dirs:
            dir_path = os.path.join(root, d)
            rel_path = os.path.relpath(dir_path, python_dir)
            
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
        
        # Handle files
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, python_dir)
            
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
    if zip_name.endswith('layer.zip') and zip_size > 250 * 1024 * 1024:
        print(f"  WARNING: Layer exceeds the Lambda layer size limit of 250 MB!")
    elif not zip_name.endswith('layer.zip') and zip_size > 50 * 1024 * 1024:
        print(f"  WARNING: Package exceeds the Lambda direct upload size limit of 50 MB!")
    
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
    """Main function to create minimal Lambda packages and layers"""
    print("Minimal AWS Lambda Package Creator for Bedrock Agent Integration")
    print("=" * 60)
    
    # Define package directories
    main_package_dir = "bedrock_minimal_code"
    layer_dir_aws = "bedrock_layer_aws"
    layer_dir_web = "bedrock_layer_web"
    
    # Define zip names
    main_zip_name = "bedrock_minimal_code.zip"
    layer_aws_zip_name = "bedrock_layer_aws.zip"
    layer_web_zip_name = "bedrock_layer_web.zip"
    
    # Define layer dependencies
    aws_deps = ["boto3", "botocore", "s3transfer", "jmespath", "python-dateutil", "six", "urllib3"]
    web_deps = ["requests", "fastapi", "uvicorn", "mangum", "pydantic", "jinja2", "aiofiles"]
    
    # Step 1: Clean up old packages
    print("\nStep 1: Cleaning up old packages...")
    for item in [main_package_dir, layer_dir_aws, layer_dir_web, 
                main_zip_name, layer_aws_zip_name, layer_web_zip_name]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
    
    # Step 2: Create directories
    os.makedirs(main_package_dir)
    os.makedirs(layer_dir_aws)
    os.makedirs(layer_dir_web)
    
    # Step 3: Copy only essential files to main package
    copy_essential_files(".", main_package_dir)
    
    # Step 4: Create layers for dependencies
    # AWS Layer
    create_requirements_file(layer_dir_aws, aws_deps)
    install_dependencies(layer_dir_aws, os.path.join(layer_dir_aws, "requirements.txt"))
    clean_python_packages(layer_dir_aws)
    
    # Web Layer
    create_requirements_file(layer_dir_web, web_deps)
    install_dependencies(layer_dir_web, os.path.join(layer_dir_web, "requirements.txt"))
    clean_python_packages(layer_dir_web)
    
    # Step 5: Create ZIP packages
    create_zip_package(main_package_dir, main_zip_name)
    create_zip_package(layer_dir_aws, layer_aws_zip_name)
    create_zip_package(layer_dir_web, layer_web_zip_name)
    
    # Step 6: Verify main package
    verification_files = [
        "lambda_handler.py",
        "bedrock_agent_adapter.py",
        "bedrock_agent_connector.py"
    ]
    verify_package(main_zip_name, verification_files)
    
    # Show deployment commands
    print("\n" + "=" * 60)
    print("Packages created successfully!")
    print("\nDeployment Steps:")
    print("1. Upload the AWS dependencies layer:")
    print(f"   aws lambda publish-layer-version --layer-name bedrock-agent-aws-deps --zip-file fileb://{layer_aws_zip_name}")
    print("\n2. Upload the Web dependencies layer:")
    print(f"   aws lambda publish-layer-version --layer-name bedrock-agent-web-deps --zip-file fileb://{layer_web_zip_name}")
    print("\n3. Note the LayerVersionArn from both responses")
    print("\n4. Upload the main function code:")
    print(f"   aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --zip-file fileb://{main_zip_name}")
    print("\n5. Attach both layers to your function:")
    print("   aws lambda update-function-configuration --function-name YOUR_FUNCTION_NAME --layers [AWSLayerVersionArn] [WebLayerVersionArn]")
    
    # Clean up temporary directories
    print("\nCleaning up temporary directories...")
    shutil.rmtree(main_package_dir)
    shutil.rmtree(layer_dir_aws)
    shutil.rmtree(layer_dir_web)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
