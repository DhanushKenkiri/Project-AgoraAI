"""
Enhanced NFT wallet login handler with session management

This module handles wallet connections and authentication with session persistence
"""
import os
import json
import uuid
import logging
import time
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced_wallet_login")

try:
    from session_manager import get_wallet_address, store_wallet_address, get_user_data, store_user_data
except ImportError:
    logger.warning("Could not import session_manager module, using mock implementation")
    
    # Mock implementation of session management functions
    _session_store = {}
    _user_data_store = {}
    
    def get_wallet_address(session_id, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        return _session_store.get(key)
    
    def store_wallet_address(session_id, wallet_address, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        _session_store[key] = wallet_address
        return True
        
    def get_user_data(session_id, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        return _user_data_store.get(key, {})
    
    def store_user_data(session_id, data, user_id=None):
        key = f"{session_id}:{user_id}" if user_id else session_id
        _user_data_store[key] = data
        return True

try:
    from wallet_login import wallet_login, get_wallet_info
except ImportError:
    logger.warning("Could not import wallet_login module, using mock implementation")
    
    # Mock implementation of wallet functions
    def wallet_login(wallet_address, wallet_type='metamask'):
        return {
            'success': True,
            'wallet_address': wallet_address,
            'wallet_type': wallet_type,
            'message': 'Mock wallet login successful'
        }
    
    def get_wallet_info(wallet_address):
        return {
            'success': True, 
            'wallet_address': wallet_address,
            'balance': '0.5 ETH',
            'network': 'Ethereum'
        }

# Try to import NFT wallet functions
try:
    from nft_wallet import get_wallet_nfts, get_wallet_details
except ImportError:
    logger.warning("Could not import nft_wallet module, using mock implementation")
    
    # Mock implementation of NFT wallet functions
    def get_wallet_nfts(wallet_address):
        return {
            'success': True,
            'nfts': [
                {
                    'contract_address': '0x1234567890abcdef',
                    'token_id': '1',
                    'name': 'Mock NFT #1',
                    'image_url': 'https://example.com/nft1.jpg'
                }
            ]
        }
        
    def get_wallet_details(wallet_address):
        return {
            'success': True,
            'address': wallet_address,
            'balance': '0.5 ETH',
            'network': 'Ethereum'
        }

def handle_wallet_connection(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle wallet connection requests including connection verification,
    reconnection and wallet switching
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    method = event.get('httpMethod', 'POST')
    path = event.get('path', '')
    
    # Extract session ID from headers or query parameters
    session_id = event.get('headers', {}).get('x-session-id', None)
    if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('session_id', str(uuid.uuid4()))
    
    # Default to a new UUID if no session ID is provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Handle wallet connection
    if method == 'POST' and path == '/wallet/connect':
        try:
            # Parse the request body
            body = json.loads(event.get('body', '{}'))
            wallet_address = body.get('wallet_address', '')
            wallet_type = body.get('wallet_type', 'metamask')
            signature = body.get('signature', '') # For verification if needed
            user_id = body.get('user_id', None)
            
            if not wallet_address:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Wallet address is required',
                        'session_id': session_id
                    })
                }
            
            # Process the wallet login
            login_result = wallet_login(wallet_address, wallet_type)
            
            # If login successful, store the wallet address in the session
            if login_result.get('success'):
                store_wallet_address(session_id, wallet_address, user_id)
                login_result['session_id'] = session_id
                login_result['connected'] = True
                login_result['message'] = f"Successfully connected wallet {wallet_address}"
            
            return {
                'statusCode': 200 if login_result.get('success') else 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(login_result)
            }
        except Exception as e:
            logger.error(f"Error handling wallet connection: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Get wallet connection status
    elif method == 'GET' and path == '/wallet/status':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            user_id = params.get('user_id', None)
            
            # Check if there's a wallet address for this session
            wallet_address = get_wallet_address(session_id, user_id)
            
            if wallet_address:
                # Get wallet info
                wallet_info = get_wallet_info(wallet_address)
                wallet_info['connected'] = True
                wallet_info['session_id'] = session_id
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps(wallet_info)
                }
            else:
                # No wallet connected for this session
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': True,
                        'connected': False,
                        'message': 'No wallet is currently connected for this session',
                        'session_id': session_id
                    })
                }
        except Exception as e:
            logger.error(f"Error checking wallet status: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Disconnect wallet
    elif method == 'POST' and path == '/wallet/disconnect':
        try:
            # Parse the request body
            body = json.loads(event.get('body', '{}'))
            user_id = body.get('user_id', None)
            
            # Store empty wallet address to effectively disconnect
            store_wallet_address(session_id, '', user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': True,
                    'connected': False,
                    'message': 'Wallet disconnected successfully',
                    'session_id': session_id
                })
            }
        except Exception as e:
            logger.error(f"Error disconnecting wallet: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Get wallet NFTs
    elif method == 'GET' and path == '/wallet/nfts':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            user_id = params.get('user_id', None)
            
            # Check if there's a wallet address for this session
            wallet_address = get_wallet_address(session_id, user_id)
            
            if not wallet_address:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'No wallet connected for this session',
                        'session_id': session_id
                    })
                }
            
            # Get NFTs for the wallet
            nfts_result = get_wallet_nfts(wallet_address)
            
            return {
                'statusCode': 200 if nfts_result.get('success') else 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(nfts_result)
            }
        except Exception as e:
            logger.error(f"Error retrieving wallet NFTs: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Get wallet details
    elif method == 'GET' and path == '/wallet/details':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            user_id = params.get('user_id', None)
            
            # Check if there's a wallet address for this session
            wallet_address = get_wallet_address(session_id, user_id)
            
            if not wallet_address:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'No wallet connected for this session',
                        'session_id': session_id
                    })
                }
            
            # Get details for the wallet
            details_result = get_wallet_details(wallet_address)
            
            return {
                'statusCode': 200 if details_result.get('success') else 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(details_result)
            }
        except Exception as e:
            logger.error(f"Error retrieving wallet details: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Handle unknown requests
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-session-id',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Endpoint not found',
                'session_id': session_id
            })
        }

