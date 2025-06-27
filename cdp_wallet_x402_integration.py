"""
Enhanced CDP Wallet Integration Module

This module extends the enhanced_wallet_login.py with CDP wallet functionality
and X402 payment capabilities.
"""
import os
import json
import uuid
import logging
import time
import base64
import requests
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cdp_wallet_integration")

# Try to import from session manager
try:
    from session_manager import get_wallet_address, store_wallet_address, get_user_data, store_user_data
except ImportError:
    logger.warning("Could not import session_manager module")
    from enhanced_wallet_login import get_wallet_address, store_wallet_address, get_user_data, store_user_data

# Import CDP wallet handler
try:
    from cdp_wallet_handler import (
        connect_cdp_wallet, 
        verify_wallet_signature, 
        get_wallet_session, 
        create_cdp_transaction
    )
except ImportError:
    logger.warning("Could not import cdp_wallet_handler, using mock implementation")
    
    # Mock CDP wallet functions for testing without the real implementation
    def connect_cdp_wallet(wallet_address, wallet_type):
        return {
            'success': True,
            'session_id': str(uuid.uuid4()),
            'wallet_address': wallet_address,
            'wallet_type': wallet_type,
            'expiration': int(time.time()) + 3600  # 1 hour expiration
        }
    
    def verify_wallet_signature(wallet_address, message, signature):
        return {
            'success': True,
            'verified': True,
            'wallet_address': wallet_address,
            'message': 'Signature verified'
        }
    
    def get_wallet_session(session_id):
        return {
            'success': True,
            'active': True,
            'wallet_address': '0x123...abc',
            'expiration': int(time.time()) + 3600
        }
    
    def create_cdp_transaction(wallet_address, recipient, amount, currency='ETH', nonce=None):
        tx_id = str(uuid.uuid4())
        return {
            'success': True,
            'transaction_id': tx_id,
            'status': 'pending',
            'wallet_address': wallet_address,
            'amount': amount,
            'currency': currency,
            'recipient': recipient
        }

# Try to import X402 payment handler
try:
    from x402_payment_handler import (
        create_payment_header,
        verify_payment, 
        process_x402_payment,
        get_payment_requirements
    )
except ImportError:
    logger.warning("Could not import x402_payment_handler, using mock implementation")
    
    # Mock X402 payment functions
    def create_payment_header(wallet_address, amount, currency, resource_id):
        mock_header = {
            'wallet': wallet_address,
            'amount': amount,
            'currency': currency,
            'resource': resource_id,
            'timestamp': int(time.time())
        }
        return base64.b64encode(json.dumps(mock_header).encode()).decode()
    
    def verify_payment(payment_header):
        try:
            decoded = json.loads(base64.b64decode(payment_header).decode())
            return {
                'success': True,
                'verified': True,
                'wallet_address': decoded.get('wallet'),
                'amount': decoded.get('amount')
            }
        except:
            return {'success': False, 'verified': False, 'error': 'Invalid payment header'}
    
    def process_x402_payment(payment_header, resource_id):
        return {
            'success': True,
            'transaction_id': str(uuid.uuid4()),
            'status': 'completed',
            'resource_id': resource_id
        }
    
    def get_payment_requirements(resource_id):
        return {
            'resource': resource_id,
            'scheme': 'exact',
            'network': 'base-sepolia',
            'maxAmountRequired': '0.001',
            'payTo': '0xpaymentsrecipientaddress',
            'asset': 'ETH',
            'extra': {
                'validity': '600'
            }
        }

