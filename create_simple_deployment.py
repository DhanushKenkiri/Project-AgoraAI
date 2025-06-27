# This script packages your Lambda function with dependencies - simplified version
import os
import subprocess
import shutil
import zipfile
import time

print("Creating deployment package for Lambda...")

# Create a timestamp for the package name
timestamp = time.strftime("%Y%m%d%H%M%S")
package_name = f"deployment_{timestamp}.zip"

# Remove existing package directory if it exists
if os.path.exists("package"):
    print("Removing existing package directory...")
    shutil.rmtree("package")

# Create a fresh directory for dependencies
os.makedirs("package")
print("Created package directory")

# Install dependencies into the package directory
print("Installing dependencies...")
try:
    subprocess.check_call(
        f"pip install -r requirements.txt -t package",
        shell=True)
    print("Dependencies installed successfully")
except Exception as e:
    print(f"Warning: Error installing dependencies: {str(e)}")

# Copy necessary files to package directory
print("Copying function code...")
files_to_copy = [
    "lambda_handler.py",
    "config.py",
    "utils",
    "apis"
]

for item in files_to_copy:
    try:
        if os.path.isdir(item):
            if os.path.exists(f"package/{item}"):
                shutil.rmtree(f"package/{item}")
            shutil.copytree(item, f"package/{item}")
            print(f"Copied directory {item}")
        elif os.path.exists(item):
            shutil.copy2(item, "package")
            print(f"Copied file {item}")
        else:
            print(f"Warning: {item} not found")
    except Exception as e:
        print(f"Warning: Could not copy {item}: {str(e)}")

# Create zip file
print("Creating zip file...")
try:
    with zipfile.ZipFile(package_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files in the package directory
        for root, dirs, files in os.walk("package"):
            for file in files:
                file_path = os.path.join(root, file)
                # Add file to zip with proper path
                zipf.write(
                    file_path, 
                    os.path.relpath(file_path, "package")
                )
    
    print(f"Successfully created {package_name}")
    
    # Verify zip file was created
    if os.path.exists(package_name):
        zip_size = os.path.getsize(package_name) / (1024 * 1024)  # Size in MB
        print(f"Deployment package size: {zip_size:.2f} MB")
        
        # Check if the zip file has expected content
        with zipfile.ZipFile(package_name, "r") as check_zip:
            file_count = len(check_zip.namelist())
            print(f"Package contains {file_count} files")
            
            # Check for critical files
            critical_files = ["lambda_handler.py", "config.py"]
            missing = []
            for file in critical_files:
                if file not in check_zip.namelist():
                    missing.append(file)
            
            if missing:
                print(f"WARNING: Missing critical files: {', '.join(missing)}")
            else:
                print("All critical files present in the package")
    else:
        print(f"ERROR: Failed to create {package_name}")
        
except Exception as e:
    print(f"Error creating zip file: {str(e)}")

print("Deployment package creation complete.")