def get_wallet_nfts_with_images(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get NFTs owned by the connected wallet with image URLs
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response with NFT data
    """
    # Extract session ID from headers or query parameters
    session_id = event.get('headers', {}).get('x-session-id', None)
    if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('session_id')
    
    # User ID is optional
    user_id = None
    if 'queryStringParameters' in event and event['queryStringParameters']:
        user_id = event['queryStringParameters'].get('user_id')
    
    # If no session ID, return error
    if not session_id:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': 'Session ID is required'
            })
        }
    
    # Get wallet address from session
    wallet_address = get_wallet_address(session_id, user_id)
    
    # Check if wallet is connected
    if not wallet_address:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': 'Wallet not connected',
                'session_id': session_id
            })
        }
    
    try:
        # Get NFTs owned by the wallet
        nfts_result = get_wallet_nfts(wallet_address)
        
        # Get user data
        user_data = get_user_data(session_id, user_id) or {}
        
        # Update NFT data in user session
        user_data['nfts'] = {
            'fetched_at': int(time.time()),
            'count': len(nfts_result.get('nfts', [])),
            'wallet_address': wallet_address
        }
        
        # Store updated user data
        store_user_data(session_id, user_data, user_id)
        
        # Format the response for rich display
        formatted_nfts = []
        for nft in nfts_result.get('nfts', []):
            formatted_nft = {
                'token_id': nft.get('token_id', ''),
                'name': nft.get('name', f"NFT #{nft.get('token_id', '')}"),
                'contract_address': nft.get('contract_address', ''),
                'image_url': nft.get('image_url', '')
            }
            
            # Add any additional metadata if available
            if 'metadata' in nft:
                formatted_nft['metadata'] = nft['metadata']
                
            formatted_nfts.append(formatted_nft)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'nfts': formatted_nfts,
                'wallet_address': wallet_address,
                'session_id': session_id
            })
        }
    except Exception as e:
        logger.error(f"Error getting wallet NFTs: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'session_id': session_id
            })
        }

def handle_bedrock_wallet_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle wallet requests from Bedrock agent with image support
    
    Args:
        event: The Bedrock agent event
        
    Returns:
        Response for Bedrock agent
    """
    try:
        # Extract request details
        session_id = event.get('sessionId')
        user_id = event.get('userId')
        
        if not session_id:
            return {
                'success': False, 
                'error': 'No session ID provided',
                'message': 'A session ID is required for wallet operations'
            }
        
        # Extract parameters from Bedrock request
        request = event.get('requestBody', {})
        parameters = request.get('parameters', [])
        
        # Extract parameters
        param_dict = {}
        for param in parameters:
            name = param.get('name', '')
            value = param.get('value', '')
            param_dict[name] = value
        
        # Determine the operation type
        operation = request.get('apiPath', '').split('/')[-1]
        
        # Connect wallet
        if operation == 'connect':
            wallet_address = param_dict.get('wallet_address')
            wallet_type = param_dict.get('wallet_type', 'metamask')
            
            if not wallet_address:
                return {
                    'success': False,
                    'error': 'Wallet address is required',
                    'message': 'Please provide a valid wallet address'
                }
            
            # Connect wallet and store in session
            store_wallet_address(session_id, wallet_address, user_id)
            
            return {
                'success': True,
                'wallet_address': wallet_address,
                'message': 'Wallet connected successfully',
                'session_id': session_id
            }
        
        # Check wallet status
        elif operation == 'status':
            wallet_address = get_wallet_address(session_id, user_id)
            
            if wallet_address:
                return {
                    'success': True,
                    'connected': True,
                    'wallet_address': wallet_address,
                    'message': 'Wallet is connected',
                    'session_id': session_id
                }
            else:
                return {
                    'success': True,
                    'connected': False,
                    'message': 'No wallet is connected',
                    'session_id': session_id
                }
        
        # Disconnect wallet
        elif operation == 'disconnect':
            # Remove wallet from session
            store_wallet_address(session_id, None, user_id)
            
            return {
                'success': True,
                'message': 'Wallet disconnected successfully',
                'session_id': session_id
            }
        
        # Get NFTs with images
        elif operation == 'nfts':
            wallet_address = get_wallet_address(session_id, user_id)
            
            if not wallet_address:
                return {
                    'success': False,
                    'error': 'No wallet connected',
                    'message': 'Please connect a wallet first'
                }
            
            # Get NFTs owned by the wallet
            nfts_result = get_wallet_nfts(wallet_address)
            
            # Format the response with image URLs
            formatted_nfts = []
            image_urls = []
            
            for nft in nfts_result.get('nfts', []):
                formatted_nft = {
                    'token_id': nft.get('token_id', ''),
                    'name': nft.get('name', ''),
                    'image_url': nft.get('image_url', '')
                }
                formatted_nfts.append(formatted_nft)
                
                if nft.get('image_url'):
                    image_urls.append(nft.get('image_url'))
            
            return {
                'success': True,
                'nfts': formatted_nfts,
                'images': image_urls[:5],  # Limit to 5 images
                'message': f"Found {len(formatted_nfts)} NFTs",
                'wallet_address': wallet_address
            }
        
        else:
            return {
                'success': False,
                'error': f"Unsupported wallet operation: {operation}",
                'message': 'This wallet operation is not supported'
            }
            
    except Exception as e:
        logger.error(f"Error handling Bedrock wallet request: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to process wallet request'
        }