def handle_cdp_wallet_connection(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle CDP wallet connection with signature verification
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    # Extract method and path
    method = event.get('httpMethod', 'POST')
    path = event.get('path', '')
    
    # Extract session ID
    session_id = event.get('headers', {}).get('x-session-id', None)
    if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('session_id')
    
    # Generate new session ID if none was provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Handle CDP wallet connection endpoint
    if method == 'POST' and path == '/cdp/wallet/connect':
        try:
            # Parse body
            body = json.loads(event.get('body', '{}'))
            wallet_address = body.get('wallet_address')
            wallet_type = body.get('wallet_type', 'cdp')
            signature = body.get('signature')
            message = body.get('message')
            user_id = body.get('user_id')
            
            if not wallet_address:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': 'Wallet address is required',
                        'session_id': session_id
                    })
                }
                
            # Verify signature if provided
            if signature and message:
                verification = verify_wallet_signature(wallet_address, message, signature)
                if not verification.get('verified'):
                    return {
                        'statusCode': 401,
                        'headers': {'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'success': False,
                            'error': 'Invalid signature',
                            'session_id': session_id
                        })
                    }
            
            # Connect to CDP wallet
            connection_result = connect_cdp_wallet(wallet_address, wallet_type)
            
            if connection_result.get('success'):
                # Store in session
                store_wallet_address(session_id, wallet_address, user_id)
                
                # Store CDP-specific session info
                user_data = get_user_data(session_id, user_id) or {}
                user_data['cdp'] = {
                    'cdp_session_id': connection_result.get('session_id'),
                    'connected_at': int(time.time()),
                    'expiration': connection_result.get('expiration'),
                    'wallet_type': wallet_type
                }
                store_user_data(session_id, user_data, user_id)
                
                # Format response
                return {
                    'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'wallet_address': wallet_address,
                        'wallet_type': wallet_type,
                        'message': 'CDP wallet connected successfully',
                        'session_id': session_id,
                        'expiration': connection_result.get('expiration')
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': connection_result.get('error', 'Failed to connect CDP wallet'),
                        'session_id': session_id
                    })
                }
                
        except Exception as e:
            logger.error(f"Error connecting to CDP wallet: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Get CDP wallet status
    elif method == 'GET' and path == '/cdp/wallet/status':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            user_id = params.get('user_id')
            
            # Get wallet address from session
            wallet_address = get_wallet_address(session_id, user_id)
            
            if not wallet_address:
                return {
                    'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'connected': False,
                        'message': 'No CDP wallet connected',
                        'session_id': session_id
                    })
                }
            
            # Get user data for CDP details
            user_data = get_user_data(session_id, user_id) or {}
            cdp_data = user_data.get('cdp', {})
            
            # Check if CDP session is still valid
            if cdp_data.get('expiration', 0) < int(time.time()):
                return {
                    'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'connected': False,
                        'expired': True,
                        'message': 'CDP wallet session has expired',
                        'session_id': session_id
                    })
                }
                
            # Return wallet status
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'connected': True,
                    'wallet_address': wallet_address,
                    'wallet_type': cdp_data.get('wallet_type', 'cdp'),
                    'expiration': cdp_data.get('expiration'),
                    'session_id': session_id
                })
            }
            
        except Exception as e:
            logger.error(f"Error checking CDP wallet status: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Disconnect CDP wallet
    elif method == 'POST' and path == '/cdp/wallet/disconnect':
        try:
            # Parse body
            body = json.loads(event.get('body', '{}'))
            user_id = body.get('user_id')
            
            # Clear wallet from session
            store_wallet_address(session_id, '', user_id)
            
            # Clear CDP session data
            user_data = get_user_data(session_id, user_id) or {}
            if 'cdp' in user_data:
                del user_data['cdp']
            store_user_data(session_id, user_data, user_id)
            
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': 'CDP wallet disconnected successfully',
                    'session_id': session_id
                })
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting CDP wallet: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Handle unknown paths
    else:
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': 'Endpoint not found',
                'session_id': session_id
            })
        }

