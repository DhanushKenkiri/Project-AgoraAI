# This script creates an AWS Lambda optimized package
import os
import subprocess
import shutil
import zipfile
import sys
import fnmatch

def clean_python_packages(package_dir):
    """
    Remove unnecessary files from Python packages to reduce deployment size.
    """
    print("Cleaning Python packages...")
    
    # Files and directories that can be safely removed
    clean_patterns = [
        # Tests
        "*/tests/*", "*/test/*", "*_test.py", "test_*.py",
        # Documentation
        "*/doc/*", "*/docs/*", "*.md", "*.rst", "*.txt", 
        # Examples
        "*/examples/*", "*/demo/*", 
        # Development files
        "*.pyc", "__pycache__", "*.py[cod]", "*$py.class", ".pytest_cache",
        "*.so", "*.pyd", ".git", ".github", ".travis.yml", ".coveragerc",
        # Build related
        "*/build/*", "*.whl", "*.egg-info", "*.dist-info/RECORD",
    ]
    
    # Walk through all packages
    for root, dirs, files in os.walk(package_dir):
        # Remove files matching patterns
        for pattern in clean_patterns:
            for file in fnmatch.filter(files, pattern):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    #print(f"  Removed file: {file_path}")
                except:
                    pass
        
        # Remove directories matching patterns (bottom-up to handle nested dirs)
        for pattern in clean_patterns:
            for dir_name in list(dirs):  # Make a copy since we'll modify dirs
                if fnmatch.fnmatch(dir_name, pattern):
                    dir_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(dir_path)
                        #print(f"  Removed directory: {dir_path}")
                        dirs.remove(dir_name)  # Don't traverse into deleted dir
                    except:
                        pass

def copy_directory_with_exclusions(src_dir, dst_dir, exclude_patterns):
    """
    Copy a directory while excluding files/directories that match any of the patterns in exclude_patterns.
    """
    os.makedirs(dst_dir, exist_ok=True)
    
    for item in os.listdir(src_dir):
        # Skip if item matches any exclusion pattern
        if any(fnmatch.fnmatch(item, pattern) for pattern in exclude_patterns):
            print(f"  Skipping: {os.path.join(src_dir, item)}")
            continue
            
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        
        if os.path.isdir(src_item):
            # Recursively copy subdirectories that aren't excluded
            copy_directory_with_exclusions(src_item, dst_item, exclude_patterns)
        else:
            # Copy files that aren't excluded
            shutil.copy2(src_item, dst_item)

