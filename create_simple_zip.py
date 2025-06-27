# Simple script to create a Lambda deployment package
import os
import shutil
import zipfile

def create_zip():
    print("Creating Lambda deployment package...")
    
    # Clean up old files
    if os.path.exists("lambda_deployment.zip"):
        os.remove("lambda_deployment.zip")
        
    # Create the zip file
    with zipfile.ZipFile("lambda_deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add main handler files
        essential_files = [
            "lambda_handler.py",
            "config.py",
            "secure_payment_config.py",
            "wallet_login.py",
            "nft_wallet.py",  # Added nft_wallet.py
            "cdp_wallet_handler.py",
            "x402_payment_handler.py",
            "wallet_login_agent_instructions.md",
            "agent_payment_handler.py",
            "agent_payment_integration.py",
            "dynamic_pricing_agent.py",
            "x402_client.js",
            "cdp_wallet_connector.js"
        ]
        
        for file in essential_files:
            if os.path.exists(file):
                print(f"Adding file: {file}")
                zipf.write(file)
            else:
                print(f"Warning: {file} not found")
        
        # Add API modules
        if os.path.exists("apis"):
            for root, dirs, files in os.walk("apis"):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        print(f"Adding API: {file_path}")
                        zipf.write(file_path)
                        
        # Add utility modules
        if os.path.exists("utils"):
            for root, dirs, files in os.walk("utils"):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        print(f"Adding utility: {file_path}")
                        zipf.write(file_path)
    
    # Print size information
    size_mb = os.path.getsize("lambda_deployment.zip") / (1024 * 1024)
    print(f"\nDeployment package created: lambda_deployment.zip ({size_mb:.2f} MB)")
    print("You can now deploy this package to AWS Lambda")

if __name__ == "__main__":
    create_zip()