def handle_x402_payment(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle X402 payment protocol requests
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    # Extract method and path
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    
    # Extract session ID
    session_id = event.get('headers', {}).get('x-session-id', None)
    if not session_id and 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('session_id')
    
    # Generate new session ID if none was provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Check for x-payment header (X402 protocol)
    payment_header = event.get('headers', {}).get('x-payment')
    
    # Extract resource ID from path or query params
    resource_id = None
    if path.startswith('/x402/resource/'):
        resource_id = path.split('/x402/resource/')[1]
    elif 'queryStringParameters' in event and event['queryStringParameters']:
        resource_id = event['queryStringParameters'].get('resource_id')
    
    # Get payment requirements for resource
    if method == 'GET' and path == '/x402/payment/requirements':
        try:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            requested_resource = params.get('resource_id')
            
            if not requested_resource:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': 'Resource ID is required',
                        'session_id': session_id
                    })
                }
            
            # Get payment requirements
            requirements = get_payment_requirements(requested_resource)
            
            # Return with 402 Payment Required status
            return {
                'statusCode': 402,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'X-Payment-Required': 'x402'
                },
                'body': json.dumps({
                    'success': True,
                    'payment_required': True,
                    'requirements': requirements,
                    'session_id': session_id
                })
            }
            
        except Exception as e:
            logger.error(f"Error getting payment requirements: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Process resource request with payment
    elif method == 'GET' and resource_id and path.startswith('/x402/resource/'):
        # If payment header is missing, return payment requirements
        if not payment_header:
            requirements = get_payment_requirements(resource_id)
            return {
                'statusCode': 402,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'X-Payment-Required': 'x402'
                },
                'body': json.dumps({
                    'payment_required': True,
                    'requirements': requirements,
                    'session_id': session_id
                })
            }
            
        try:
            # Verify payment header
            verification = verify_payment(payment_header)
            
            if not verification.get('verified'):
                return {
                    'statusCode': 401,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': 'Invalid payment',
                        'session_id': session_id
                    })
                }
            
            # Process payment
            payment_result = process_x402_payment(payment_header, resource_id)
            
            if payment_result.get('success'):
                # Get resource data - replace with your actual resource retrieval logic
                resource_data = {
                    'id': resource_id,
                    'type': 'premium_content',
                    'content': 'This is premium content that required X402 payment to access',
                    'transaction_id': payment_result.get('transaction_id')
                }
                
                # Return resource with payment info
                return {
                    'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'paid': True,
                        'resource': resource_data,
                        'transaction_id': payment_result.get('transaction_id'),
                        'session_id': session_id
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': payment_result.get('error', 'Payment processing failed'),
                        'session_id': session_id
                    })
                }
                
        except Exception as e:
            logger.error(f"Error processing X402 payment: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Submit X402 payment for a resource
    elif method == 'POST' and path == '/x402/payment/submit':
        try:
            # Parse body
            body = json.loads(event.get('body', '{}'))
            resource_id = body.get('resource_id')
            wallet_address = body.get('wallet_address')
            amount = body.get('amount')
            currency = body.get('currency', 'ETH')
            user_id = body.get('user_id')
            
            if not resource_id or not wallet_address or not amount:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': 'Resource ID, wallet address and amount are required',
                        'session_id': session_id
                    })
                }
            
            # Check if wallet is connected in our session
            session_wallet = get_wallet_address(session_id, user_id)
            if not session_wallet or session_wallet != wallet_address:
                return {
                    'statusCode': 401,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': 'Wallet not connected or does not match session',
                        'session_id': session_id
                    })
                }
            
            # Create payment header
            payment_header = create_payment_header(wallet_address, amount, currency, resource_id)
            
            # Process payment
            payment_result = process_x402_payment(payment_header, resource_id)
            
            if payment_result.get('success'):
                return {
                    'statusCode': 200,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'transaction_id': payment_result.get('transaction_id'),
                        'status': payment_result.get('status'),
                        'payment_header': payment_header,  # Client can use this for subsequent requests
                        'session_id': session_id
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': False,
                        'error': payment_result.get('error', 'Payment processing failed'),
                        'session_id': session_id
                    })
                }
                
        except Exception as e:
            logger.error(f"Error submitting X402 payment: {e}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'session_id': session_id
                })
            }
    
    # Handle unknown paths
    else:
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': 'X402 endpoint not found',
                'session_id': session_id
            })
        }

def handle_combined_wallet_payment_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler that routes requests to appropriate CDP wallet or X402 payment handlers
    
    Args:
        event: The API Gateway event
        
    Returns:
        API Gateway response
    """
    path = event.get('path', '')
    
    # Route to appropriate handler based on path
    if path.startswith('/cdp/wallet/'):
        return handle_cdp_wallet_connection(event)
    elif path.startswith('/x402/'):
        return handle_x402_payment(event)
    else:
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': 'Endpoint not found'
            })
        }
