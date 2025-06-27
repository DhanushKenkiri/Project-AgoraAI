"""
AWS Bedrock Agent Integration for Rich Media and Wallet Management

This module integrates AWS Bedrock Agents with rich media support (images)
and persistent wallet sessions for a complete NFT management system.
"""

import json
import os
import uuid
import base64
import logging
from typing import Dict, Any, Optional, List, Tuple
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bedrock_integration")

# Import session manager for persistent wallet storage
try:
    from session_manager import get_user_data, store_user_data, get_wallet_address, store_wallet_address
except ImportError:
    logger.warning("Could not import session_manager module, using mocks")
    # Simple in-memory storage for testing
    _session_data = {}
    _wallet_data = {}
    
    def get_user_data(session_id, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        return _session_data.get(key, {})
    
    def store_user_data(session_id, data, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        _session_data[key] = data
        return True
        
    def get_wallet_address(session_id, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        return _wallet_data.get(key)
    
    def store_wallet_address(session_id, wallet_address, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        _wallet_data[key] = wallet_address
        return True

# Try to import image processor
try:
    from image_processor import process_image_upload, get_nft_images, analyze_image
except ImportError:
    logger.warning("Could not import image_processor module, using mocks")
    
    # Mock image processing functions
    def process_image_upload(image_data, session_id, user_id=None):
        return {
            'success': True,
            'image_id': str(uuid.uuid4()),
            'image_url': f"https://example.com/mock-image-{uuid.uuid4()}.jpg",
            'analysis': {'labels': ['NFT', 'Art', 'Digital']}
        }
    
    def get_nft_images(contract_address, token_ids=None):
        return {
            'success': True,
            'images': [
                {
                    'token_id': '1',
                    'image_url': f"https://example.com/nft-1.jpg",
                    'metadata': {'name': 'Mock NFT 1'}
                }
            ]
        }
        
    def analyze_image(image_url, session_id=None):
        return {
            'success': True,
            'analysis': {'labels': ['NFT', 'Art', 'Digital']}
        }

# Try to import wallet login module
try:
    from enhanced_wallet_login import handle_wallet_connection, check_wallet_status, disconnect_wallet
except ImportError:
    logger.warning("Could not import enhanced_wallet_login module, using mocks")
    
    # Mock wallet functions
    def handle_wallet_connection(event):
        try:
            body = json.loads(event.get('body', '{}'))
            wallet_address = body.get('wallet_address', '')
            session_id = event.get('headers', {}).get('x-session-id', str(uuid.uuid4()))
            
            # Store wallet in session
            store_wallet_address(session_id, wallet_address)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,x-session-id'
                },
                'body': json.dumps({
                    'success': True,
                    'session_id': session_id,
                    'wallet_address': wallet_address,
                    'message': 'Mock wallet login successful'
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': str(e)})
            }
    
    def check_wallet_status(event):
        session_id = event.get('headers', {}).get('x-session-id', '')
        wallet_address = get_wallet_address(session_id)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'connected': bool(wallet_address),
                'wallet_address': wallet_address
            })
        }
    
    def disconnect_wallet(event):
        session_id = event.get('headers', {}).get('x-session-id', '')
        store_wallet_address(session_id, None)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'message': 'Wallet disconnected'
            })
        }

# Initialize AWS clients if needed
try:
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
except Exception as e:
    logger.warning(f"Error initializing S3 client: {e}")
    s3_client = None

# S3 bucket configuration
S3_BUCKET_NAME = os.environ.get('IMAGE_BUCKET', 'nft-image-analysis-bucket')

