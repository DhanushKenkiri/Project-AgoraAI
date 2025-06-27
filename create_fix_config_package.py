#!/usr/bin/env python3
"""
Fix Config Package Creator for Lambda

This script creates a Lambda package that resolves the 'No module named config' error
by creating a comprehensive config.py file with all necessary variables and settings.
"""

import os
import zipfile
import shutil
import glob
import re

def find_config_imports():
    """Find all files that import a config module"""
    print("Searching for files that import 'config' module...")
    
    imports = []
    # Search for import statements in all Python files
    for file_path in glob.glob('**/*.py', recursive=True):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                content = f.read()
                # Look for import statements
                if re.search(r'import\s+config\b', content) or re.search(r'from\s+config\s+import', content):
                    imports.append(file_path)
                    print(f"  Found config import in {file_path}")
            except Exception as e:
                print(f"  Error reading {file_path}: {e}")
    
    return imports

def create_config_py():
    """Create a comprehensive config.py file"""
    print("Creating comprehensive config.py file...")
    
    config_content = """# Comprehensive configuration for AWS Lambda function

# AWS Bedrock settings
BEDROCK_AGENT_ID = "LRKVLMX55I"  # AgoraAI_BASEMain
BEDROCK_REGION = "ap-south-1"
BEDROCK_AGENT_ALIAS = "default-runtime-alias"

# DynamoDB settings
BEDROCK_SESSIONS_TABLE = "NFTBedrockSessions-prod"

# AWS settings
AWS_REGION = "ap-south-1"

# NFT API settings
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY", "")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY", "")
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

# Payment settings
DEFAULT_PAYMENT_AMOUNT = "0.005"
DEFAULT_PAYMENT_CURRENCY = "ETH"
PAYMENT_CONTRACT_ADDRESS = "0x123abc"

# Import variables from bedrock_agent_config if available
try:
    from bedrock_agent_config import *
except ImportError:
    pass

# Get overrides from environment variables
import os
BEDROCK_AGENT_ID = os.getenv("BEDROCK_AGENT_ID", BEDROCK_AGENT_ID)
BEDROCK_REGION = os.getenv("BEDROCK_REGION", BEDROCK_REGION)
BEDROCK_AGENT_ALIAS = os.getenv("BEDROCK_AGENT_ALIAS", BEDROCK_AGENT_ALIAS)
BEDROCK_SESSIONS_TABLE = os.getenv("BEDROCK_SESSIONS_TABLE", BEDROCK_SESSIONS_TABLE)
"""
    
    return config_content

def create_fixed_package():
    """Create a Lambda package with fixed config imports"""
    print("Creating Lambda package with fixed config imports...")
    
    # Create a temporary directory for the package
    if os.path.exists('fixed_package'):
        shutil.rmtree('fixed_package')
    os.makedirs('fixed_package')
    
    # Create config.py file
    with open('fixed_package/config.py', 'w', encoding='utf-8') as f:
        f.write(create_config_py())
    
    # Add the import fix to the main handler
    try:
        with open('lambda_handler.py', 'r', encoding='utf-8') as f:
            handler_code = f.read()
        
        import_fix = """import os
import sys

# Add the current directory to Python path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'apis'))
sys.path.append(os.path.join(current_dir, 'utils'))

"""
        
        # Write the modified handler
        with open('fixed_package/lambda_handler.py', 'w', encoding='utf-8') as f:
            f.write(import_fix + handler_code)
        print("  Added import paths fix to lambda_handler.py")
    except Exception as e:
        print(f"  Error processing lambda_handler.py: {e}")
    
    # Copy all Python files from the current directory
    for py_file in glob.glob('*.py'):
        if py_file != 'create_fix_config_package.py' and not py_file.startswith('create_'):
            try:
                shutil.copy(py_file, os.path.join('fixed_package', py_file))
                print(f"  Copied {py_file}")
            except Exception as e:
                print(f"  Error copying {py_file}: {e}")
    
    # Copy all directories
    for directory in ['apis', 'utils']:
        if os.path.exists(directory):
            try:
                shutil.copytree(directory, os.path.join('fixed_package', directory))
                print(f"  Copied directory {directory}")
            except Exception as e:
                print(f"  Error copying directory {directory}: {e}")
    
    # Copy bedrock_agent_config.py if available in lambda_slim_code
    slim_code_config = 'lambda_slim_code/bedrock_agent_config.py'
    if os.path.exists(slim_code_config):
        try:
            shutil.copy(slim_code_config, os.path.join('fixed_package', 'bedrock_agent_config.py'))
            print(f"  Copied {slim_code_config}")
        except Exception as e:
            print(f"  Error copying {slim_code_config}: {e}")
    
    # Create the zip file
    with zipfile.ZipFile('fixed_config_package.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('fixed_package'):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'fixed_package')
                    zipf.write(file_path, arcname)
                except Exception as e:
                    print(f"  Error adding {file} to zip: {e}")
    
    # Check the size of the zip file
    size_bytes = os.path.getsize('fixed_config_package.zip')
    size_mb = size_bytes / (1024 * 1024)
    print(f"Created fixed_config_package.zip ({size_mb:.2f} MB)")

def main():
    """Main function"""
    print("=" * 60)
    print("Fix Config Package Creator for Lambda")
    print("=" * 60)
    
    # Find files that import config module
    files_with_imports = find_config_imports()
    
    # Create the fixed package
    create_fixed_package()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Upload fixed_config_package.zip to your AWS Lambda function")
    print("2. Test the function again")
    print("=" * 60)
    
    if files_with_imports:
        print("\nFound config imports in the following files:")
        for file_path in files_with_imports:
            print(f"  - {file_path}")
    else:
        print("\nNo explicit config imports found.")
        print("The error might be from an indirect import or dynamic import.")
    
    print("\nThe package includes a comprehensive config.py with all likely variables.")
    print("=" * 60)

if __name__ == "__main__":
    main()
