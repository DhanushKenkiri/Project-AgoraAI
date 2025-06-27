import json
import os
import time
import uuid
import base64
import boto3
from botocore.exceptions import ClientError
from utils.x402_processor import X402PaymentProcessor
try:
    from secure_payment_config import load_payment_config
except ImportError:
    import os
    import json
    # Fallback if secure_payment_config is not available
    def load_payment_config():
        """Fallback payment config if secure_payment_config is not available"""
        print("WARNING: Using fallback payment config due to import error")
        return {
            "x402": {
                "network": os.environ.get('NETWORK', 'base-sepolia'),
                "token_contract_address": os.environ.get('TOKEN_CONTRACT_ADDRESS', ''),
                "rpc_url": os.environ.get('RPC_URL', 'https://sepolia.base.org')
            },
            "cdp_wallet": {
                "app_id": os.environ.get('CDP_WALLET_APP_ID', '')
            },
            "nft_apis": {
                "reservoir": os.environ.get('RESERVOIR_API_KEY', ''),
                "opensea": os.environ.get('OPENSEA_API_KEY', ''),
                "nftgo": os.environ.get('NFTGO_API_KEY', '')
            },
            "payment": {
                "max_amount": float(os.environ.get('MAX_PAYMENT_AMOUNT', '10.0')),
                "min_amount": float(os.environ.get('MIN_PAYMENT_AMOUNT', '0.001')),
                "default_currency": os.environ.get('DEFAULT_CURRENCY', 'ETH'),
                "supported_currencies": os.environ.get('SUPPORTED_CURRENCIES', 'ETH,USDC,USDT,DAI').split(',')
            }
        }

# Initialize the X402 payment processor
x402_processor = X402PaymentProcessor()

def lambda_handler(event, context):
    """
    Main handler for X402 payment protocol integration
    
    This Lambda function implements the server-side components of the X402 protocol,
    acting as both a resource server and potentially a facilitator server.
    """
    try:
        # Log the incoming request (excluding sensitive data)
        print(f"Received payment request: {json.dumps({k: v for k, v in event.items() if k not in ['wallet_address', 'payment_header']})}")
        
        # Check if this is an HTTP request with payment header
        if 'headers' in event and 'X-PAYMENT' in event['headers']:
            return process_x402_payment_request(event)
        
        # Otherwise handle as a direct action request
        action = event.get('action', '')
        
        # Route to appropriate handler
        if action == 'connect_wallet':
            return handle_wallet_connection(event)
        elif action == 'initiate_payment':
            return initiate_payment(event)
        elif action == 'check_status':
            return check_payment_status(event)
        elif action == 'confirm_payment':
            return confirm_payment(event)
        elif action == 'payment_required_response':
            return generate_payment_required_response(event)
        else:
            return {
                'success': False,
                'error': f"Unknown action: {action}"
            }
    
    except Exception as e:
        print(f"Error processing payment request: {str(e)}")
        return {
            'success': False,
            'error': f"Error processing payment request: {str(e)}"
        }

def process_x402_payment_request(event):
    """
    Process an HTTP request with X402 payment header
    
    Args:
        event: API Gateway event with X402 headers
        
    Returns:
        dict: API Gateway response with status code and body
    """
    try:
        # Extract the payment header
        payment_header = event['headers']['X-PAYMENT']
        
        # Extract the resource path
        resource_path = event.get('path', '/premium-nft-data')
        
        # Verify the payment header
        verification_result = x402_processor.verify_x402_payment(payment_header, resource_path)
        
        if not verification_result['isValid']:
            # If payment is invalid, return 402 with error message
            return x402_processor.generate_payment_required_response(
                resource_path, 
                f"Invalid payment: {verification_result['invalidReason']}"
            )
        
        # If payment is valid, settle it
        if verification_result.get('requiresSettlement', True):
            settlement_result = x402_processor.settle_x402_payment(verification_result['paymentInfo'])
            
            if not settlement_result['success']:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f"Payment settlement failed: {settlement_result.get('error', 'Unknown error')}"
                    })
                }
            
            # Generate payment response header
            payment_response_header = x402_processor.generate_payment_response_header(settlement_result)
            
            # Return successful response with payment response header
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'X-PAYMENT-RESPONSE': payment_response_header
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment_id': settlement_result['payment_id'],
                    'transaction_hash': settlement_result['tx_hash'],
                    'explorer_url': settlement_result['explorer_url']
                })
            }
        else:
            # Payment was valid but doesn't require settlement
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Payment verified successfully'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error processing payment request: {str(e)}"
            })
        }

def handle_wallet_connection(event):
    """Process wallet connection request"""
    wallet_address = event.get('wallet_address')
    
    if not wallet_address:
        # If no wallet address provided, create connection URL
        connection_info = x402_processor.create_wallet_connection_url(
            callback_url=event.get('callback_url')
        )
        
        return {
            'success': True,
            'connection_url': connection_info['connection_url'],
            'state': connection_info['state'],
            'qr_data': connection_info.get('qr_data')
        }
    
    # Otherwise store the wallet connection
    result = x402_processor.store_wallet_connection(
        wallet_address=wallet_address,
        state=event.get('state')
    )
    
    return result

def generate_payment_required_response(event):
    """Generate a 402 Payment Required response for a resource"""
    resource_path = event.get('resource', '/premium-nft-data')
    description = event.get('description')
    
    response = x402_processor.generate_payment_required_response(resource_path, description)
    
    # Convert API Gateway response format to Lambda direct invocation format
    if 'statusCode' in response and 'body' in response:
        body = json.loads(response['body'])
        return {
            'success': True,
            'paymentRequirements': body
        }
    
    return response

