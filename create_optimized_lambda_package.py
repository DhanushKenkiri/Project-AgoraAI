#!/usr/bin/env python
"""
Optimized Lambda Deployment Package Creator

Creates a minimal deployment package for AWS Lambda under 50MB by:
1. Including only necessary Python files
2. Excluding __pycache__, tests, and other unnecessary files
3. Optimizing dependencies by only including what's needed
"""
import os
import sys
import zipfile
import shutil
import tempfile
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("deployment")

# Output zip file
OUTPUT_ZIP = 'lambda_deployment_optimized.zip'

# Core files needed for the Lambda function
CORE_FILES = [
    'lambda_handler.py',
    'cdp_wallet_x402_integration.py',
    'config.py',
    'x402_client.js',
    'cdp_wallet_connector.js'
]

# Core directories (will be scanned for .py files only)
CORE_DIRS = [
    'apis',
    'utils'
]

# Minimal required packages (these will be installed to the package)
REQUIRED_PACKAGES = [
    'requests',
    'boto3'
]

# Files and directories to exclude completely
EXCLUDE_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git',
    '.github',
    '.vscode',
    'tests',
    'test_*',
    '*_test.py',
    'venv',
    'env',
    '.env',
    'node_modules',
    '.DS_Store',
    '*.zip',
    '*.log'
]

def should_exclude(path):
    """Check if a path should be excluded based on patterns"""
    path_str = str(path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def create_temp_dir():
    """Create a temporary directory for building the package"""
    temp_dir = Path(tempfile.mkdtemp(prefix="lambda_build_"))
    logger.info(f"Created temporary build directory: {temp_dir}")
    return temp_dir

def copy_core_files(source_dir, target_dir):
    """Copy core files to the build directory"""
    logger.info("Copying core files...")
    for file in CORE_FILES:
        source_file = source_dir / file
        if source_file.exists():
            shutil.copy2(source_file, target_dir)
            logger.info(f"  - Copied {file}")
        else:
            logger.warning(f"  - Warning: {file} not found, skipping")

def copy_core_directories(source_dir, target_dir):
    """Copy core directories, but only .py files"""
    logger.info("Copying core directories...")
    for dir_name in CORE_DIRS:
        source_subdir = source_dir / dir_name
        if not source_subdir.exists():
            logger.warning(f"  - Warning: Directory {dir_name} not found, skipping")
            continue
            
        # Create the target directory
        target_subdir = target_dir / dir_name
        target_subdir.mkdir(exist_ok=True)
        
        # Copy all .py files from the source directory
        logger.info(f"  - Processing directory {dir_name}")
        for file_path in source_subdir.glob('**/*.py'):
            if should_exclude(file_path):
                continue
                
            # Create relative path structure
            relative_path = file_path.relative_to(source_subdir)
            target_file = target_subdir / relative_path
            
            # Create directories if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(file_path, target_file)
            logger.info(f"    - Copied {file_path.relative_to(source_dir)}")

def install_dependencies(target_dir):
    """Install minimal dependencies into the package"""
    logger.info("Installing minimal dependencies...")
    
    if not REQUIRED_PACKAGES:
        logger.info("  - No dependencies to install")
        return
    
    # Change to the target directory
    original_dir = os.getcwd()
    os.chdir(target_dir)
    
    try:
        # Install packages
        packages_str = ' '.join(REQUIRED_PACKAGES)
        cmd = f"{sys.executable} -m pip install {packages_str} --target . --no-cache-dir --no-deps"
        logger.info(f"  - Running: {cmd}")
        
        # Execute the pip install
        subprocess.check_call(cmd, shell=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
    finally:
        # Return to the original directory
        os.chdir(original_dir)

def create_deployment_package(source_dir, build_dir):
    """Create the final ZIP package"""
    logger.info(f"Creating deployment package: {OUTPUT_ZIP}")
    
    # Remove existing zip if it exists
    output_path = source_dir / OUTPUT_ZIP
    if output_path.exists():
        output_path.unlink()
        logger.info(f"  - Removed existing {OUTPUT_ZIP}")
    
    # Create a new zip file
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(build_dir):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                if should_exclude(file_path):
                    continue
                    
                # Calculate the archive path (relative to build_dir)
                archive_path = file_path.relative_to(build_dir)
                
                # Add the file to the ZIP
                zipf.write(file_path, str(archive_path))
                
    # Get and log the size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Package created successfully: {OUTPUT_ZIP} ({size_mb:.2f} MB)")
    
    if size_mb > 50:
        logger.warning(f"Warning: Package size exceeds 50MB limit ({size_mb:.2f} MB)")
    
    return output_path

def main():
    """Main function to create the deployment package"""
    logger.info("Starting optimized Lambda package creation")
    
    # Get the source directory (where this script is located)
    source_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Create a temporary build directory
        build_dir = create_temp_dir()
        
        # Copy core files and directories
        copy_core_files(source_dir, build_dir)
        copy_core_directories(source_dir, build_dir)
        
        # Install minimal dependencies
        install_dependencies(build_dir)
        
        # Create the deployment package
        package_path = create_deployment_package(source_dir, build_dir)
        
        logger.info(f"Deployment package created successfully: {package_path}")
        logger.info(f"You can now upload this file to AWS Lambda")
        
    except Exception as e:
        logger.error(f"Error creating deployment package: {e}", exc_info=True)
        return 1
    finally:
        # Clean up the temporary directory
        if 'build_dir' in locals():
            shutil.rmtree(build_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary build directory")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
