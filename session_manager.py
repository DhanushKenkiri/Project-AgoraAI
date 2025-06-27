"""
Session Manager for AWS Bedrock Agents

This module provides functions for storing and retrieving user session data
from DynamoDB, enabling persistent information across conversations.
"""

import boto3
import os
import json
import uuid
import time
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("session_manager")

# Default table name from environment variable
DEFAULT_SESSION_TABLE = os.environ.get('BEDROCK_SESSIONS_TABLE', 'NFTBedrockSessions')

def store_user_data(session_id, user_id=None, data=None):
    """
    Store user data in DynamoDB session table
    
    Args:
        session_id: The Bedrock agent session ID
        user_id: Optional user identifier
        data: Dictionary of data to store
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not session_id:
        logger.error("Session ID is required")
        return False
        
    if not data:
        logger.warning("No data provided to store")
        return False
        
    try:
        # Get region name from environment
        region_name = os.environ.get('AWS_REGION')
        
        # For local testing without AWS credentials
        if 'AWS_ENDPOINT_URL' in os.environ:
            # Use local DynamoDB
            dynamodb = boto3.resource(
                'dynamodb', 
                endpoint_url=os.environ['AWS_ENDPOINT_URL'],
                region_name=region_name or 'us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        elif not region_name:
            # For testing without actual DynamoDB
            logger.warning("No AWS region specified, using mock storage")
            # Store in memory for testing
            global _mock_session_data
            if not hasattr(store_user_data, '_mock_session_data'):
                store_user_data._mock_session_data = {}
                
            # Store in mock data
            store_user_data._mock_session_data[session_id] = {
                'session_id': session_id,
                'timestamp': int(time.time()),
                'expiration': int(time.time()) + (30 * 24 * 60 * 60),
                'data': data,
                'user_id': user_id
            }
            logger.info(f"Stored session data in mock storage for session {session_id}")
            return True
        else:
            # Use actual DynamoDB in AWS
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            
        table = dynamodb.Table(DEFAULT_SESSION_TABLE)
        
        # Current timestamp
        current_time = int(time.time())
        
        # Expiration time (30 days from now)
        expiration_time = current_time + (30 * 24 * 60 * 60)
        
        # Create or update the session item
        item = {
            'session_id': session_id,
            'timestamp': current_time,
            'expiration': expiration_time,
            'data': data
        }
        
        # Add user ID if provided
        if user_id:
            item['user_id'] = user_id
            
        # Store in DynamoDB
        table.put_item(Item=item)
        logger.info(f"Stored session data for session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing session data: {str(e)}")
        return False

def get_user_data(session_id, user_id=None):
    """
    Retrieve user data from DynamoDB session table
    
    Args:
        session_id: The Bedrock agent session ID
        user_id: Optional user identifier
        
    Returns:
        dict: User data if found, None otherwise
    """
    if not session_id:
        logger.error("Session ID is required")
        return None
        
    try:
        # Get region name from environment
        region_name = os.environ.get('AWS_REGION')
        
        # For local testing without AWS credentials
        if 'AWS_ENDPOINT_URL' in os.environ:
            # Use local DynamoDB
            dynamodb = boto3.resource(
                'dynamodb', 
                endpoint_url=os.environ['AWS_ENDPOINT_URL'],
                region_name=region_name or 'us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        elif not region_name:
            # For testing without actual DynamoDB
            logger.warning("No AWS region specified, using mock storage")
            # Check in-memory data for testing
            if not hasattr(store_user_data, '_mock_session_data'):
                store_user_data._mock_session_data = {}
                
            # Get from mock data
            item = store_user_data._mock_session_data.get(session_id)
            
            if not item:
                logger.info(f"No session found for ID {session_id} in mock storage")
                return None
                
            # Check if user ID matches if provided
            if user_id and item.get('user_id') != user_id:
                logger.warning(f"User ID mismatch for session {session_id}")
                return None
                
            # Check if session is expired
            if item.get('expiration', 0) < int(time.time()):
                logger.info(f"Session {session_id} is expired")
                return None
                
            # Return the data
            return item.get('data', {})
        else:
            # Use actual DynamoDB in AWS
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            table = dynamodb.Table(DEFAULT_SESSION_TABLE)
            
            # Get session from DynamoDB
            response = table.get_item(
                Key={'session_id': session_id}
            )
            
            # Check if item exists and has data
            if 'Item' in response:
                item = response['Item']
                
                # Check if user ID matches if provided
                if user_id and item.get('user_id') != user_id:
                    logger.warning(f"User ID mismatch for session {session_id}")
                    return None
                    
                # Check if session is expired
                if item.get('expiration', 0) < int(time.time()):
                    logger.info(f"Session {session_id} is expired")
                    return None
                    
                # Return the data
                return item.get('data', {})
            else:
                logger.info(f"No session found for ID {session_id}")
                return None
            
    except Exception as e:
        logger.error(f"Error retrieving session data: {str(e)}")
        return None

def store_wallet_address(session_id, wallet_address, user_id=None):
    """
    Store wallet address in the user's session
    
    Args:
        session_id: The Bedrock agent session ID
        wallet_address: Ethereum wallet address
        user_id: Optional user identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get existing data first
    existing_data = get_user_data(session_id, user_id) or {}
    
    # Add wallet address
    existing_data['wallet_address'] = wallet_address
    
    # Store back to DynamoDB
    return store_user_data(session_id, user_id, existing_data)

def get_wallet_address(session_id, user_id=None):
    """
    Get stored wallet address for the user's session
    
    Args:
        session_id: The Bedrock agent session ID
        user_id: Optional user identifier
        
    Returns:
        str: Wallet address if found, None otherwise
    """
    # Get user data
    user_data = get_user_data(session_id, user_id)
    
    # Return wallet address if found
    return user_data.get('wallet_address') if user_data else None

def create_dynamodb_table(table_name=DEFAULT_SESSION_TABLE, region=None):
    """
    Create DynamoDB table for session storage if it doesn't exist
    
    Args:
        table_name: Name of the table to create
        region: AWS region
        
    Returns:
        bool: True if successful or already exists, False otherwise
    """
    try:
        # Create boto3 client
        dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Check if table already exists
        try:
            dynamodb.describe_table(TableName=table_name)
            logger.info(f"Table {table_name} already exists")
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            # Table doesn't exist, create it
            logger.info(f"Creating table {table_name}...")
            
        # Create the table
        dynamodb.create_table(
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
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table creation
        logger.info(f"Waiting for table {table_name} to be created...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        logger.info(f"Table {table_name} created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating DynamoDB table: {str(e)}")
        return False
