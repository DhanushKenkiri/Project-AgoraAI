# Simple script to create a Lambda deployment package
import os
import shutil
import fnmatch
import zipfile
import sys

def clean_directory(directory):
    """Remove directory if it exists"""
    if os.path.exists(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        else:
            os.remove(directory)

def create_lambda_package():
    print("=== Creating Lambda Deployment Package ===")
    
    # Clean previous package
    for path in ["lambda_package", "lambda_deployment.zip"]:
        clean_directory(path)
    
    # Create package directory
    os.makedirs("lambda_package")
    
    # Files to include
    required_files = [
        "lambda_handler.py",
        "config.py",
        "secure_payment_config.py",
        "agent_payment_handler.py",
        "agent_payment_integration.py",
        "dynamic_pricing_agent.py",
        "x402_payment_handler.py",
        "x402_client.js",
        "cdp_wallet_connector.js",
        "wallet_login.py",
        "cdp_wallet_handler.py",
        "wallet_login_agent_instructions.md"
    ]
    
    # Directories to include
    required_dirs = ["apis", "utils"]
    
    # Files/directories to exclude
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".git*",
        "tests",
        "test_*.py",
        "*_test.py",
        "create_*.py",
        "deploy_*.py",
        "*.zip",
        "*.yaml",
        "*.md",
        "!wallet_login_agent_instructions.md"  # Exception to include this specific MD file
    ]
    
    print("\nCopying required files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
            shutil.copy2(file, os.path.join("lambda_package", file))
        else:
            print(f"  ⚠ Missing: {file}")
    
    print("\nCopying required directories:")
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✓ {dir_name}")
            # Copy only necessary files
            for root, dirs, files in os.walk(dir_name):
                # Exclude directories
                for pattern in exclude_patterns:
                    if pattern.startswith("!"):
                        continue
                    for d in list(dirs):
                        if fnmatch.fnmatch(d, pattern):
                            dirs.remove(d)
                
                # Create subdirectory in package
                rel_path = os.path.relpath(root, ".")
                os.makedirs(os.path.join("lambda_package", rel_path), exist_ok=True)
                
                # Copy files
                for file in files:
                    # Skip excluded files
                    if any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns if not pattern.startswith("!")):
                        continue
                    
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join("lambda_package", rel_path, file)
                    shutil.copy2(src_file, dst_file)
        else:
            print(f"  ⚠ Missing: {dir_name}")
      print("\nCreating ZIP file...")
    with zipfile.ZipFile("lambda_deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda_package"):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, "lambda_package")
                zipf.write(file_path, rel_path)
                print(f"  Added: {rel_path}")
    
    # Get file size
    zip_size = os.path.getsize("lambda_deployment.zip") / (1024 * 1024)  # Size in MB
    
    print(f"\n✅ Deployment package created: lambda_deployment.zip ({zip_size:.2f} MB)")
    
    if zip_size > 50:
        print("⚠️ WARNING: Package exceeds AWS Lambda's 50 MB limit!")
    
    return True

if __name__ == "__main__":
    create_lambda_package()