def handle_image_upload_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle image upload requests
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    try:
        # Extract session ID from headers or query parameters
        session_id = event.get('headers', {}).get('x-session-id', None)
        if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
            session_id = event['queryStringParameters'].get('session_id')
        
        # Default to a new UUID if no session ID is provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Extract user ID if available
        user_id = None
        if 'queryStringParameters' in event and event['queryStringParameters']:
            user_id = event['queryStringParameters'].get('user_id')
        
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image', '')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'No image data provided'})
            }
        
        # Process the image
        result = process_image_upload(image_data, session_id, user_id)
        
        # Store image reference in session data
        session_data = get_user_data(session_id, user_id) or {}
        if 'images' not in session_data:
            session_data['images'] = []
        
        # Add this image to the session's image history
        session_data['images'].append({
            'image_id': result.get('image_id'),
            'image_url': result.get('image_url'),
            'timestamp': result.get('timestamp', int(time.time())),
            'analysis': result.get('analysis', {})
        })
        
        # Update session data
        store_user_data(session_id, session_data, user_id)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'session_id': session_id,
                'image_id': result.get('image_id'),
                'image_url': result.get('image_url'),
                'analysis': result.get('analysis', {})
            })
        }
    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def handle_nft_image_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle NFT image retrieval requests
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response with NFT images
    """
    try:
        # Parse parameters
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Extract required parameters
        contract_address = query_params.get('contractAddress')
        token_ids = query_params.get('tokenIds')
        
        if not contract_address:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Contract address is required'})
            }
        
        # Parse token IDs if provided
        token_id_list = None
        if token_ids:
            token_id_list = token_ids.split(',')
        
        # Get NFT images
        result = get_nft_images(contract_address, token_id_list)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'contract_address': contract_address,
                'images': result.get('images', [])
            })
        }
    except Exception as e:
        logger.error(f"Error retrieving NFT images: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def handle_wallet_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle wallet-related requests (login, status, disconnect)
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    if path == '/wallet/connect' and method == 'POST':
        return handle_wallet_connection(event)
    elif path == '/wallet/status':
        return check_wallet_status(event)
    elif path == '/wallet/disconnect':
        return disconnect_wallet(event)
    else:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': f"Invalid wallet endpoint: {path}"})
        }

def handle_bedrock_image_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle image requests from Bedrock agent
    
    Args:
        event: The Bedrock agent event
        
    Returns:
        Response for Bedrock agent
    """
    try:
        # Extract parameters from Bedrock request
        request = event.get('requestBody', {})
        parameters = request.get('parameters', [])
        
        # Extract parameters
        param_dict = {}
        for param in parameters:
            name = param.get('name', '')
            value = param.get('value', '')
            param_dict[name] = value
            
        # Get contract address and token ID
        contract_address = param_dict.get('contract_address')
        token_id = param_dict.get('token_id')
        
        # Extract session info
        session_id = event.get('sessionId')
        
        if not contract_address:
            return {
                'success': False,
                'error': 'Contract address is required',
                'message': 'Please provide a valid NFT contract address'
            }
            
        # Get a single token or the first from the collection
        token_ids = [token_id] if token_id else None
        
        # Get NFT images
        result = get_nft_images(contract_address, token_ids)
        
        # Format response for Bedrock
        response = {
            'success': True,
            'contract_address': contract_address,
            'images': result.get('images', []),
            'message': f"Found {len(result.get('images', []))} NFT images"
        }
        
        return response
    except Exception as e:
        logger.error(f"Error handling Bedrock image request: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve NFT images'
        }

def bedrock_format_rich_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a rich response for Bedrock agent with text and image links
    
    Args:
        data: The data to format
        
    Returns:
        Formatted response with text and image links
    """
    # Extract image URLs if present
    images = data.get('images', [])
    image_urls = []
    
    for image in images:
        if 'image_url' in image:
            image_urls.append(image['image_url'])
    
    # Generate text description
    text_content = data.get('message', '')
    if not text_content:
        if data.get('success'):
            text_content = f"Found {len(images)} NFT images"
        else:
            text_content = data.get('error', 'An error occurred')
    
    # Formatted response with images
    response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "NFTImageActions",
            "apiPath": "/nft/images",
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": json.dumps({
                    "text": text_content,
                    "images": image_urls,
                    "data": data
                })
            }
        }
    }
    
    return response
"""
