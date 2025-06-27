# This script creates an AWS Lambda optimized deployment package
# It will help fix the Lambda response processing errors

import os
import subprocess
import shutil
import zipfile
import sys
import json

# Function to print colored text
def print_color(text, color):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

print_color("Creating optimized Lambda deployment package...", "blue")

# First, clean up any old deployment files
for item in ["package", "lambda_deployment.zip"]:
    if os.path.exists(item):
        print(f"Removing old {item}...")
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

# Create directory for the package
print("Creating package directory...")
os.makedirs("package")

# Install dependencies
print_color("Installing dependencies...", "blue")
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-t", "package"],
    shell=True
)

# Copy function code
print_color("Copying function code...", "blue")
for item in os.listdir("."):
    if item not in ["package", "lambda_deployment.zip", "__pycache__"]:
        if os.path.isdir(item):
            print(f"Copying directory: {item}")
            shutil.copytree(item, os.path.join("package", item))
        elif os.path.isfile(item) and item.endswith('.py'):
            print(f"Copying file: {item}")
            shutil.copy2(item, os.path.join("package", item))

# Create ZIP file with the correct structure
print_color("Creating ZIP archive...", "blue")
with zipfile.ZipFile("lambda_deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    # Walk the directory and add all files
    for root, dirs, files in os.walk("package"):
        for file in files:
            file_path = os.path.join(root, file)
            # Add to zip with the right path relative to package dir
            archive_name = os.path.relpath(file_path, "package")
            zipf.write(file_path, archive_name)

# Verify the package
print_color("Verifying package...", "blue")
with zipfile.ZipFile("lambda_deployment.zip", "r") as zipf:
    file_list = zipf.namelist()
    
    # Check for critical files
    critical_files = [
        "lambda_handler.py", 
        "apis/nftscan_api.py", 
        "apis/moralis_api.py", 
        "apis/__init__.py",
        "utils/__init__.py",
        "config.py"
    ]
    
    missing_files = []
    for file in critical_files:
        if file in file_list:
            print_color(f"✓ Found {file}", "green")
        else:
            print_color(f"✗ MISSING: {file}", "red")
            missing_files.append(file)
    
    # Check total size
    total_size = sum(zipinfo.file_size for zipinfo in zipf.infolist())
    print(f"Total package size: {total_size / (1024*1024):.2f} MB")
    
    if total_size > 50 * 1024 * 1024:
        print_color("WARNING: Package is larger than 50MB AWS Lambda limit", "red")
    
    # Count files
    print(f"Total files: {len(file_list)}")

if missing_files:
    print_color("\nWARNING: Some critical files are missing from the package!", "red")
    sys.exit(1)
else:
    print_color("\nPackage validation successful!", "green")
    print_color("\nDeployment package created: lambda_deployment.zip", "blue")
    print("To deploy:")
    print("1. Go to AWS Lambda Console")
    print("2. Select your function")
    print("3. In the Code tab, click 'Upload from'")
    print("4. Choose '.zip file' and upload lambda_deployment.zip")
    print("5. Update your function timeout to at least 30 seconds")
    print("   (Configuration tab > General configuration > Edit)")