def create_lambda_package():
    """Create a proper Lambda deployment package"""    # First, check if all required files exist
    required_dirs = ["apis", "utils", "templates", "static"]
    
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
        "bedrock_agent_adapter.py",  # Add Bedrock agent adapter
        "mcp_server.py",             # Add MCP server
        "aws_mcp_server.py",         # Add AWS-optimized MCP server
        "nft_wallet.py"              # Add NFT wallet functionality
    ]
    api_files = ["__init__.py", "alchemy_api.py", "etherscan_api.py", "moralis_api.py", 
                "nftgo_api.py", "nftscan_api.py", "opensea_api.py", "perplexity_api.py", "reservoir_api.py"]
    
    # Check directories
    missing = []
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing.append(dir_name)
    
    # Check main files
    for file_name in required_files:
        if not os.path.isfile(file_name):
            missing.append(file_name)
    
    # Check API files
    for api_file in api_files:
        if not os.path.isfile(os.path.join("apis", api_file)):
            missing.append(f"apis/{api_file}")
    
    if missing:
        print("Error: The following required files/directories are missing:")
        for item in missing:
            print(f" - {item}")
        return False
    
    # Clean up old files
    for item in ["package", "lambda_package", "lambda_deployment.zip"]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
    
    # Create a directory for our Lambda package
    os.makedirs("lambda_package")    # Define files and directories to exclude
    exclude_list = [
        # Package directories and files
        "lambda_package", "package", "deployment.zip", "lambda_deployment.zip",
        # Python cache directories
        "__pycache__", ".pytest_cache", "*.pyc",
        
        # Scripts and deployment tools
        "create_lambda_package.py", "create_deployment_package.py", "create_optimized_package.py",
        "create_layer.py", "update_lambda_config.sh", "deploy_lambda.py",
        "deploy_dynamic_pricing.py", "update_lambda_env.py", 
        "deploy_aws_mcp_server.py", "setup_aws_mcp_server.py",
        
        # Test files and configuration
        "test_local.py", "test_config.py", "*_test.py", "test_*.py", "tests",
        "test_wallet_login.py", "test_wallet_login.sh", "test_mcp_server.py", 
        "test_aws_mcp_server.py", "agent_wallet_test.py",
        
        # Documentation and setup guides
        "README.md", "DYNAMIC_PRICING_SETUP.md", "README_DYNAMIC_PRICING.md", 
        "payment_agent_setup_guide.md", "x402_cdp_wallet_integration_guide.md",
        "x402_payment_implementation.md", "nft_payment_flow_diagram.txt",
        "wallet_connection_guide.md", "DEPLOYMENT.md",
        
        # Environment setup files
        "set_env_vars.ps1", ".env", "*.env",
        
        # CloudFormation templates
        "nft_payment_stack.yaml", "nft_payment_stack_fixed.yaml",
        
        # Development files
        ".vscode", ".idea", ".git", ".gitignore", ".github",
        
        # Temp and backup files
        "*.tmp", "*.log", "*.bak", "*.swp", "*.swo"
    ]
    
    # Copy only necessary files (not in excluded list)
    for item in os.listdir("."):
        # Skip excluded items
        if any(fnmatch.fnmatch(item, pattern) for pattern in exclude_list):
            print(f"Skipping: {item}")
            continue
            
        src = item
        dst = os.path.join("lambda_package", item)
        
        if os.path.isdir(src):
            # For directories, use a custom copy function to exclude unnecessary files
            print(f"Copying directory: {src}")
            copy_directory_with_exclusions(src, dst, exclude_list)
        else:
            print(f"Copying file: {src}")
            shutil.copy2(src, dst)    # Install only production dependencies (no dev or test dependencies)
    print("\nInstalling production dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-t", "lambda_package", 
             "--no-dev", "--no-cache-dir", "--quiet"],
            shell=False
        )
    except subprocess.CalledProcessError:
        # Fallback if --no-dev flag isn't supported
        print("  Warning: --no-dev flag not supported, installing all dependencies...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-t", "lambda_package", 
             "--no-cache-dir", "--quiet"],
            shell=False
        )
    
    # Clean up unnecessary files from dependencies to reduce size
    clean_python_packages("lambda_package")
    
    # Create a zip with the correct structure
    print("\nCreating Lambda deployment package...")
    with zipfile.ZipFile("lambda_deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda_package"):
            for file in files:
                file_path = os.path.join(root, file)
                # This ensures the files are at the root of the zip
                arc_name = os.path.relpath(file_path, "lambda_package")
                zipf.write(file_path, arc_name)
      # Verify the zip contents
    with zipfile.ZipFile("lambda_deployment.zip", "r") as zipf:
        file_count = len(zipf.namelist())
        
        # Calculate total size
        total_size = sum(zipinfo.file_size for zipinfo in zipf.infolist())
        zip_size = os.path.getsize("lambda_deployment.zip")
          print(f"\nZIP Statistics:")
        print(f"  - Files included: {file_count}")
        print(f"  - Uncompressed size: {total_size / (1024*1024):.2f} MB")
        print(f"  - Compressed size: {zip_size / (1024*1024):.2f} MB")
        print(f"  - Compression ratio: {(1 - zip_size/total_size) * 100:.1f}%")
        
        if zip_size > 50 * 1024 * 1024:
            print(f"\n⚠️  WARNING: ZIP file exceeds Lambda size limit of 50 MB!")
            
        # Check critical files
        print("\nChecking critical files:")
        critical_files = [
            # Core Lambda files
            "lambda_handler.py", 
            "config.py",
            "secure_payment_config.py",
            
            # Payment handlers
            "agent_payment_handler.py",
            "agent_payment_integration.py",
            "dynamic_pricing_agent.py",
            "x402_payment_handler.py",
            
            # Wallet functionality
            "wallet_login.py",
            "cdp_wallet_handler.py",
            "nft_wallet.py",
            
            # Javascript integration files
            "x402_client.js",
            "cdp_wallet_connector.js",
            
            # Bedrock Agent and MCP integration
            "bedrock_agent_adapter.py",
            "mcp_server.py",
            "aws_mcp_server.py",
            
            # API modules
            "apis/__init__.py", 
            "apis/reservoir_api.py", 
            "apis/opensea_api.py", 
            "apis/nftgo_api.py",
            "apis/moralis_api.py",
            "apis/alchemy_api.py",
            "apis/perplexity_api.py",
            
            # Utils
            "utils/x402_processor.py",
            "utils/__init__.py",
            "utils/utils.py",
            "utils/recommendations.py",
            "utils/sentiment.py",
            "utils/payment_integration.py"
        ]
        missing_files = []
        
        for file in critical_files:
            if file in zipf.namelist():
                print(f"  ✓ Found {file}")
            else:
                print(f"  ✗ MISSING: {file}")
                missing_files.append(file)
        
        if missing_files:
            print(f"\n❌ ERROR: {len(missing_files)} critical files are missing from the package!")
            return False
        else:
            print("\n✅ All critical files are present in the package")
    
    print("\n📦 Package created: lambda_deployment.zip")
    print("   Upload this file to your AWS Lambda function")
    
    # Provide command for AWS CLI users    print("\nOR deploy via AWS CLI:")
    print(f"   aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --zip-file fileb://lambda_deployment.zip")
    return True

if __name__ == "__main__":
    create_lambda_package()
    
    # Count removed items
    removed_count = 0
    removed_size = 0
    
    # Walk through all files in the package directory
    for root, dirs, files in os.walk(package_dir):
        # Check directories first (remove them and their contents)
        dirs_to_remove = []
        for d in dirs:
            dir_path = os.path.join(root, d)
            rel_path = os.path.relpath(dir_path, package_dir)
            
            # Check if directory matches any pattern
            if any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns_to_remove):
                dir_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(dir_path) for f in fn)
                removed_size += dir_size
                removed_count += 1
                dirs_to_remove.append(d)
                print(f"  Removing directory: {rel_path} ({dir_size/1024:.1f} KB)")
                shutil.rmtree(dir_path)
        
        # Update dirs list to avoid processing removed directories
        for d in dirs_to_remove:
            dirs.remove(d)
        
        # Now check files
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, package_dir)
            
            # Check if file matches any pattern
            if any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns_to_remove):
                file_size = os.path.getsize(file_path)
                removed_size += file_size
                removed_count += 1
                print(f"  Removing file: {rel_path} ({file_size/1024:.1f} KB)")
                os.remove(file_path)
    
    print(f"\nRemoved {removed_count} unnecessary files/directories ({removed_size/1048576:.2f} MB)")
    
    # Create a file to indicate that the package has been cleaned
    with open(os.path.join(package_dir, '.cleaned'), 'w') as f:
        f.write(f"Cleaned {removed_count} files ({removed_size} bytes) at {os.path.basename(__file__)} on {os.path.basename}")

if __name__ == "__main__":
    create_lambda_package()
