#!/usr/bin/env python
"""
Complete Lambda Deployment Package Creator

This script creates a comprehensive deployment package (ZIP) for AWS Lambda,
including all necessary files and dependencies.
"""
import os
import zipfile
import shutil
import sys
import json
import importlib.util
import pkgutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the core files to include
CORE_FILES = [
    'lambda_handler.py',
    'cdp_wallet_x402_integration.py',
    'config.py',
    'x402_payment_handler.py',
    'x402_client.js',
    'enhanced_wallet_login.py',
    'wallet_login.py',
    'nft_wallet.py',
    'image_processor.py',
    'nft_image_processor.py',
    'bedrock_integration.py',
    'payment_config.py',
]

# Define directories to include
CORE_DIRS = [
    'apis',
    'utils'
]

# Output zip file
OUTPUT_ZIP = 'lambda_deployment_complete.zip'

def get_module_dependencies(module_name):
    """Try to find dependencies for a given module"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec:
            return [module_name]
        return []
    except (ImportError, AttributeError):
        return []

def is_aws_built_in(module_name):
    """Check if a module is built into AWS Lambda Python runtime"""
    builtin_modules = [
        'boto3', 'botocore', 'json', 'datetime', 'time',
        'os', 'sys', 'math', 'random', 're', 'uuid',
        'hashlib', 'base64', 'logging', 'urllib', 'io',
        'contextlib', 'tempfile', 'decimal', 'threading',
        'queue', 'collections', 'functools', 'itertools'
    ]
    return module_name in builtin_modules or module_name.startswith('aws')

def create_deployment_package():
    """Create a comprehensive deployment package for AWS Lambda"""
    logger.info("Creating deployment package...")
    
    # Remove existing zip if it exists
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)
        logger.info(f"Removed existing {OUTPUT_ZIP}")
    
    # Create a new zip file
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add core files
        for file_name in CORE_FILES:
            if os.path.exists(file_name):
                logger.info(f"Adding file: {file_name}")
                zipf.write(file_name)
            else:
                logger.warning(f"File not found: {file_name}, skipping")
        
        # Add core directories
        for dir_name in CORE_DIRS:
            if os.path.exists(dir_name) and os.path.isdir(dir_name):
                logger.info(f"Adding directory: {dir_name}")
                for root, _, files in os.walk(dir_name):
                    for file in files:
                        if file.endswith('.py') or file == '__init__.py' or not (file.endswith('.pyc') or '__pycache__' in root):
                            file_path = os.path.join(root, file)
                            logger.info(f"  - {file_path}")
                            zipf.write(file_path)
            else:
                logger.warning(f"Directory not found: {dir_name}, skipping")
    
    # Get the size of the zip file
    zip_size = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    logger.info(f"\nDeployment package created: {OUTPUT_ZIP}")
    logger.info(f"Package size: {zip_size:.2f} MB")

if __name__ == "__main__":
    create_deployment_package()
