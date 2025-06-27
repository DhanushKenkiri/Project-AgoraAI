"""
AWS MCP Server Setup Script

This script sets up the AWS MCP server for local development and testing.
It installs the required dependencies and creates the necessary templates.
"""

import os
import sys
import subprocess
import argparse

def check_directory_structure():
    """Check if the required directory structure exists"""
    print("Checking directory structure...")
    
    required_dirs = [
        "templates",
        "static"
    ]
    
    required_files = [
        "aws_mcp_server.py",
        "requirements.txt"
    ]
    
    # Check directories
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"Creating directory: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
    
    # Check files
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"Warning: Missing required files: {', '.join(missing_files)}")
        return False
    
    return True

def install_dependencies():
    """Install the required dependencies"""
    print("Installing dependencies...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def test_server():
    """Test the server locally"""
    print("Testing the server locally...")
    
    try:
        subprocess.run(
            [sys.executable, "test_aws_mcp_server.py"],
            check=True
        )
        return True
    except Exception as e:
        print(f"Error testing server: {str(e)}")
        return False

def start_server():
    """Start the server for local development"""
    print("Starting the AWS MCP server...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "aws_mcp_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            check=True
        )
        return True
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        return False

def prepare_for_aws_deployment():
    """Prepare for AWS deployment"""
    print("Preparing for AWS deployment...")
    
    try:
        # Check if aws_mcp_server.py exists
        if not os.path.exists("aws_mcp_server.py"):
            print("Error: aws_mcp_server.py not found")
            return False
        
        # Check if deploy_aws_mcp_server.py exists
        if not os.path.exists("deploy_aws_mcp_server.py"):
            print("Error: deploy_aws_mcp_server.py not found")
            return False
        
        print("\nAWS deployment preparation complete!")
        print("\nTo deploy to AWS, run:")
        print("python deploy_aws_mcp_server.py --name your-function-name [--region your-region]")
        
        return True
    except Exception as e:
        print(f"Error preparing for AWS deployment: {str(e)}")
        return False

def open_example_page():
    """Open the example integration page"""
    print("Opening example integration page...")
    
    example_path = "aws_mcp_integration_example.html"
    if not os.path.exists(example_path):
        print(f"Error: {example_path} not found")
        return False
    
    # Get absolute path
    abs_path = os.path.abspath(example_path)
    url = f"file:///{abs_path}"
    
    # Try to open the page in the default browser
    try:
        import webbrowser
        webbrowser.open(url)
        print(f"Opened {url} in the default browser")
        return True
    except Exception as e:
        print(f"Error opening example page: {str(e)}")
        print(f"Please manually open: {abs_path}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AWS MCP Server Setup Script")
    parser.add_argument("--install", action="store_true", help="Install dependencies")
    parser.add_argument("--test", action="store_true", help="Test the server locally")
    parser.add_argument("--start", action="store_true", help="Start the server for local development")
    parser.add_argument("--prepare-aws", action="store_true", help="Prepare for AWS deployment")
    parser.add_argument("--example", action="store_true", help="Open the example integration page")
    args = parser.parse_args()
    
    # Check directory structure
    if not check_directory_structure():
        print("Please make sure all required files are available")
        return 1
    
    # Run requested actions
    if args.install:
        if not install_dependencies():
            return 1
    
    if args.test:
        if not test_server():
            return 1
    
    if args.prepare_aws:
        if not prepare_for_aws_deployment():
            return 1
    
    if args.example:
        if not open_example_page():
            return 1
    
    if args.start:
        if not start_server():
            return 1
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\nNo action requested. Use one or more options to perform actions.")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
