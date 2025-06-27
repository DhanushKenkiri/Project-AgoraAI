# This script packages your Lambda function with dependencies
import os
import subprocess
import shutil
import zipfile
import time

print(f"Starting Lambda deployment package creation at {time.strftime('%H:%M:%S')}")

# Clean up any existing files
if os.path.exists("deployment.zip"):
    print("Removing existing deployment.zip...")
    os.remove("deployment.zip")

if os.path.exists("package"):
    print("Removing existing package directory...")
    shutil.rmtree("package")

# Create a clean package directory
print("Creating fresh package directory...")
os.makedirs("package")

# Install dependencies
print("Installing dependencies...")
try:
    subprocess.check_call("pip install -r requirements.txt -t package", shell=True)
    print("Dependencies installed successfully.")
except Exception as e:
    print(f"Warning: Error installing dependencies: {str(e)}")
    print("Continuing with package creation anyway...")

# Copy function code files - exclude package directory, deployment zip, and cache files
print("Copying function code...")
exclude_items = ["package", "create_deployment_package.py", "deployment.zip", "__pycache__"]

# First copy all the Python files
for item in os.listdir("."):
    if item not in exclude_items:
        src_path = os.path.join(".", item)
        dst_path = os.path.join("package", item)
        
        try:
            if os.path.isdir(src_path):
                print(f"Copying directory: {item}")
                # Use ignore function to skip __pycache__ directories
                shutil.copytree(src_path, dst_path, 
                               ignore=shutil.ignore_patterns('__pycache__'),
                               dirs_exist_ok=True)
            else:
                print(f"Copying file: {item}")
                shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"Warning: Could not copy {item}: {str(e)}")

# Create the deployment zip package
print("Creating deployment zip file...")
try:
    with zipfile.ZipFile("deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the package directory and add all files
        file_count = 0
        for root, _, files in os.walk("package"):
            for file in files:
                file_path = os.path.join(root, file)
                # We want paths relative to the package directory for Lambda
                archive_path = os.path.relpath(file_path, "package")
                print(f"Adding to zip: {archive_path}")
                zipf.write(file_path, archive_path)
                file_count += 1
                
        print(f"Added {file_count} files to the deployment package")
    
    # Verify the zip was created and contains essential files
    if os.path.exists("deployment.zip"):
        size_mb = os.path.getsize("deployment.zip") / (1024 * 1024)
        print(f"Deployment package created: deployment.zip ({size_mb:.2f} MB)")
        
        # Check for critical files
        print("Verifying essential files are in the package:")
        try:
            with zipfile.ZipFile("deployment.zip", "r") as zip_verify:
                essential_files = ["lambda_handler.py", "utils/x402_processor.py"]
                for file in essential_files:
                    if file in zip_verify.namelist():
                        print(f"✓ Found {file}")
                    else:
                        print(f"✗ MISSING: {file}")
        except Exception as e:
            print(f"Error verifying zip contents: {str(e)}")
    else:
        print("ERROR: Failed to create deployment.zip")
except Exception as e:
    print(f"ERROR: Failed to create deployment package: {str(e)}")

print(f"Deployment package creation completed at {time.strftime('%H:%M:%S')}")
print("Upload deployment.zip to your Lambda function.")
