"""
Deploy MCP Server to AWS Lambda with API Gateway

This script deploys the AWS MCP server to Lambda with API Gateway,
setting up all the necessary resources and permissions.
"""

import os
import json
import subprocess
import argparse
import shutil
import zipfile
import tempfile
import time

def run_command(command, cwd=None):
    """Run a command and return its output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()

def check_aws_cli():
    """Check if AWS CLI is installed and configured"""
    try:
        result = run_command(["aws", "--version"])
        if not result:
            print("Error: AWS CLI not installed or not in PATH")
            return False
        
        result = run_command(["aws", "sts", "get-caller-identity"])
        if not result:
            print("Error: AWS CLI not configured. Run 'aws configure'")
            return False
        
        print(f"AWS CLI is installed and configured: {result}")
        return True
    except Exception as e:
        print(f"Error checking AWS CLI: {str(e)}")
        return False

def create_deployment_package(output_path):
    """Create a deployment package for AWS Lambda"""
    print("Creating deployment package...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy required files
        files_to_include = [
            "aws_mcp_server.py",
            "mcp_server.py",
            "wallet_login.py",
            "nft_wallet.py",
            "lambda_handler.py",
            "x402_payment_handler.py",
            "bedrock_agent_adapter.py"
        ]
        
        directories_to_include = [
            "templates",
            "static"
        ]
        
        # Copy individual files
        for file in files_to_include:
            if os.path.exists(file):
                shutil.copy2(file, temp_dir)
                print(f"Copied {file}")
            else:
                print(f"Warning: {file} not found")
        
        # Copy directories
        for directory in directories_to_include:
            if os.path.exists(directory):
                dest_dir = os.path.join(temp_dir, directory)
                shutil.copytree(directory, dest_dir)
                print(f"Copied directory {directory}")
            else:
                print(f"Warning: directory {directory} not found")
          # Create lambda_function.py for AWS Lambda
        lambda_function_content = """
import os
import json
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lambda_function")

# Import the AWS MCP server
from aws_mcp_server import app

# Import Mangum for API Gateway integration
try:
    from mangum import Mangum
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "mangum", "-t", "."])
    from mangum import Mangum

# Create the handler for Lambda
handler = Mangum(app)

# Import Bedrock agent adapter
try:
    from bedrock_agent_adapter import bedrock_lambda_handler, lambda_handler as combined_lambda_handler
    logger.info("Bedrock agent adapter loaded successfully")
except ImportError:
    logger.warning("Bedrock agent adapter not available")
    combined_lambda_handler = None
    bedrock_lambda_handler = None

def aws_lambda_handler(event, context):
    # This is the entry point for AWS Lambda via API Gateway
    return handler(event, context)

def lambda_handler(event, context):
    """
    Main Lambda handler that supports multiple integration types:
    - AWS API Gateway requests
    - AWS Bedrock agent requests
    - Direct Lambda invocations
    """
    try:
        # Log the incoming event type (but not the full event for privacy/security)
        logger.info(f"Lambda invoked with event type: {type(event)}")
        
        # Detect if this is a Bedrock agent request
        is_bedrock_request = (
            isinstance(event, dict) and (
                "requestBody" in event or
                "messageVersion" in event or
                ("rawPath" in event and event.get("rawPath", "") == "/validate")
            )
        )
        
        # Check if this is an API Gateway request
        is_api_gateway = (
            isinstance(event, dict) and (
                "httpMethod" in event or
                "requestContext" in event and "http" in event.get("requestContext", {})
            )
        )
        
        if is_bedrock_request and combined_lambda_handler:
            # Use the combined handler that supports Bedrock
            logger.info("Handling as Bedrock agent request")
            return combined_lambda_handler(event, context)
        elif is_api_gateway:
            # Use Mangum handler for API Gateway requests
            logger.info("Handling as API Gateway request")
            return aws_lambda_handler(event, context)
        else:
            # Direct Lambda invocation - use the regular handler
            logger.info("Handling as direct Lambda invocation")
            from lambda_handler import lambda_handler as base_lambda_handler
            return base_lambda_handler(event, context)
            
    except Exception as e:
        logger.error(f"Unhandled exception in lambda_handler: {e}")
        # Return a proper API Gateway response
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Unhandled exception: {str(e)}"
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
"""
        
        with open(os.path.join(temp_dir, "lambda_function.py"), "w") as f:
            f.write(lambda_function_content)
            print("Created lambda_function.py")
        
        # Create requirements.txt
        requirements_content = """