def initiate_payment(event):
    """Initiate a payment to a user-specified address"""
    wallet_address = event.get('wallet_address')
    amount = event.get('amount')
    currency = event.get('currency', 'ETH')
    
    # Auto payment is now always enabled by default
    
    if not wallet_address:
        return {
            'success': False,
            'error': 'Wallet address is required'
        }

    if not amount:
        return {
            'success': False,
            'error': 'Payment amount is required'
        }

    # Process payment automatically in the background
    payment_result = x402_processor.settle_x402_payment({
        'from': 'system_wallet',  # System wallet address for automatic payments
        'to': wallet_address,
        'amount': amount,
        'currency': currency
    })
    
    # Add notification info to the response
    payment_result['notification'] = {
        'show': True,
        'message': f"Payment of {amount} {currency} to {wallet_address} has been initiated.",
        'type': 'info'
    }
    
    return payment_result

def check_payment_status(event):
    """Check the status of a payment"""
    payment_id = event.get('payment_id')
    
    if not payment_id:
        return {
            'success': False,
            'error': 'Payment ID is required'
        }
    
    return x402_processor.check_payment_status(payment_id)

def confirm_payment(event):
    """Confirm a completed payment"""
    payment_id = event.get('payment_id')
    transaction_hash = event.get('transaction_hash')
    
    if not payment_id:
        return {
            'success': False,
            'error': 'Payment ID is required'
        }
    
    # Get current payment status
    status_result = x402_processor.check_payment_status(payment_id)
    
    if not status_result['success']:
        return status_result
    
    # If payment already completed, return status
    if status_result['status'] == 'completed':
        return status_result
    
    # In a real implementation, you would verify the transaction on the blockchain
    # and update the payment status
    
    # For now, just return the current status
    return status_result

def store_transaction_record(transaction_data):
    """
    Store transaction record in DynamoDB for audit and tracking
    """
    try:
        # Add timestamp for tracking
        if 'timestamp' not in transaction_data:
            transaction_data['timestamp'] = int(time.time())
            
        if 'created_at' not in transaction_data:
            transaction_data['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Store the transaction using the X402 processor
        return x402_processor._store_transaction_record(transaction_data)
    except Exception as e:
        print(f"Error storing transaction: {str(e)}")
        return False

def handle_payment_request(event):
    """
    Handle payment initiation requests from API Gateway or Bedrock agent
    
    This function processes payment requests and initiates X402 payments,
    supporting both API Gateway events and Bedrock agent parameters.
    
    Args:
        event: API Gateway or parameter dictionary from Bedrock agent
        
    Returns:
        dict: Payment initiation result
    """
    try:
        # Parse request body for API Gateway events
        if 'body' in event:
            body = event['body']
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    return {
                        'success': False,
                        'error': 'Invalid JSON in request body'
                    }
            
            # Extract payment parameters
            amount = body.get('amount')
            currency = body.get('currency', os.environ.get('DEFAULT_CURRENCY', 'ETH'))
            payment_reason = body.get('paymentReason')
            
            # Extract X402-specific parameters
            x402_params = body.get('x402', {})
            wallet_address = x402_params.get('wallet_address')
            contract_address = x402_params.get('contract_address')
            redirect_url = x402_params.get('redirect_url')
        
        # For direct parameter invocation (e.g. from Bedrock)
        else:
            # Extract directly from event
            amount = event.get('amount')
            currency = event.get('currency', os.environ.get('DEFAULT_CURRENCY', 'ETH'))
            payment_reason = event.get('payment_reason')
            wallet_address = event.get('wallet_address')
            contract_address = event.get('contract_address')
            redirect_url = event.get('redirect_url')
        
        # Validate required parameters
        if not amount:
            return {
                'success': False,
                'error': 'Amount is required'
            }
            
        if not wallet_address:
            return {
                'success': False,
                'error': 'Wallet address is required'
            }
            
        # Check payment amount limits
        try:
            amount_float = float(amount)
            min_amount = float(os.environ.get('MIN_PAYMENT_AMOUNT', '0.001'))
            max_amount = float(os.environ.get('MAX_PAYMENT_AMOUNT', '10.0'))
            
            if amount_float < min_amount:
                return {
                    'success': False, 
                    'error': f'Payment amount too small. Minimum allowed: {min_amount} {currency}'
                }
                
            if amount_float > max_amount:
                return {
                    'success': False,
                    'error': f'Payment amount too large. Maximum allowed: {max_amount} {currency}'
                }
        except ValueError:
            return {
                'success': False,
                'error': 'Invalid payment amount'
            }
            
        # Load payment configuration
        payment_config = load_payment_config()
            
        # Initialize payment with X402 processor
        payment_result = x402_processor.initiate_payment(
            amount=amount,
            currency=currency,
            wallet_address=wallet_address,
            contract_address=contract_address or payment_config.get('token_contract_address'),
            payment_reason=payment_reason or 'NFT Data Access',
            redirect_url=redirect_url
        )
        
        # Store transaction record
        transaction_data = {
            'transaction_id': payment_result.get('payment_id'),
            'wallet_address': wallet_address,
            'amount': amount,
            'currency': currency,
            'payment_reason': payment_reason,
            'status': 'initiated'
        }
        
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions'))
            table.put_item(Item=transaction_data)
        except Exception as db_error:
            print(f"Warning: Failed to store transaction data: {str(db_error)}")
        
        # Return payment initiation result
        return {
            'success': True,
            'payment_id': payment_result.get('payment_id'),
            'payment_url': payment_result.get('payment_url'),
            'qr_code': payment_result.get('qr_code'),
            'expiration': payment_result.get('expiration'),
            'amount': amount,
            'currency': currency
        }
        
    except Exception as e:
        print(f"Error handling payment request: {str(e)}")
        return {
            'success': False,
            'error': f'Payment initialization failed: {str(e)}'
        }
