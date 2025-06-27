"""
Create Deployment Package for CDP Wallet and X402 Integration

This script creates a deployment package for AWS Lambda with all required files
for CDP wallet connection and X402 payment functionality.
"""
import os
import shutil
import zipfile
import subprocess
import sys

# Configuration
PACKAGE_NAME = "cdp_wallet_x402_lambda_package.zip"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# List of Python files to include
PYTHON_FILES = [
    "lambda_handler.py",
    "cdp_wallet_handler.py",
    "cdp_wallet_x402_integration.py",
    "x402_payment_handler.py",
    "enhanced_wallet_login.py",
    "config.py",
    "secure_payment_config.py",  # Critical for X402 payment configuration
    "session_manager.py",
    "__init__.py"
]

# List of directories to include
DIRECTORIES = [
    "apis",
    "utils",
    "templates",
    "static"
]

# Create a temporary directory for package building
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp_package")

def create_package():
    """Create the deployment package"""
    print(f"Creating deployment package: {PACKAGE_NAME}")
    
    # Clean up any existing temp directory or package
    cleanup()
    
    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Copy Python files
    for file in PYTHON_FILES:
        if os.path.exists(file):
            print(f"Including file: {file}")
            shutil.copy(file, os.path.join(TEMP_DIR, file))
        else:
            print(f"Warning: File {file} not found, skipping")
    
    # Copy directories
    for directory in DIRECTORIES:
        if os.path.exists(directory):
            print(f"Including directory: {directory}")
            dest_dir = os.path.join(TEMP_DIR, directory)
            shutil.copytree(directory, dest_dir)
        else:
            print(f"Warning: Directory {directory} not found, skipping")
    
    # Install dependencies to the package directory
    install_dependencies()
    
    # Create zip file
    create_zip()
    
    # Clean up temp directory
    shutil.rmtree(TEMP_DIR)
    
    print(f"Deployment package created: {os.path.join(OUTPUT_DIR, PACKAGE_NAME)}")

def install_dependencies():
    """Install required dependencies for CDP wallet and X402 payment"""
    print("Installing dependencies...")
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Creating requirements.txt file")
        with open("requirements.txt", "w") as f:
            f.write("requests>=2.25.1\n")
            f.write("boto3>=1.18.0\n")
    
    # Install dependencies to package directory
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", "requirements.txt",
            "--target", TEMP_DIR,
            "--upgrade"
        ])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def create_zip():
    """Create the deployment zip file"""
    package_path = os.path.join(OUTPUT_DIR, PACKAGE_NAME)
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory
        for root, _, files in os.walk(TEMP_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path for the archive
                arc_name = os.path.relpath(file_path, TEMP_DIR)
                print(f"Adding to zip: {arc_name}")
                zipf.write(file_path, arc_name)

def cleanup():
    """Clean up temporary files and directories"""
    # Remove temp directory if it exists
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # Remove existing package if it exists
    package_path = os.path.join(OUTPUT_DIR, PACKAGE_NAME)
    if os.path.exists(package_path):
        os.remove(package_path)

if __name__ == "__main__":
    create_package()
