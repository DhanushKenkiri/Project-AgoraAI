# (This is the fully rewritten lambda_handler.py file)

import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import boto3
import uuid
import base64
import sys

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import API integrations
from apis.moralis_api import fetch_moralis_data
from apis.alchemy_api import fetch_alchemy_data
from apis.nftscan_api import fetch_nftscan_data
from apis.opensea_api import fetch_opensea_data
from apis.nftgo_api import fetch_nftgo_data
from apis.reservoir_api import fetch_collection_data, fetch_market_data, fetch_rarity_data
from apis.perplexity_api import search_web_with_perplexity
from apis.etherscan_api import fetch_gas_prices
from utils.utils import check_api_availability, generate_search_query
from utils.recommendations import generate_recommendations
from utils.sentiment import fetch_social_sentiment
from config import load_api_keys

# Import our enhanced modules with safe error handling
try:
    # Enhanced wallet login handler with session management
    from enhanced_wallet_login import handle_wallet_connection, check_wallet_status, disconnect_wallet
    # Image processing modules
    from image_processor import process_image_upload, get_image_by_id
    from nft_image_processor import get_nft_images, get_wallet_nft_images
    # Bedrock integration
    from bedrock_integration import bedrock_agent_handler    # CDP wallet and X402 payment integration
    from cdp_wallet_x402_integration import handle_combined_wallet_payment_request
except ImportError as e:
    logger.warning(f"Failed to import enhanced modules: {str(e)}")

# Import wallet login handlers with fallbacks
try:
    from wallet_login import wallet_login, get_wallet_info
    from nft_wallet import handle_wallet_login, get_wallet_details, get_wallet_nfts, check_transaction_status
except ImportError:
    # Fallback if wallet_login.py doesn't exist or has errors
    logger.warning("Using fallback wallet integration")
    from x402_payment_handler import handle_wallet_connection
    wallet_login = lambda wallet_address: handle_wallet_connection({'wallet_address': wallet_address})
    get_wallet_info = lambda wallet_address: {'success': True, 'wallet_address': wallet_address}
    handle_wallet_login = lambda wallet_address, wallet_type=None: {'success': True, 'wallet_address': wallet_address}
    get_wallet_details = lambda wallet_address: {'success': True, 'wallet_address': wallet_address, 'balance': '0.5 ETH'}
    get_wallet_nfts = lambda wallet_address: {'success': True, 'nfts': []}
    check_transaction_status = lambda tx_id: {'success': True, 'status': 'pending'}

# Define CORS headers for responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

def fetch_data_from_apis(token_address, token_id):
    """
    Fetch NFT data from multiple APIs concurrently with fallbacks
    """
    start_time = time.time()
    
    # Load API keys from environment or configuration
    api_keys = load_api_keys()
    
    # Available APIs to try
    available_apis = check_api_availability(api_keys)
    
    # Prepare results dictionary
    results = {
        'token_address': token_address,
        'token_id': token_id,
        'success': False,
        'data_sources': [],
        'processing_time': 0,
        'api_response_times': {},
        'error': None
    }
    
    try:
        # Use ThreadPoolExecutor for concurrent API calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            # Submit API tasks based on availability
            if available_apis.get('moralis'):
                futures['moralis'] = executor.submit(fetch_moralis_data, token_address, token_id, api_keys.get('MORALIS_API_KEY', ''))
            
            if available_apis.get('alchemy'):
                futures['alchemy'] = executor.submit(fetch_alchemy_data, token_address, token_id, api_keys.get('ALCHEMY_API_KEY', ''))
            
            if available_apis.get('nftscan'):
                futures['nftscan'] = executor.submit(fetch_nftscan_data, token_address, token_id, api_keys.get('NFTSCAN_API_KEY', ''))
            
            if available_apis.get('opensea'):
                futures['opensea'] = executor.submit(fetch_opensea_data, token_address, token_id, api_keys.get('OPENSEA_API_KEY', ''))
            
            if available_apis.get('nftgo'):
                futures['nftgo'] = executor.submit(fetch_nftgo_data, token_address, token_id, api_keys.get('NFTGO_API_KEY', ''))
            
            # Process results as they complete
            for api_name, future in futures.items():
                try:
                    api_start = time.time()
                    api_result = future.result(timeout=10)  # 10 second timeout
                    api_time = time.time() - api_start
                    
                    # Record API response time
                    results['api_response_times'][api_name] = api_time
                    
                    # Add API data to results if successful
                    if api_result and api_result.get('success'):
                        results['data_sources'].append(api_name)
                        
                        # Merge API data into results
                        for key, value in api_result.items():
                            if key != 'success':
                                results[key] = value
                    
                except Exception as e:
                    logger.error(f"Error from {api_name} API: {str(e)}")
            
            # If no API data available, try web search as fallback
            if not results['data_sources'] and available_apis.get('perplexity'):
                try:
                    web_search_query = generate_search_query(token_address, token_id)
                    web_result = search_web_with_perplexity(web_search_query, api_keys.get('PERPLEXITY_API_KEY', ''))
                    
                    if web_result and web_result.get('success'):
                        results['data_sources'].append('web_search')
                        results['web_search_data'] = web_result.get('data')
                except Exception as e:
                    logger.error(f"Web search fallback failed: {str(e)}")
        
        # Mark as successful if we have any data sources
        results['success'] = len(results['data_sources']) > 0
    
    except Exception as e:
        logger.error(f"General data fetching error: {str(e)}")
        results['error'] = str(e)
    
    # Calculate total processing time
    results['processing_time'] = time.time() - start_time
    
    return results

