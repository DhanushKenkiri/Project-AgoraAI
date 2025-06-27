"""
Simple script to create a minimal package with the required files
"""
import os
import shutil
import zipfile

def create_simple_fix():
    """Create a simple zip file with all required files"""
    
    print("Creating simple fix package...")
    
    # Define essential files
    essential_files = [
        "lambda_handler.py",
        "config.py",
        "secure_payment_config.py",
        "payment_handler.py", 
        "payment_config.py",
        "x402_payment_handler.py",
        "x402_client.js",
        "cdp_wallet_connector.js"
    ]
    
    # Optional files that are good to include if they exist
    optional_files = [
        "enhanced_wallet_login.py",
        "image_processor.py",
        "nft_image_processor.py",
        "bedrock_integration.py",
        "session_manager.py",
        "wallet_login.py",
        "nft_wallet.py",
        "agent_payment_integration.py",
        "dynamic_pricing_agent.py"
    ]
    
    # Remove existing zip if it exists
    if os.path.exists("lambda_simple_fix.zip"):
        os.remove("lambda_simple_fix.zip")
    
    # Create a new zip file
    with zipfile.ZipFile("lambda_simple_fix.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add essential files
        for file in essential_files:
            if os.path.exists(file):
                print(f"Adding {file}")
                zipf.write(file)
            else:
                print(f"Warning: {file} not found, skipping")
        
        # Add optional files
        for file in optional_files:
            if os.path.exists(file):
                print(f"Adding optional file {file}")
                zipf.write(file)
        
        # Add API files
        if os.path.exists("apis"):
            for file in os.listdir("apis"):
                if file.endswith(".py"):
                    file_path = os.path.join("apis", file)
                    print(f"Adding {file_path}")
                    zipf.write(file_path)
        
        # Add utility files
        if os.path.exists("utils"):
            for file in os.listdir("utils"):
                if file.endswith(".py"):
                    file_path = os.path.join("utils", file)
                    print(f"Adding {file_path}")
                    zipf.write(file_path)
    
    print(f"\nCreated lambda_simple_fix.zip with {sum(1 for _ in zipfile.ZipFile('lambda_simple_fix.zip', 'r').namelist())} files")
    print("List of files in the package:")
    for file in zipfile.ZipFile("lambda_simple_fix.zip", "r").namelist():
        print(f" - {file}")
    
    # Verify essential files are included
    zip_contents = zipfile.ZipFile("lambda_simple_fix.zip", "r").namelist()
    print("\nVerifying essential files:")
    for file in essential_files:
        if file in zip_contents:
            print(f"✓ {file}")
        else:
            print(f"✗ Missing: {file}")
    
    print("\nUpload lambda_simple_fix.zip to your AWS Lambda function")

if __name__ == "__main__":
    create_simple_fix()
