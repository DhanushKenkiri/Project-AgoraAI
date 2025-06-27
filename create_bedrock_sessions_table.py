"""
Script to create the DynamoDB table needed for Bedrock agent sessions
"""

import boto3
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_bedrock_sessions_table")

# Table configuration
DEFAULT_TABLE_NAME = os.environ.get('BEDROCK_SESSIONS_TABLE', 'NFTBedrockSessions')

def create_bedrock_sessions_table(table_name=DEFAULT_TABLE_NAME, region=None):
    """
    Create the DynamoDB table for Bedrock agent sessions
    
    Args:
        table_name: Name of the table to create
        region: AWS region
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Use the provided region or default to AWS_REGION environment variable
    if not region:
        region = os.environ.get('AWS_REGION', 'ap-south-1')
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Check if table already exists
        try:
            dynamodb.describe_table(TableName=table_name)
            logger.info(f"Table {table_name} already exists")
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            logger.info(f"Table {table_name} does not exist, creating...")
        
        # Create the DynamoDB table
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'session_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'session_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            TimeToLiveSpecification={
                'AttributeName': 'expiration',
                'Enabled': True
            }
        )
        
        # Wait for table to be created
        logger.info(f"Waiting for table {table_name} to be created...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        logger.info(f"Table {table_name} created successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error creating DynamoDB table: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Get table name from command line argument or use default
    table_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TABLE_NAME
    
    # Get region from command line argument or use default
    region = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Create the table
    success = create_bedrock_sessions_table(table_name, region)
    
    # Exit with success or failure code
    sys.exit(0 if success else 1)
