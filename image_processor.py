"""
Image processing module for NFT analysis and display

This module handles image uploads, processing, and retrieval for NFT analysis
"""
import os
import json
import uuid
import base64
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("image_processor")

# Initialize AWS clients
try:
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
    rekognition_client = boto3.client('rekognition', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
except Exception as e:
    logger.warning(f"Error initializing AWS clients: {e}")
    s3_client = None
    rekognition_client = None

# Get bucket name from environment variables or use default
S3_BUCKET_NAME = os.environ.get('IMAGE_BUCKET', 'nft-image-analysis-bucket')
IMAGE_EXPIRATION_DAYS = int(os.environ.get('IMAGE_EXPIRATION_DAYS', '30'))

def process_image_upload(image_data: str, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process an uploaded image
    
    Args:
        image_data: Base64 encoded image data
        session_id: User session ID
        user_id: Optional user ID
        
    Returns:
        Dict with processing results
    """
    try:
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())
        
        # Decode the base64 image
        if image_data.startswith('data:image'):
            # Extract the actual base64 content after the content type declaration
            _, encoded = image_data.split(',', 1)
            image_content = base64.b64decode(encoded)
        else:
            # Assuming it's just base64 without content type prefix
            image_content = base64.b64decode(image_data)
        
        # Generate paths
        image_key = f"uploads/{session_id}/{image_id}.jpg"
        
        # Upload to S3
        if s3_client:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=image_key,
                Body=image_content,
                ContentType='image/jpeg',
                Metadata={
                    'session_id': session_id,
                    'user_id': user_id or 'anonymous',
                    'upload_date': datetime.now().isoformat()
                }
            )
            
            # Generate a presigned URL that expires after a set time
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET_NAME, 'Key': image_key},
                ExpiresIn=3600*24*IMAGE_EXPIRATION_DAYS  # URL expires in 30 days
            )
            
            # Analyze the image if Rekognition is available
            analysis = {}
            if rekognition_client:
                try:
                    response = rekognition_client.detect_labels(
                        Image={'S3Object': {'Bucket': S3_BUCKET_NAME, 'Name': image_key}},
                        MaxLabels=10
                    )
                    labels = [label['Name'] for label in response.get('Labels', [])]
                    analysis['labels'] = labels
                except Exception as e:
                    logger.error(f"Error analyzing image with Rekognition: {e}")
            
            return {
                'success': True,
                'image_id': image_id,
                'image_url': url,
                'analysis': analysis
            }
        else:
            logger.error("S3 client not available for image upload")
            return {
                'success': False,
                'error': 'Image storage service not available'
            }
    
    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def retrieve_nft_images(wallet_address: str, collection: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve NFT images for a wallet
    
    Args:
        wallet_address: The wallet address to retrieve NFTs for
        collection: Optional collection to filter by
        
    Returns:
        Dict containing NFT image information
    """
    try:
        # First try to get the NFTs using the existing function
        from nft_wallet import get_wallet_nfts
        
        nft_data = get_wallet_nfts(wallet_address)
        
        # Add image URLs to the NFT data
        nfts_with_images = []
        
        if nft_data.get('success') and nft_data.get('nfts'):
            for nft in nft_data.get('nfts', []):
                # Check if NFT already has an image_url
                if 'image_url' in nft and nft['image_url']:
                    nfts_with_images.append(nft)
                    continue
                
                # Try to get image URL from metadata
                if 'metadata_url' in nft:
                    # Here you would fetch the metadata and extract the image URL
                    # For now, we'll assume a mock implementation
                    nft['image_url'] = f"https://example.com/nft-image/{nft.get('id')}.png"
                
                # Add this NFT to the result
                nfts_with_images.append(nft)
            
            # Filter by collection if specified
            if collection:
                nfts_with_images = [nft for nft in nfts_with_images if nft.get('collection', '').lower() == collection.lower()]
            
            return {
                'success': True,
                'nfts': nfts_with_images,
                'wallet_address': wallet_address
            }
        else:
            return nft_data  # Return original response if not successful
    
    except Exception as e:
        logger.error(f"Error retrieving NFT images: {e}")
        return {
            'success': False,
            'error': str(e),
            'nfts': []
        }

def format_rich_response(content: str, images: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Format a response with rich content including images
    
    Args:
        content: The text content
        images: List of image dictionaries with 'url' and 'description'
        
    Returns:
        Formatted response for the frontend
    """
    response = {
        'content': content,
        'type': 'text'
    }
    
    if images and len(images) > 0:
        response['type'] = 'rich'
        response['images'] = images
    
    return response

def handle_image_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle image-related requests from API Gateway
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    
    # Extract session ID from headers or query parameters
    session_id = event.get('headers', {}).get('x-session-id', None)
    if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('session_id', str(uuid.uuid4()))
    
    # Default to a new UUID if no session ID is provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Handle image upload
    if method == 'POST' and path == '/image/upload':
        try:
            # Parse the request body
            body = json.loads(event.get('body', '{}'))
            image_data = body.get('image', '')
            user_id = body.get('user_id', None)
            
            if not image_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'No image data provided'
                    })
                }
            
            # Process the image
            result = process_image_upload(image_data, session_id, user_id)
            
            return {
                'statusCode': 200 if result.get('success') else 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(result)
            }
        except Exception as e:
            logger.error(f"Error handling image upload: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }
    
    # Handle NFT image retrieval
    elif method == 'GET' and path == '/wallet/nft-images':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            wallet_address = params.get('wallet_address', '')
            collection = params.get('collection', None)
            
            if not wallet_address:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Wallet address is required'
                    })
                }
            
            # Retrieve NFT images
            result = retrieve_nft_images(wallet_address, collection)
            
            return {
                'statusCode': 200 if result.get('success') else 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(result)
            }
        except Exception as e:
            logger.error(f"Error handling NFT image retrieval: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }
    
    # Handle unknown requests
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Endpoint not found'
            })
        }