def trim_response_if_needed(response_data, max_size=6291556):  # Lambda limit is 6MB
    """
    Trim response data to fit within Lambda limits
    """
    try:
        # Convert to JSON to check size
        response_json = json.dumps(response_data)
        current_size = len(response_json.encode('utf-8'))
        
        if current_size <= max_size:
            return response_data, False
        
        # Need to trim the response
        trimmed_data = response_data.copy()
        
        # Start by removing fields that might have large content
        large_fields = ['metadata_raw', 'description', 'attributes', 'web_search_data']
        for field in large_fields:
            if field in trimmed_data:
                del trimmed_data[field]
                
                # Check if we're under the limit now
                trimmed_json = json.dumps(trimmed_data)
                if len(trimmed_json.encode('utf-8')) <= max_size:
                    return trimmed_data, True
        
        # If still too large, trim other fields
        if 'transaction_history' in trimmed_data:
            trimmed_data['transaction_history'] = trimmed_data['transaction_history'][:5]
        
        if 'similar_nfts' in trimmed_data:
            trimmed_data['similar_nfts'] = trimmed_data['similar_nfts'][:3]
        
        return trimmed_data, True
    
    except Exception as e:
        logger.error(f"Error trimming response: {str(e)}")
        return response_data, False

def lambda_handler(event, context):
    """
    AWS Lambda handler to fetch comprehensive NFT data with smart fallbacks and web search.
    Uses multiple NFT APIs with graceful degradation to Perplexity web search if APIs fail.
    Also handles wallet login and payment requests.
    Integrates with Bedrock Agent for AI capabilities.
    """
    # Parse API path if present
    path = event.get('path', '')
    http_method = event.get('httpMethod', 'GET')
    
    # Handle different API endpoints
    if path == '/wallet/login' or path == '/wallet/connect':
        return handle_wallet_request(event)
    elif path == '/wallet/status':
        return handle_wallet_status(event)
    elif path == '/wallet/disconnect':
        return handle_wallet_disconnect(event)
    elif path == '/wallet/nfts':
        return handle_wallet_nfts_request(event)
    elif path == '/wallet/nft-images':
        return handle_wallet_nft_images(event)
    elif path == '/wallet/details':
        return handle_wallet_details_request(event)
    elif path == '/image/upload':
        return handle_image_upload(event)
    elif path == '/image':
        return handle_image_request(event)
    elif path == '/payment/init':
        return handle_payment_request(event)
    elif path == '/transaction/status':
        return handle_transaction_status(event)
    elif path == '/pricing/calculate':
        return handle_pricing_request(event)
    elif path == '/blockchain/gas':
        return handle_gas_request(event)
    elif path == '/search/web':
        return handle_web_search_request(event)
    elif path == '/nft/sentiment':
        return handle_sentiment_request(event)
    elif path == '/nft/multi-analysis':
        return handle_multi_collection_request(event)
    elif path == '/nft/rarity':
        return handle_rarity_request(event)
    elif path == '/collection/floor':
        return handle_collection_price_request(event)
    elif path == '/nft/query':
        return handle_nft_query_request(event)
    elif path == '/ai/chat' or path == '/agent/chat':
        return handle_ai_chat_request(event)
    elif '/ui/' in path:
        return handle_ui_request(event)
    elif path.startswith('/cdp/wallet/') or path.startswith('/x402/'):
        try:
            # Route to combined CDP wallet and X402 payment handler
            return handle_combined_wallet_payment_request(event)
        except Exception as e:
            logger.error(f"Error handling CDP wallet or X402 payment request: {str(e)}")
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': f'CDP wallet or X402 payment processing failed: {str(e)}'
                })
            }
    
    # Check if this is a Bedrock agent request
    if ('action' in event and 'parameters' in event) or ('requestBody' in event and 'messageVersion' in event):
        # This appears to be a Bedrock agent request, we need to handle it properly
        try:
            return handle_bedrock_agent_request(event, context)
        except Exception as e:
            logger.error(f"Error handling Bedrock agent request: {str(e)}")
            return {
                'messageVersion': '1.0',
                'response': {
                    'message': f"Sorry, I encountered an error: {str(e)}"
                }
            }
    
    # Default NFT data query handling
    try:
        # Extract token address and ID from query parameters
        params = event.get('queryStringParameters', {}) or {}
        
        token_address = params.get('address') or params.get('contract') or params.get('token_address')
        token_id = params.get('id') or params.get('token_id')
        
        # Validate input
        if not token_address or not token_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required parameters: address and id'
                })
            }
        
        # Fetch data from APIs
        result = fetch_data_from_apis(token_address, token_id)
        
        # Generate value-added insights if data is available
        if result['success']:
            try:
                # Enhance with recommendations
                result['recommendations'] = generate_recommendations(result)
                
                # Enhance with sentiment analysis if available
                try:
                    sentiment_data = fetch_social_sentiment(token_address)
                    if sentiment_data and sentiment_data.get('success'):
                        result['sentiment'] = sentiment_data.get('sentiment', {})
                except Exception as e:
                    logger.warning(f"Error fetching sentiment data: {str(e)}")
            
            except Exception as e:
                logger.warning(f"Error generating insights: {str(e)}")
        
        # Trim response if needed
        trimmed_result, was_trimmed = trim_response_if_needed(result)
        if was_trimmed:
            trimmed_result['note'] = 'Response was trimmed due to size limits'
        
        # Return the API response
        return {
            'statusCode': 200 if result['success'] else 404,
            'headers': CORS_HEADERS,
            'body': json.dumps(trimmed_result)
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_bedrock_agent_request(event, context):
    """Handle Bedrock agent requests"""
    try:
        # If bedrock_agent_handler is available, use it
        if 'bedrock_agent_handler' in globals():
            return bedrock_agent_handler(event, context)
        
        # Fallback response if handler not available
        return {
            'messageVersion': '1.0',
            'response': {
                'message': "I'm sorry, but the Bedrock agent integration is not available."
            }
        }
    except Exception as e:
        logger.error(f"Error in Bedrock agent handler: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'message': f"Sorry, I encountered an error: {str(e)}"
            }
        }