fastapi==0.104.1
uvicorn==0.24.0
mangum==0.17.0
pydantic==2.4.2
jinja2==3.1.2
boto3==1.29.0
"""
        
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write(requirements_content)
            print("Created requirements.txt")
        
        # Install dependencies
        print("Installing dependencies...")
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt", "-t", temp_dir],
            check=True
        )
        
        # Create the zip file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Zip all files in the temporary directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    
        print(f"Deployment package created: {output_path}")
        return True

def create_lambda_function(function_name, zip_file, role_arn=None, region=None):
    """Create or update an AWS Lambda function"""
    print(f"Creating/updating Lambda function: {function_name}")
    
    # Create IAM role if not provided
    if not role_arn:
        role_name = f"{function_name}-role"
        print(f"Creating IAM role: {role_name}")
        
        # Create trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            json.dump(trust_policy, temp)
            temp_name = temp.name
        
        # Create role
        result = run_command([
            "aws", "iam", "create-role",
            "--role-name", role_name,
            "--assume-role-policy-document", f"file://{temp_name}"
        ])
        
        if not result:
            print("Error creating IAM role")
            os.unlink(temp_name)
            return False
        
        role_data = json.loads(result)
        role_arn = role_data["Role"]["Arn"]
        
        # Attach policies
        run_command([
            "aws", "iam", "attach-role-policy",
            "--role-name", role_name,
            "--policy-arn", "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        ])
        
        run_command([
            "aws", "iam", "attach-role-policy",
            "--role-name", role_name,
            "--policy-arn", "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
        ])
        
        # Wait for role to propagate
        print("Waiting for IAM role to propagate...")
        time.sleep(10)
        os.unlink(temp_name)
    
    # Check if function exists
    check_result = run_command([
        "aws", "lambda", "get-function",
        "--function-name", function_name
    ])
    
    if check_result:
        # Update existing function
        print("Function exists, updating...")
        result = run_command([
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", f"fileb://{zip_file}"
        ])
    else:
        # Create new function
        print("Creating new function...")
        region_param = ["--region", region] if region else []
        result = run_command([
            "aws", "lambda", "create-function",
            "--function-name", function_name,
            "--runtime", "python3.9",
            "--handler", "lambda_function.aws_lambda_handler",
            "--role", role_arn,
            "--zip-file", f"fileb://{zip_file}",
            "--timeout", "30",
            "--memory-size", "256",
            *region_param
        ])
    
    if not result:
        print("Error creating/updating Lambda function")
        return False
    
    print("Lambda function created/updated successfully")
    return True

def create_api_gateway(function_name, api_name=None, region=None):
    """Create an API Gateway for the Lambda function"""
    if not api_name:
        api_name = f"{function_name}-api"
    
    print(f"Creating API Gateway: {api_name}")
    
    # Create API
    region_param = ["--region", region] if region else []
    result = run_command([
        "aws", "apigatewayv2", "create-api",
        "--name", api_name,
        "--protocol-type", "HTTP",
        *region_param
    ])
    
    if not result:
        print("Error creating API Gateway")
        return False
    
    api_data = json.loads(result)
    api_id = api_data["ApiId"]
    
    # Get Lambda function ARN
    function_result = run_command([
        "aws", "lambda", "get-function",
        "--function-name", function_name,
        *region_param
    ])
    
    if not function_result:
        print("Error retrieving Lambda function")
        return False
    
    function_data = json.loads(function_result)
    function_arn = function_data["Configuration"]["FunctionArn"]
    
    # Create integration
    integration_result = run_command([
        "aws", "apigatewayv2", "create-integration",
        "--api-id", api_id,
        "--integration-type", "AWS_PROXY",
        "--integration-uri", function_arn,
        "--payload-format-version", "2.0",
        *region_param
    ])
    
    if not integration_result:
        print("Error creating API Gateway integration")
        return False
    
    integration_data = json.loads(integration_result)
    integration_id = integration_data["IntegrationId"]
    
    # Create route
    route_result = run_command([
        "aws", "apigatewayv2", "create-route",
        "--api-id", api_id,
        "--route-key", "ANY /{proxy+}",
        "--target", f"integrations/{integration_id}",
        *region_param
    ])
    
    if not route_result:
        print("Error creating API Gateway route")
        return False
    
    # Add permission for API Gateway to invoke Lambda
    account_id = run_command([
        "aws", "sts", "get-caller-identity",
        "--query", "Account",
        "--output", "text"
    ])
    
    if not account_id:
        print("Error getting AWS account ID")
        return False
    
    # Use the current region if not specified
    if not region:
        region = run_command([
            "aws", "configure", "get", "region"
        ])
    
    # Add permission
    permission_result = run_command([
        "aws", "lambda", "add-permission",
        "--function-name", function_name,
        "--statement-id", f"apigateway-{api_id}",
        "--action", "lambda:InvokeFunction",
        "--principal", "apigateway.amazonaws.com",
        "--source-arn", f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*",
        *region_param
    ])
    
    # Create deployment and stage
    deploy_result = run_command([
        "aws", "apigatewayv2", "create-deployment",
        "--api-id", api_id,
        *region_param
    ])
    
    if not deploy_result:
        print("Error creating API Gateway deployment")
        return False
    
    deployment_data = json.loads(deploy_result)
    deployment_id = deployment_data["DeploymentId"]
    
    stage_result = run_command([
        "aws", "apigatewayv2", "create-stage",
        "--api-id", api_id,
        "--deployment-id", deployment_id,
        "--stage-name", "prod",
        "--auto-deploy", "true",
        *region_param
    ])
    
    if not stage_result:
        print("Error creating API Gateway stage")
        return False
    
    # Get API endpoint
    api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod"
    print(f"API Gateway created: {api_url}")
    
    return api_url

def create_dynamodb_tables(prefix="NFT", region=None):
    """Create the required DynamoDB tables"""
    print("Creating DynamoDB tables...")
    
    tables = [
        {
            "name": f"{prefix}PaymentTransactions",
            "key": "transaction_id"
        },
        {
            "name": f"{prefix}WalletSessions",
            "key": "session_id"
        }
    ]
    
    region_param = ["--region", region] if region else []
    
    for table in tables:
        # Check if table exists
        check_result = run_command([
            "aws", "dynamodb", "describe-table",
            "--table-name", table["name"],
            *region_param
        ])
        
        if check_result:
            print(f"Table {table['name']} already exists")
            continue
        
        print(f"Creating table {table['name']}...")
        result = run_command([
            "aws", "dynamodb", "create-table",
            "--table-name", table["name"],
            "--attribute-definitions", f'AttributeName={table["key"]},AttributeType=S',
            "--key-schema", f'AttributeName={table["key"]},KeyType=HASH',
            "--billing-mode", "PAY_PER_REQUEST",
            *region_param
        ])
        
        if not result:
            print(f"Error creating table {table['name']}")
        else:
            print(f"Table {table['name']} created successfully")
    
    return True

def create_env_vars(function_name, env_vars, region=None):
    """Set environment variables for the Lambda function"""
    print(f"Setting environment variables for {function_name}...")
    
    # Build environment JSON
    env_json = {"Variables": env_vars}
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
        json.dump(env_json, temp)
        temp_name = temp.name
    
    # Update Lambda configuration
    region_param = ["--region", region] if region else []
    result = run_command([
        "aws", "lambda", "update-function-configuration",
        "--function-name", function_name,
        "--environment", f"file://{temp_name}",
        *region_param
    ])
    
    os.unlink(temp_name)
    
    if not result:
        print("Error setting environment variables")
        return False
    
    print("Environment variables set successfully")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Deploy MCP server to AWS Lambda")
    parser.add_argument("--name", default="nft-payment-mcp", help="Lambda function name")
    parser.add_argument("--role", help="IAM role ARN (optional)")
    parser.add_argument("--region", help="AWS region (default: configured region)")
    parser.add_argument("--prefix", default="NFT", help="Prefix for DynamoDB tables")
    parser.add_argument("--output", default="mcp_deployment.zip", help="Output zip file")
    args = parser.parse_args()
    
    # Check AWS CLI
    if not check_aws_cli():
        return 1
    
    # Create deployment package
    if not create_deployment_package(args.output):
        return 1
    
    # Create DynamoDB tables
    if not create_dynamodb_tables(args.prefix, args.region):
        return 1
    
    # Create Lambda function
    if not create_lambda_function(args.name, args.output, args.role, args.region):
        return 1
    
    # Get current Lambda environment variables to preserve existing ones
    region_param = ["--region", args.region] if args.region else []
    function_result = run_command([
        "aws", "lambda", "get-function",
        "--function-name", args.name,
        *region_param
    ])
    
    existing_env_vars = {}
    if function_result:
        function_data = json.loads(function_result)
        existing_env_vars = function_data.get("Configuration", {}).get("Environment", {}).get("Variables", {})
    
    # Set environment variables
    env_vars = {
        **existing_env_vars,
        "WALLET_SESSIONS_TABLE": f"{args.prefix}WalletSessions",
        "TRANSACTION_TABLE_NAME": f"{args.prefix}PaymentTransactions",
        "ENVIRONMENT": "production",
    }
    
    if not create_env_vars(args.name, env_vars, args.region):
        return 1
    
    # Create API Gateway
    api_url = create_api_gateway(args.name, None, args.region)
    if not api_url:
        return 1
    
    # Update environment variable with the API URL
    env_vars["SERVER_URL"] = api_url
    if not create_env_vars(args.name, env_vars, args.region):
        return 1
    
    print(f"\nDeployment completed successfully!")
    print(f"MCP Server API URL: {api_url}")
    print(f"Try accessing: {api_url}/aws/health")
    return 0

if __name__ == "__main__":
    exit(main())
