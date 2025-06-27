"""
Enhanced image processor for NFT analysis and retrieval

This module handles image uploads, NFT image retrieval, and image analysis
"""
import os
import json
import uuid
import base64
import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple
import boto3
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nft_image_processor")

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

# Try to import API modules
try:
    from apis.opensea_api import fetch_opensea_data
    from apis.reservoir_api import fetch_collection_data
    from apis.nftscan_api import fetch_nftscan_data
    from apis.alchemy_api import fetch_alchemy_data
    from apis.moralis_api import fetch_moralis_data
except ImportError:
    logger.warning("Could not import NFT API modules, using mock data")
    
    # Mock NFT API functions
    def fetch_opensea_data(contract_address, token_id=None):
        return {'success': True, 'data': {'image_url': f"https://example.com/nft-{token_id or 1}.jpg"}}
    
    def fetch_collection_data(contract_address):
        return {'success': True, 'collection': {'image_url': f"https://example.com/collection-{contract_address}.jpg"}}
    
    def fetch_nftscan_data(contract_address, token_id=None):
        return {'success': True, 'data': {'image': f"https://example.com/nft-{token_id or 1}.jpg"}}
    
    def fetch_alchemy_data(contract_address, token_id=None):
        return {'success': True, 'metadata': {'image': f"https://example.com/nft-{token_id or 1}.jpg"}}
    
    def fetch_moralis_data(contract_address, token_id=None):
        return {'success': True, 'metadata': {'image': f"https://example.com/nft-{token_id or 1}.jpg"}}

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
            
            # Return the result with timestamp
            return {
                'success': True,
                'image_id': image_id,
                'image_url': url,
                'analysis': analysis,
                'timestamp': int(time.time())
            }
        else:
            # Mock mode without S3 access
            logger.warning("No S3 client available, using mock URL")
            return {
                'success': True,
                'image_id': image_id,
                'image_url': f"https://example.com/mock-image-{image_id}.jpg",
                'analysis': {'labels': ['NFT', 'Art', 'Digital']},
                'timestamp': int(time.time())
            }
            
    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_nft_images(contract_address: str, token_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get NFT images from various APIs
    
    Args:
        contract_address: NFT contract address
        token_ids: Optional list of token IDs
        
    Returns:
        Dict with NFT images
    """
    if not contract_address:
        return {'success': False, 'error': 'Contract address is required'}
    
    # If token_ids is None or empty, we'll try to get collection data
    collection_mode = not token_ids
    
    results = []
    errors = []
    sources_used = []
    
    try:
        # Try OpenSea API first
        try:
            opensea_results = []
            
            if collection_mode:
                # Get collection data
                opensea_data = fetch_opensea_data(contract_address)
                if opensea_data.get('success'):
                    sources_used.append('OpenSea')
                    collection = opensea_data.get('data', {})
                    
                    # Extract collection image
                    if 'image_url' in collection or 'image' in collection:
                        image_url = collection.get('image_url') or collection.get('image')
                        opensea_results.append({
                            'token_id': 'collection',
                            'image_url': image_url,
                            'metadata': {
                                'name': collection.get('name', 'Collection'),
                                'description': collection.get('description', '')
                            }
                        })
            else:
                # Get specific token data
                for token_id in token_ids:
                    opensea_data = fetch_opensea_data(contract_address, token_id)
                    if opensea_data.get('success'):
                        sources_used.append('OpenSea')
                        token_data = opensea_data.get('data', {})
                        
                        # Extract token image
                        if 'image_url' in token_data or 'image' in token_data:
                            image_url = token_data.get('image_url') or token_data.get('image')
                            opensea_results.append({
                                'token_id': token_id,
                                'image_url': image_url,
                                'metadata': {
                                    'name': token_data.get('name', f"Token #{token_id}"),
                                    'description': token_data.get('description', '')
                                }
                            })
            
            # Add OpenSea results if found
            results.extend(opensea_results)
        except Exception as e:
            errors.append(f"OpenSea API error: {str(e)}")
        
        # Try NFTScan API next if we don't have results yet
        if not results:
            try:
                nftscan_results = []
                
                if collection_mode:
                    # Get collection data
                    nftscan_data = fetch_nftscan_data(contract_address)
                    if nftscan_data.get('success'):
                        sources_used.append('NFTScan')
                        collection = nftscan_data.get('data', {})
                        
                        # Extract collection image
                        if 'image' in collection or 'logo' in collection:
                            image_url = collection.get('image') or collection.get('logo')
                            nftscan_results.append({
                                'token_id': 'collection',
                                'image_url': image_url,
                                'metadata': {
                                    'name': collection.get('name', 'Collection'),
                                    'description': collection.get('description', '')
                                }
                            })
                else:
                    # Get specific token data
                    for token_id in token_ids:
                        nftscan_data = fetch_nftscan_data(contract_address, token_id)
                        if nftscan_data.get('success'):
                            sources_used.append('NFTScan')
                            token_data = nftscan_data.get('data', {})
                            
                            # Extract token image
                            if 'image' in token_data:
                                image_url = token_data.get('image')
                                nftscan_results.append({
                                    'token_id': token_id,
                                    'image_url': image_url,
                                    'metadata': {
                                        'name': token_data.get('name', f"Token #{token_id}"),
                                        'description': token_data.get('description', '')
                                    }
                                })
                
                # Add NFTScan results if found
                results.extend(nftscan_results)
            except Exception as e:
                errors.append(f"NFTScan API error: {str(e)}")
        
        # Try Alchemy API if still no results
        if not results:
            try:
                alchemy_results = []
                
                if collection_mode:
                    # Not ideal to get collection info from Alchemy without a token ID
                    # Let's try with token ID #1
                    alchemy_data = fetch_alchemy_data(contract_address, "1")
                else:
                    # Get specific token data
                    for token_id in token_ids:
                        alchemy_data = fetch_alchemy_data(contract_address, token_id)
                        if alchemy_data.get('success'):
                            sources_used.append('Alchemy')
                            metadata = alchemy_data.get('metadata', {})
                            
                            # Extract token image
                            if 'image' in metadata:
                                image_url = metadata.get('image')
                                
                                # Fix IPFS URLs
                                if image_url.startswith('ipfs://'):
                                    image_url = image_url.replace('ipfs://', 'https://ipfs.io/ipfs/')
                                
                                alchemy_results.append({
                                    'token_id': token_id,
                                    'image_url': image_url,
                                    'metadata': {
                                        'name': metadata.get('name', f"Token #{token_id}"),
                                        'description': metadata.get('description', '')
                                    }
                                })
                
                # Add Alchemy results if found
                results.extend(alchemy_results)
            except Exception as e:
                errors.append(f"Alchemy API error: {str(e)}")
                
        # Try Moralis as a last resort
        if not results:
            try:
                moralis_results = []
                
                if collection_mode:
                    # Not ideal to get collection info from Moralis without a token ID
                    # Let's try with token ID #0
                    moralis_data = fetch_moralis_data(contract_address, "0")
                else:
                    # Get specific token data
                    for token_id in token_ids:
                        moralis_data = fetch_moralis_data(contract_address, token_id)
                        if moralis_data.get('success'):
                            sources_used.append('Moralis')
                            metadata = moralis_data.get('metadata', {})
                            
                            # Extract token image
                            if 'image' in metadata:
                                image_url = metadata.get('image')
                                
                                # Fix IPFS URLs
                                if image_url.startswith('ipfs://'):
                                    image_url = image_url.replace('ipfs://', 'https://ipfs.io/ipfs/')
                                
                                moralis_results.append({
                                    'token_id': token_id,
                                    'image_url': image_url,
                                    'metadata': {
                                        'name': metadata.get('name', f"Token #{token_id}"),
                                        'description': metadata.get('description', '')
                                    }
                                })
                
                # Add Moralis results if found
                results.extend(moralis_results)
            except Exception as e:
                errors.append(f"Moralis API error: {str(e)}")
        
        # If we still don't have results, try Reservoir API for collection data
        if not results and collection_mode:
            try:
                reservoir_data = fetch_collection_data(contract_address)
                if reservoir_data.get('success'):
                    sources_used.append('Reservoir')
                    collection = reservoir_data.get('collection', {})
                    
                    # Extract collection image
                    if 'image' in collection or 'imageUrl' in collection:
                        image_url = collection.get('image') or collection.get('imageUrl')
                        results.append({
                            'token_id': 'collection',
                            'image_url': image_url,
                            'metadata': {
                                'name': collection.get('name', 'Collection'),
                                'description': collection.get('description', '')
                            }
                        })
            except Exception as e:
                errors.append(f"Reservoir API error: {str(e)}")
        
        # Return the results
        return {
            'success': bool(results),  # True if we have any results
            'images': results,
            'errors': errors if errors else None,
            'sources': list(set(sources_used))
        }
    except Exception as e:
        logger.error(f"Error retrieving NFT images: {e}")
        return {
            'success': False,
            'error': str(e),
            'errors': errors
        }

def analyze_image(image_url: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze an image using AWS Rekognition
    
    Args:
        image_url: URL of the image to analyze
        session_id: Optional session ID
        
    Returns:
        Dict with analysis results
    """
    if not rekognition_client:
        return {
            'success': False,
            'error': 'Rekognition client not available'
        }
    
    try:
        # Generate a unique ID for tracking
        analysis_id = str(uuid.uuid4())
        
        # If the URL is from our S3 bucket, we can analyze it directly
        if S3_BUCKET_NAME in image_url and s3_client:
            # Extract the key from the URL
            # This is a simple approach and might need adjustment based on your URL structure
            match = re.search(f"{S3_BUCKET_NAME}/(.+?)(\?|$)", image_url)
            if match:
                key = match.group(1)
                
                # Analyze using Rekognition
                response = rekognition_client.detect_labels(
                    Image={'S3Object': {'Bucket': S3_BUCKET_NAME, 'Name': key}},
                    MaxLabels=10
                )
                
                # Extract labels
                labels = [label['Name'] for label in response.get('Labels', [])]
                
                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'image_url': image_url,
                    'analysis': {
                        'labels': labels
                    }
                }
        
        # For external URLs, we need to download the image first
        # This is a placeholder for that functionality
        logger.warning("Analysis of external images not implemented")
        return {
            'success': False,
            'error': 'Analysis of external images not implemented'
        }
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def format_rich_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a response with both text and image content for rich frontends
    
    Args:
        data: The data to format
        
    Returns:
        Dict with text and image content
    """
    # Extract images
    images = data.get('images', [])
    
    # Format for rich display
    rich_content = {
        'type': 'rich_content',
        'text': data.get('message', f"Found {len(images)} NFT images"),
        'images': []
    }
    
    # Format each image
    for img in images:
        image_url = img.get('image_url')
        if image_url:
            metadata = img.get('metadata', {})
            rich_content['images'].append({
                'url': image_url,
                'title': metadata.get('name', ''),
                'description': metadata.get('description', ''),
                'token_id': img.get('token_id', '')
            })
    
    # Add success status and error info
    rich_content['success'] = data.get('success', bool(images))
    if 'error' in data:
        rich_content['error'] = data['error']
    
    return rich_content
"""