def handle_wallet_request(event):
    """Handle wallet login/connect requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        wallet_address = body.get('wallet_address')
        wallet_type = body.get('wallet_type', 'metamask')
        signature = body.get('signature')
        
        if not wallet_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Wallet address is required'
                })
            }
        
        # Try enhanced wallet connection if available
        try:
            if 'handle_wallet_connection' in globals():
                result = handle_wallet_connection(event)
                return {
                    'statusCode': 200 if result.get('success') else 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(result)
                }
        except Exception as e:
            logger.warning(f"Enhanced wallet connection failed, using fallback: {str(e)}")
        
        # Fallback to basic wallet login
        result = wallet_login(wallet_address)
        
        return {
            'statusCode': 200 if result.get('success') else 400,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Wallet request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_wallet_status(event):
    """Handle wallet status check"""
    try:
        # Get session ID from headers or query parameters
        headers = event.get('headers', {}) or {}
        params = event.get('queryStringParameters', {}) or {}
        
        session_id = headers.get('x-session-id') or params.get('session_id')
        
        # Try enhanced wallet status check if available
        try:
            if 'check_wallet_status' in globals():
                result = check_wallet_status(session_id)
                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(result)
                }
        except Exception as e:
            logger.warning(f"Enhanced wallet status check failed, using fallback: {str(e)}")
        
        # Fallback response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'connected': bool(session_id),
                'wallet_address': session_id and f"0x{session_id[-8:]}" or None
            })
        }
    
    except Exception as e:
        logger.error(f"Wallet status error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_wallet_disconnect(event):
    """Handle wallet disconnect requests"""
    try:
        # Get session ID from headers or body
        headers = event.get('headers', {}) or {}
        body = json.loads(event.get('body', '{}'))
        
        session_id = headers.get('x-session-id') or body.get('session_id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Session ID is required'
                })
            }
        
        # Try enhanced wallet disconnect if available
        try:
            if 'disconnect_wallet' in globals():
                result = disconnect_wallet(session_id)
                return {
                    'statusCode': 200 if result.get('success') else 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(result)
                }
        except Exception as e:
            logger.warning(f"Enhanced wallet disconnect failed, using fallback: {str(e)}")
        
        # Fallback response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'Wallet disconnected successfully'
            })
        }
    
    except Exception as e:
        logger.error(f"Wallet disconnect error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_wallet_nfts_request(event):
    """Handle requests for NFTs owned by a wallet"""
    try:
        # Get wallet address from query parameters
        params = event.get('queryStringParameters', {}) or {}
        wallet_address = params.get('wallet_address') or params.get('address')
        
        if not wallet_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Wallet address is required'
                })
            }
        
        # Get NFTs from wallet
        result = get_wallet_nfts(wallet_address)
        
        # Trim response if needed
        trimmed_result, was_trimmed = trim_response_if_needed(result)
        if was_trimmed:
            trimmed_result['note'] = 'Response was trimmed due to size limits'
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(trimmed_result)
        }
    
    except Exception as e:
        logger.error(f"Wallet NFTs error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_wallet_details_request(event):
    """Handle wallet details request"""
    try:
        # Get wallet address from query parameters
        params = event.get('queryStringParameters', {}) or {}
        wallet_address = params.get('wallet_address') or params.get('address')
        
        if not wallet_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Wallet address is required'
                })
            }
        
        # Get wallet details
        result = get_wallet_details(wallet_address)
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Wallet details error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_image_upload(event):
    """Handle image upload requests"""
    try:
        if not 'process_image_upload' in globals():
            return {
                'statusCode': 501,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Image upload functionality not available'
                })
            }
        
        # Get image data from request body
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image_data')
        image_name = body.get('image_name', 'uploaded_image')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Image data is required'
                })
            }
        
        # Process image upload
        result = process_image_upload(image_data, image_name)
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_image_request(event):
    """Handle image retrieval requests"""
    try:
        if not 'get_image_by_id' in globals():
            return {
                'statusCode': 501,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Image retrieval functionality not available'
                })
            }
        
        # Get image ID from query parameters
        params = event.get('queryStringParameters', {}) or {}
        image_id = params.get('id')
        
        if not image_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Image ID is required'
                })
            }
        
        # Get image by ID
        result = get_image_by_id(image_id)
        
        return {
            'statusCode': 200 if result.get('success') else 404,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Image retrieval error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_payment_request(event):
    """Handle payment initialization requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        wallet_address = body.get('wallet_address')
        amount = body.get('amount')
        currency = body.get('currency', 'ETH')
        
        if not wallet_address or not amount:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Wallet address and amount are required'
                })
            }
        
        # Generate payment ID
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        
        # Return payment initiation response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'payment_id': payment_id,
                'wallet_address': wallet_address,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'created_at': time.time()
            })
        }
    
    except Exception as e:
        logger.error(f"Payment request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_transaction_status(event):
    """Handle transaction status check requests"""
    try:
        # Get transaction ID from query parameters
        params = event.get('queryStringParameters', {}) or {}
        tx_id = params.get('tx_id') or params.get('id')
        
        if not tx_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Transaction ID is required'
                })
            }
        
        # Check transaction status
        result = check_transaction_status(tx_id)
        
        return {
            'statusCode': 200 if result.get('success') else 404,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Transaction status error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_pricing_request(event):
    """Handle pricing calculation requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        nft_count = body.get('nft_count', 1)
        tier = body.get('tier', 'standard')
        
        # Calculate price based on NFT count and tier
        base_price = 0.01  # Base price in ETH
        
        if tier == 'premium':
            base_price = 0.03
        elif tier == 'enterprise':
            base_price = 0.05
        
        total_price = base_price * max(1, nft_count)
        
        # Apply volume discount
        if nft_count > 10:
            discount = 0.15  # 15% discount for more than 10 NFTs
            total_price = total_price * (1 - discount)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'nft_count': nft_count,
                'tier': tier,
                'base_price': base_price,
                'total_price': total_price,
                'currency': 'ETH'
            })
        }
    
    except Exception as e:
        logger.error(f"Pricing calculation error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_gas_request(event):
    """Handle gas price retrieval requests"""
    try:
        # Load API keys
        api_keys = load_api_keys()
        
        # Fetch gas prices
        gas_prices = fetch_gas_prices(api_keys.get('ETHERSCAN_API_KEY', ''))
        
        if not gas_prices.get('success'):
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Failed to retrieve gas prices'
                })
            }
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps(gas_prices)
        }
    
    except Exception as e:
        logger.error(f"Gas price retrieval error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_web_search_request(event):
    """Handle web search requests"""
    try:
        # Get query from query parameters
        params = event.get('queryStringParameters', {}) or {}
        query = params.get('query')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Search query is required'
                })
            }
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Search web with Perplexity
        result = search_web_with_perplexity(query, api_keys.get('PERPLEXITY_API_KEY', ''))
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Web search error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_sentiment_request(event):
    """Handle NFT sentiment analysis requests"""
    try:
        # Get contract address from query parameters
        params = event.get('queryStringParameters', {}) or {}
        contract_address = params.get('address') or params.get('contract')
        
        if not contract_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Contract address is required'
                })
            }
        
        # Fetch sentiment data
        sentiment_data = fetch_social_sentiment(contract_address)
        
        return {
            'statusCode': 200 if sentiment_data.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(sentiment_data)
        }
    
    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_multi_collection_request(event):
    """Handle multi-collection analysis requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        collections = body.get('collections', [])
        
        if not collections:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Collections array is required'
                })
            }
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Analyze multiple collections
        results = {}
        
        for collection in collections:
            try:
                collection_data = fetch_collection_data(collection, api_keys.get('RESERVOIR_API_KEY', ''))
                results[collection] = collection_data
            except Exception as e:
                results[collection] = {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'results': results
            })
        }
    
    except Exception as e:
        logger.error(f"Multi-collection analysis error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_rarity_request(event):
    """Handle NFT rarity analysis requests"""
    try:
        # Get parameters from query parameters
        params = event.get('queryStringParameters', {}) or {}
        contract_address = params.get('address') or params.get('contract')
        token_id = params.get('id') or params.get('token_id')
        
        if not contract_address or not token_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Contract address and token ID are required'
                })
            }
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Fetch rarity data
        rarity_data = fetch_rarity_data(contract_address, token_id, api_keys.get('RESERVOIR_API_KEY', ''))
        
        return {
            'statusCode': 200 if rarity_data.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(rarity_data)
        }
    
    except Exception as e:
        logger.error(f"Rarity analysis error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_collection_price_request(event):
    """Handle collection floor price requests"""
    try:
        # Get collection address from query parameters
        params = event.get('queryStringParameters', {}) or {}
        collection_address = params.get('address') or params.get('collection')
        
        if not collection_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Collection address is required'
                })
            }
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Fetch market data
        market_data = fetch_market_data(collection_address, api_keys.get('RESERVOIR_API_KEY', ''))
        
        return {
            'statusCode': 200 if market_data.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(market_data)
        }
    
    except Exception as e:
        logger.error(f"Collection price error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_nft_query_request(event):
    """Handle natural language NFT queries"""
    try:
        # Get query from query parameters
        params = event.get('queryStringParameters', {}) or {}
        query = params.get('query')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Query is required'
                })
            }
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Use Perplexity to search for NFT info
        search_result = search_web_with_perplexity(f"NFT {query}", api_keys.get('PERPLEXITY_API_KEY', ''))
        
        if not search_result.get('success'):
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Failed to process NFT query'
                })
            }
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'query': query,
                'result': search_result.get('data', {})
            })
        }
    
    except Exception as e:
        logger.error(f"NFT query error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_ai_chat_request(event):
    """Handle AI chat requests"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Message is required'
                })
            }
        
        # Process AI chat request
        try:
            # Try using the bedrock agent handler if available
            response = handle_bedrock_agent_request({
                'action': {
                    'name': 'userMessage',
                    'parameters': {
                        'message': message
                    }
                }
            }, None)
            
            # Extract message from Bedrock response
            if 'response' in response and 'message' in response['response']:
                ai_response = response['response']['message']
            else:
                ai_response = "I'm sorry, I couldn't process your request."
            
        except Exception:
            # Fallback to simple response
            ai_response = f"I received your message: '{message}'. How can I help with NFTs today?"
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': message,
                'response': ai_response
            })
        }
    
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_ui_request(event):
    """Handle UI resource requests"""
    try:
        path = event.get('path', '')
        
        # Simple UI resources handler
        if path.endswith('.html'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                    **CORS_HEADERS
                },
                'body': "<html><body><h1>NFT Analyzer UI</h1><p>This is a placeholder UI.</p></body></html>"
            }
        elif path.endswith('.js'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/javascript',
                    **CORS_HEADERS
                },
                'body': "console.log('NFT Analyzer UI Script');"
            }
        elif path.endswith('.css'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/css',
                    **CORS_HEADERS
                },
                'body': "body { font-family: Arial, sans-serif; }"
            }
        else:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'UI resource not found'
                })
            }
    
    except Exception as e:
        logger.error(f"UI request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_wallet_nft_images(event):
    """
    Handle requests for NFT images from a wallet
    """
    try:
        if 'get_wallet_nft_images' not in globals():
            return {
                'statusCode': 501,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'NFT image retrieval functionality not available'
                })
            }
        
        # Get wallet address from query parameters
        params = event.get('queryStringParameters', {}) or {}
        wallet_address = params.get('wallet_address') or params.get('address')
        limit = params.get('limit')
        if limit:
            try:
                limit = int(limit)
            except:
                limit = None
        
        if not wallet_address:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': 'Wallet address is required'
                })
            }
        
        # Get NFT images from the wallet
        result = get_wallet_nft_images(wallet_address, limit)
        
        # Trim response if needed
        trimmed_result, was_trimmed = trim_response_if_needed(result)
        if was_trimmed:
            trimmed_result['note'] = 'Response was trimmed due to size limits'
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(trimmed_result)
        }
    except Exception as e:
        logger.error(f"NFT image retrieval error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': f'NFT image retrieval failed: {str(e)}'
            })
        }

def handle_combined_wallet_payment_request(event):
    """
    Route CDP wallet and X402 payment requests to the appropriate handler
    """
    try:
        # Import the handler module if not already imported
        if 'handle_combined_wallet_payment_request' not in globals():
            from cdp_wallet_x402_integration import handle_combined_wallet_payment_request
        
        # Forward the request to the CDP wallet and X402 payment handler
        return handle_combined_wallet_payment_request(event)
    except Exception as e:
        logger.error(f"Error handling CDP wallet or X402 payment request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': f'CDP wallet or X402 payment processing failed: {str(e)}'
            })
        }
