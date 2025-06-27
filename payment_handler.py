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

def generate_nonce():
    """Generate a unique nonce for transaction security"""
    return str(uuid.uuid4())

def verify_transaction_status(payment_id):
    """Verify transaction status with X402 payment processor"""
    try:
        # Use the X402 processor to check payment status
        return x402_processor.check_payment_status(payment_id)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def store_transaction_record(transaction_data):
    """Store transaction record in DynamoDB for audit and tracking"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions'))
        
        # Add timestamp for tracking
        transaction_data['timestamp'] = int(time.time())
        transaction_data['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Store in DynamoDB
        table.put_item(Item=transaction_data)
        return True
    except ClientError as e:
        print(f"Error storing transaction: {str(e)}")
        return False

def encrypt_sensitive_data(data):
    """Encrypt sensitive data using AWS KMS"""
    try:
        kms = boto3.client('kms')
        key_id = os.environ.get('KMS_KEY_ID')
        
        if not key_id:
            print("Warning: KMS_KEY_ID not set, skipping encryption")
            return data
            
        response = kms.encrypt(
            KeyId=key_id,
            Plaintext=json.dumps(data).encode()
        )
        return {
            'encrypted': True,
            'data': response['CiphertextBlob'].hex()
        }
    except Exception as e:
        print(f"Error encrypting data: {str(e)}")
        # Fall back to returning unencrypted data if encryption fails
        # In production, you might want to fail instead
        return data

def validate_request(event):
    """Validate incoming requests to prevent attacks"""
    required_fields = ['wallet_address', 'action']
    
    # Check required fields
    for field in required_fields:
        if field not in event:
            return False, f"Missing required field: {field}"
    
    # Validate wallet address format (simplified check)
    wallet_address = event.get('wallet_address')
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        return False, "Invalid wallet address format"
        
    # Validate action is permitted
    allowed_actions = ['connect_wallet', 'initiate_payment', 'confirm_payment', 'check_status']
    if event.get('action') not in allowed_actions:
        return False, "Invalid action requested"
    
    return True, "Valid request"

def handle_wallet_connection(wallet_data):
    """Process wallet connection request"""
    # Generate a session token for the wallet connection
    session_token = str(uuid.uuid4())
    
    # In a real implementation, you would validate the wallet signature
    # to prove ownership of the private key
    
    return {
        'success': True,
        'wallet_address': wallet_data.get('wallet_address'),
        'session_token': session_token,
        'expiration': int(time.time()) + 3600  # 1 hour expiration
    }

def initiate_payment(payment_data):
    """Initiate a payment through X402 gateway"""
    try:
        # Extract payment details
        wallet_address = payment_data.get('wallet_address')
        amount = payment_data.get('amount')
        currency = payment_data.get('currency', 'ETH')
        nft_contract = payment_data.get('nft_contract')
        nft_token_id = payment_data.get('nft_token_id')
        
        if not all([wallet_address, amount, nft_contract]):
            return {
                'success': False,
                'error': 'Missing required payment parameters'
            }
        
        # Generate a unique payment ID
        payment_id = f"pmt_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Create a payment intent
        # In production, this would involve an actual API call to X402
        payment_intent = {
            'payment_id': payment_id,
            'wallet_address': wallet_address,
            'amount': amount,
            'currency': currency,
            'nft_contract': nft_contract,
            'nft_token_id': nft_token_id,
            'status': 'pending',
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Store the payment intent
        store_transaction_record(payment_intent)
        
        # In a real implementation, you would make an API call to X402
        # to create the actual payment intent
        
        return {
            'success': True,
            'payment_id': payment_id,
            'status': 'pending',
            'next_action': 'confirm_payment',
            'payment_url': f"cdp://pay/{payment_id}?amount={amount}&currency={currency}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def confirm_payment(confirmation_data):
    """Confirm a payment has been completed"""
    try:
        payment_id = confirmation_data.get('payment_id')
        transaction_hash = confirmation_data.get('transaction_hash')
        
        if not payment_id or not transaction_hash:
            return {
                'success': False,
                'error': 'Missing payment ID or transaction hash'
            }
            
        # In production, verify the transaction on-chain
        # For this example, we'll just simulate verification
        
        # Update transaction record
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions'))
        
        # Get existing record
        response = table.get_item(Key={'payment_id': payment_id})
        if 'Item' not in response:
            return {
                'success': False,
                'error': 'Payment not found'
            }
            
        payment_record = response['Item']
        payment_record['status'] = 'completed'
        payment_record['transaction_hash'] = transaction_hash
        payment_record['completed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update record
        table.put_item(Item=payment_record)
        
        return {
            'success': True,
            'payment_id': payment_id,
            'status': 'completed',
            'transaction_hash': transaction_hash
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def check_payment_status(status_request):
    """Check the status of a payment"""
    try:
        payment_id = status_request.get('payment_id')
        
        if not payment_id:
            return {
                'success': False,
                'error': 'Missing payment ID'
            }
            
        # Query DynamoDB for payment status
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions'))
        
        response = table.get_item(Key={'payment_id': payment_id})
        if 'Item' not in response:
            return {
                'success': False,
                'error': 'Payment not found'
            }
            
        payment_record = response['Item']
        
        return {
            'success': True,
            'payment_id': payment_id,
            'status': payment_record.get('status', 'unknown'),
            'created_at': payment_record.get('created_at'),
            'completed_at': payment_record.get('completed_at', None),
            'transaction_hash': payment_record.get('transaction_hash', None)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for CDP wallet integration and X402 payment processing
    """
    try:
        print(f"Received payment event: {json.dumps(event)}")
        
        # Validate the request
        is_valid, validation_msg = validate_request(event)
        if not is_valid:
            return {
                'success': False,
                'error': validation_msg
            }
        
        # Extract the action from the request
        action = event.get('action')
        
        # Handle different payment actions
        if action == 'connect_wallet':
            result = handle_wallet_connection(event)
        elif action == 'initiate_payment':
            result = initiate_payment(event)
        elif action == 'confirm_payment':
            result = confirm_payment(event)
        elif action == 'check_status':
            result = check_payment_status(event)
        else:
            result = {
                'success': False,
                'error': f"Unsupported action: {action}"
            }
            
        # Add security headers and audit info
        result['request_id'] = context.aws_request_id
        result['timestamp'] = int(time.time())
        
        # Return the result
        return result
        
    except Exception as e:
        print(f"Error processing payment request: {str(e)}")
        return {
            'success': False,
            'error': 'Internal server error while processing payment',
            'message': str(e)
        }
