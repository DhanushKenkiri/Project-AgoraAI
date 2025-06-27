import json
import time
import uuid
import os
import base64
import boto3
from urllib.parse import urlencode
from botocore.exceptions import ClientError
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
            },
            "aws": {
                "transaction_table": os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions'),
                "wallet_sessions_table": os.environ.get('WALLET_SESSIONS_TABLE_NAME', 'NFTWalletSessions'),
                "kms_key_id": os.environ.get('KMS_KEY_ID', ''),
                "region": os.environ.get('AWS_REGION', 'us-east-1')
            }
        }

class X402PaymentProcessor:
    """
    Implementation of the X402 payment protocol for NFT transactions
    
    This class handles both resource server and facilitator server roles
    in the X402 payment protocol specification.
    """
    def __init__(self):
        """Initialize the X402 payment processor with configuration"""
        self.config = load_payment_config()
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config.get('aws', {}).get('region', 'us-east-1'))
        
        # Get table names, using defaults if not configured
        transaction_table = self.config.get('aws', {}).get('transaction_table', 'NFTPaymentTransactions')
        wallet_sessions_table = self.config.get('aws', {}).get('wallet_sessions_table', 'NFTWalletSessions')
        
        # Set tables or create mocks if running locally/testing
        try:
            self.payment_table = self.dynamodb.Table(transaction_table)
            self.wallet_table = self.dynamodb.Table(wallet_sessions_table)
        except Exception as e:
            print(f"Warning: Unable to access DynamoDB tables: {str(e)}. Using mock tables for local testing.")
            # Create mock table handlers for local testing
            class MockTable:
                def __init__(self, name):
                    self.name = name
                    self.items = {}
                
                def put_item(self, Item):
                    item_id = Item.get('id', str(uuid.uuid4()))
                    self.items[item_id] = Item
                    return {'ResponseMetadata': {'HTTPStatusCode': 200}}
                
                def get_item(self, Key):
                    item_id = Key.get('id')
                    return {'Item': self.items.get(item_id, {})} if item_id in self.items else {'ResponseMetadata': {'HTTPStatusCode': 404}}
                
                def query(self, **kwargs):
                    return {'Items': list(self.items.values()), 'Count': len(self.items)}
                
            self.payment_table = MockTable(transaction_table)
            self.wallet_table = MockTable(wallet_sessions_table)
        
    def generate_payment_required_response(self, resource_path, description=None):
        """
        Generate a 402 Payment Required response according to X402 protocol specs
        
        Args:
            resource_path: The resource path being requested
            description: Optional description of the resource
            
        Returns:
            dict: X402 Payment Required Response object
        """
        # Get the price for this resource
        price_info = self._get_resource_price(resource_path)
        amount = price_info['amount']
        currency = price_info['currency']
        
        # Set description if not provided
        if not description:
            description = f"Payment required for {resource_path}"
        
        # Convert amount to atomic units based on currency
        atomic_amount = self._convert_to_atomic_units(amount, currency)
        
        # Get the payment address from config
        payment_address = self.config['x402']['payment_address']
        
        # Get token contract address if paying in an ERC-20 token
        token_contract = None
        if currency != 'ETH':
            token_contract = self.config['x402']['token_contract_address']
            if not token_contract:
                # Return error since token payment requested but no contract configured
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f"Payment in {currency} requested but no token contract configured"
                    })
                }
        
        # Build the payment requirements object according to X402 protocol spec
        payment_requirements = {
            'scheme': 'exact',  # Using the exact payment scheme
            'network': self.config['x402']['network'],
            'maxAmountRequired': atomic_amount,
            'resource': resource_path,
            'description': description,
            'mimeType': 'application/json',
            'payTo': payment_address,
            'maxTimeoutSeconds': 300,  # 5 minutes to complete the payment
            'asset': token_contract or '',  # Empty for ETH, contract address for tokens
            'extra': {
                'name': 'NFT Data Access',
                'version': '1'
            }
        }
        
        # Build the full payment required response
        payment_response = {
            'x402Version': 1,
            'accepts': [payment_requirements],
            'error': None
        }
        
        return {
            'statusCode': 402,  # Payment Required
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps(payment_response)
        }
    
    def verify_x402_payment(self, payment_header, resource_path):
        """
        Verify an X402 payment header
        
        Args:
            payment_header: Base64 encoded X402 payment header
            resource_path: Resource path being requested
            
        Returns:
            dict: Verification result with isValid flag
        """
        try:
            # Decode the base64 payment header
            decoded_header = base64.b64decode(payment_header).decode('utf-8')
            payment_data = json.loads(decoded_header)
            
            # Extract basic payment data
            scheme = payment_data.get('scheme')
            network = payment_data.get('network')
            version = payment_data.get('x402Version')
            payload = payment_data.get('payload')
            
            # Validate scheme and network
            if scheme != 'exact':
                return {'isValid': False, 'invalidReason': 'Unsupported payment scheme'}
                
            if network != self.config['x402']['network']:
                return {'isValid': False, 'invalidReason': f"Unsupported network: {network}"}
            
            # Validate version
            if version != 1:
                return {'isValid': False, 'invalidReason': f"Unsupported x402 version: {version}"}
            
            # Validate payload exists
            if not payload:
                return {'isValid': False, 'invalidReason': 'Missing payload in payment header'}
            
            # Get price requirements for this resource
            price_info = self._get_resource_price(resource_path)
            required_amount = self._convert_to_atomic_units(price_info['amount'], price_info['currency'])
            
            # Verify payment type
            payment_type = payload.get('type')
            
            if payment_type == 'native':  # ETH payment
                # Verify sender address
                from_address = payload.get('from')
                if not from_address or not from_address.startswith('0x'):
                    return {'isValid': False, 'invalidReason': 'Invalid sender address'}
                
                # Verify recipient address
                to_address = payload.get('to')
                if to_address != self.config['x402']['payment_address']:
                    return {'isValid': False, 'invalidReason': 'Invalid recipient address'}
                
                # Verify amount
                amount = payload.get('amount')
                if not amount or int(amount) < int(required_amount):
                    return {'isValid': False, 'invalidReason': f"Insufficient payment amount: {amount} < {required_amount}"}
                
                # Verify timestamp is recent
                timestamp = payload.get('timestamp', 0)
                current_time = int(time.time())
                if current_time - timestamp > 300:  # 5 minutes
                    return {'isValid': False, 'invalidReason': 'Payment timestamp expired'}
                
                # Verify signature (simplified validation - in production you'd verify on chain)
                signature = payload.get('signature')
                if not signature:
                    return {'isValid': False, 'invalidReason': 'Missing payment signature'}
                
                # In a real implementation, you'd verify the signature cryptographically
                # For now, we'll assume it's valid if it exists
                
                return {
                    'isValid': True,
                    'requiresSettlement': True,
                    'paymentInfo': {
                        'from': from_address,
                        'to': to_address,
                        'amount': amount,
                        'currency': 'ETH',
                        'timestamp': timestamp
                    }
                }
                
            elif payment_type == 'erc20-3009':  # ERC-20 payment using EIP-3009
                # Verify token address
                token = payload.get('token')
                if token != self.config['x402']['token_contract_address']:
                    return {'isValid': False, 'invalidReason': 'Invalid token contract address'}
                
                # Verify sender address
                from_address = payload.get('from')
                if not from_address or not from_address.startswith('0x'):
                    return {'isValid': False, 'invalidReason': 'Invalid sender address'}
                
                # Verify recipient address
                to_address = payload.get('to')
                if to_address != self.config['x402']['payment_address']:
                    return {'isValid': False, 'invalidReason': 'Invalid recipient address'}
                
                # Verify amount
                value = payload.get('value')
                if not value or int(value) < int(required_amount):
                    return {'isValid': False, 'invalidReason': f"Insufficient payment amount: {value} < {required_amount}"}
                
                # Verify validity period
                valid_after = payload.get('validAfter', 0)
                valid_before = payload.get('validBefore', 0)
                current_time = int(time.time())
                
                if current_time < valid_after:
                    return {'isValid': False, 'invalidReason': 'Payment not yet valid'}
                    
                if current_time > valid_before:
                    return {'isValid': False, 'invalidReason': 'Payment validity expired'}
                
                # Verify signature exists
                signature = payload.get('signature')
                if not signature:
                    return {'isValid': False, 'invalidReason': 'Missing payment signature'}
                
                # In a real implementation, you'd verify the signature cryptographically
                # For now, we'll assume it's valid if it exists
                
                # Get currency from token address - simplified example
                currency = 'USDC'  # This would actually be determined by the token contract
                
                return {
                    'isValid': True,
                    'requiresSettlement': True,
                    'paymentInfo': {
                        'from': from_address,
                        'to': to_address,
                        'amount': value,
                        'currency': currency,
                        'token': token,
                        'timestamp': valid_after
                    }
                }
            
            else:
                return {'isValid': False, 'invalidReason': f"Unsupported payment type: {payment_type}"}
                
        except Exception as e:
            return {'isValid': False, 'invalidReason': f"Error verifying payment: {str(e)}"}
    
    def settle_x402_payment(self, payment_info):
        """
        Settle an X402 payment on the blockchain
        
        Args:
            payment_info: Payment information from verification step
            
        Returns:
            dict: Settlement result with success flag and transaction hash
        """
        try:
            # Generate a payment ID
            payment_id = f"x402_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # In a real implementation, you would:
            # 1. For native ETH transfers: Submit the signed transaction to the blockchain
            # 2. For ERC-20 EIP-3009: Call the transferWithAuthorization function on the token contract
            
            # For now, we'll simulate a successful settlement
            tx_hash = f"0x{uuid.uuid4().hex}"
            
            # Store the payment record
            self._store_transaction_record({
                'payment_id': payment_id,
                'tx_hash': tx_hash,
                'from_address': payment_info['from'],
                'to_address': payment_info['to'],
                'amount': payment_info['amount'],
                'currency': payment_info['currency'],
                'timestamp': payment_info.get('timestamp', int(time.time())),
                'network': self.config['x402']['network'],
                'status': 'completed',
                'created_at': int(time.time())
            })
            
            # Return settlement information
            return {
                'success': True,
                'payment_id': payment_id,
                'tx_hash': tx_hash,
                'network': self.config['x402']['network'],
                'explorer_url': f"{self.config['blockchain']['explorer_url_prefix']}{tx_hash}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error settling payment: {str(e)}"
            }
    
    def create_wallet_connection_url(self, callback_url=None):
        """
        Create a CDP wallet connection URL
        
        Args:
            callback_url: URL to redirect after wallet connection
            
        Returns:
            dict: Connection URL and state parameter
        """
        # Generate a unique state parameter for security
        state = str(uuid.uuid4())
        
        # Get callback URL from parameter or config
        redirect_url = callback_url or self.config['cdp_wallet']['redirect_url']
        
        # Build parameters for CDP wallet deeplink
        params = {
            'callback': redirect_url,
            'state': state,
            'timestamp': int(time.time())
        }
        
        # Generate the connection URL
        connect_url = f"cdp://connect?{urlencode(params)}"
        
        return {
            'connection_url': connect_url,
            'state': state,
            'qr_data': connect_url  # For generating QR code if needed
        }
    
    def store_wallet_connection(self, wallet_address, state=None):
        """
        Store a wallet connection in the database
        
        Args:
            wallet_address: User's wallet address
            state: Optional state parameter from connection request
            
        Returns:
            dict: Connection information
        """
        try:
            # Validate wallet address
            if not wallet_address or not wallet_address.startswith('0x') or len(wallet_address) != 42:
                return {
                    'success': False,
                    'error': 'Invalid wallet address format'
                }
            
            # Generate a session token
            session_token = str(uuid.uuid4())
            
            # Create expiration time
            expiration = int(time.time()) + self.config['security']['session_expiry']
            
            # Store session in DynamoDB
            self.wallet_table.put_item(
                Item={
                    'wallet_address': wallet_address,
                    'session_token': session_token,
                    'state': state,
                    'created_at': int(time.time()),
                    'expires_at': expiration,
                    'status': 'active'
                }
            )
            
            return {
                'success': True,
                'wallet_address': wallet_address,
                'session_token': session_token,
                'expires_at': expiration
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error storing wallet connection: {str(e)}"
            }
    
    def create_payment_url(self, wallet_address, amount, currency='ETH'):
        """Create a payment URL for user-specified transactions"""
        try:
            payment_id = f"x402_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            payment_address = wallet_address  # Use user-specified address
            network = self.config['x402']['network']

            params = {
                'recipient': payment_address,
                'amount': amount,
                'currency': currency,
                'reference': payment_id,
                'network': network,
                'callback': self.config['cdp_wallet']['redirect_url']
            }

            payment_url = f"cdp://pay?{urlencode(params)}"

            self._store_transaction_record({
                'payment_id': payment_id,
                'wallet_address': wallet_address,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'created_at': int(time.time()),
                'network': network
            })

            return {
                'success': True,
                'payment_id': payment_id,
                'payment_url': payment_url,
                'status': 'pending',
                'network': network
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Error creating payment URL: {str(e)}"
            }
    
    def check_payment_status(self, payment_id):
        """
        Check the status of a payment
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            dict: Payment status information
        """
        try:
            # Get payment record from DynamoDB
            response = self.payment_table.get_item(Key={'payment_id': payment_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Payment not found'
                }
                
            payment = response['Item']
            
            # Check if transaction hash exists
            tx_hash = payment.get('tx_hash')
            explorer_url = None
            
            if tx_hash:
                explorer_url = f"{self.config['blockchain']['explorer_url_prefix']}{tx_hash}"
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': payment.get('status', 'unknown'),
                'amount': payment.get('amount'),
                'currency': payment.get('currency'),
                'wallet_address': payment.get('wallet_address'),
                'transaction_hash': tx_hash,
                'created_at': payment.get('created_at'),
                'completed_at': payment.get('completed_at'),
                'explorer_url': explorer_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking payment status: {str(e)}"
            }
    
    def generate_payment_response_header(self, settlement_result):
        """
        Generate X-PAYMENT-RESPONSE header value
        
        Args:
            settlement_result: Result from payment settlement
            
        Returns:
            str: Base64 encoded payment response header
        """
        response_data = {
            'success': settlement_result.get('success'),
            'txHash': settlement_result.get('tx_hash'),
            'networkId': settlement_result.get('network'),
            'paymentId': settlement_result.get('payment_id')
        }
        
        # Base64 encode the JSON response
        encoded_response = base64.b64encode(
            json.dumps(response_data).encode()
        ).decode()
        
        return encoded_response
    
    def _convert_to_atomic_units(self, amount, currency):
        """
        Convert amount to atomic units based on currency
        
        Args:
            amount: Amount in decimal units
            currency: Currency code
            
        Returns:
            str: Amount in atomic units as a string
        """
        if currency == 'ETH':
            # Convert ETH to wei (1 ETH = 10^18 wei)
            return str(int(float(amount) * 10**18))
        elif currency == 'USDC' or currency == 'USDT':
            # Convert to atomic units (1 USDC/USDT = 10^6 units)
            return str(int(float(amount) * 10**6))
        else:
            # Default to 18 decimals for other ERC-20 tokens
            return str(int(float(amount) * 10**18))
    
    def _get_resource_price(self, resource_path):
        """
        Get the price for a resource
        
        Args:
            resource_path: Resource path
            
        Returns:
            dict: Price information with amount and currency
        """
        # Get resource prices from config
        resource_prices = self.config['payment'].get('resource_prices', {})
        
        # Check if we have a price for this specific resource
        if resource_path in resource_prices:
            return resource_prices[resource_path]
        
        # If no specific price found, return default
        return {
            'amount': self.config['payment'].get('min_amount', 0.001),
            'currency': self.config['payment'].get('default_currency', 'ETH')
        }
    
    def _store_transaction_record(self, transaction_data):
        """
        Store transaction record in DynamoDB
        
        Args:
            transaction_data: Transaction data to store
            
        Returns:
            bool: Success flag
        """
        try:
            # Store in DynamoDB
            self.payment_table.put_item(Item=transaction_data)
            return True
        except Exception as e:
            print(f"Error storing transaction: {str(e)}")
            return False
