import json
import os
import requests
import uuid
from datetime import datetime
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

# Initialize the payment processor
payment_processor = X402PaymentProcessor()
config = load_payment_config()

class NFTPriceOracle:
    """
    Oracle for retrieving real-time NFT pricing information 
    from various marketplaces and APIs
    """
      def __init__(self):
        """Initialize the NFT price oracle"""
        # Get API keys from secure config
        self.api_keys = {
            'reservoir': config['nft_apis'].get('reservoir', ''),
            'opensea': config['nft_apis'].get('opensea', ''),
            'nftgo': config['nft_apis'].get('nftgo', '')
        }
        
        # Cache for price data to reduce API calls
        self.price_cache = {}
        self.cache_expiry = 300  # 5 minutes
    
    def get_collection_floor_price(self, collection_address, blockchain='ethereum'):
        """
        Get the current floor price for an NFT collection
        
        Args:
            collection_address: The contract address of the NFT collection
            blockchain: The blockchain network the collection is on
            
        Returns:
            dict: Floor price information
        """
        # Check cache first
        cache_key = f"{collection_address}_{blockchain}_floor"
        cached_data = self._check_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Try Reservoir API first
            if self.api_keys['reservoir']:
                data = self._fetch_reservoir_floor_price(collection_address, blockchain)
                if data and 'floorPrice' in data:
                    result = {
                        'floor_price': data['floorPrice'],
                        'currency': data.get('currency', 'ETH'),
                        'source': 'reservoir',
                        'timestamp': datetime.now().timestamp()
                    }
                    self._update_cache(cache_key, result)
                    return result
            
            # Fallback to OpenSea API
            if self.api_keys['opensea']:
                data = self._fetch_opensea_floor_price(collection_address)
                if data and 'stats' in data and 'floor_price' in data['stats']:
                    result = {
                        'floor_price': data['stats']['floor_price'],
                        'currency': 'ETH',
                        'source': 'opensea',
                        'timestamp': datetime.now().timestamp()
                    }
                    self._update_cache(cache_key, result)
                    return result
            
            # Final fallback to NFTGo
            if self.api_keys['nftgo']:
                data = self._fetch_nftgo_floor_price(collection_address)
                if data and 'data' in data and 'floorPrice' in data['data']:
                    result = {
                        'floor_price': data['data']['floorPrice'],
                        'currency': 'ETH',
                        'source': 'nftgo',
                        'timestamp': datetime.now().timestamp()
                    }
                    self._update_cache(cache_key, result)
                    return result
            
            # If all APIs fail, return default price
            return {
                'floor_price': 0.01,
                'currency': 'ETH',
                'source': 'default',
                'timestamp': datetime.now().timestamp()
            }
            
        except Exception as e:
            print(f"Error fetching floor price: {str(e)}")
            # Return default price on error
            return {
                'floor_price': 0.01,
                'currency': 'ETH',
                'source': 'default',
                'error': str(e),
                'timestamp': datetime.now().timestamp()
            }
    
    def get_nft_details_price(self, token_id, collection_address=None):
        """
        Calculate appropriate price for NFT details API access
        
        Args:
            token_id: The NFT token ID
            collection_address: The NFT collection address
            
        Returns:
            dict: Price information for NFT details access
        """
        try:
            base_price = 0.001  # Base price in ETH
            
            # If collection address is provided, adjust price based on floor
            if collection_address:
                floor_data = self.get_collection_floor_price(collection_address)
                floor_price = floor_data.get('floor_price', 0.01)
                
                # Scale price based on floor price (higher floor = higher price)
                if floor_price > 10:
                    adjusted_price = base_price * 10  # Premium collections
                elif floor_price > 1:
                    adjusted_price = base_price * 5   # Mid-tier collections
                else:
                    adjusted_price = base_price       # Standard collections
                    
                return {
                    'amount': round(adjusted_price, 6),
                    'currency': 'ETH',
                    'floor_price': floor_price,
                    'price_basis': 'floor',
                    'timestamp': datetime.now().timestamp()
                }
            
            # Without collection address, use default pricing
            return {
                'amount': base_price,
                'currency': 'ETH',
                'price_basis': 'default',
                'timestamp': datetime.now().timestamp()
            }
            
        except Exception as e:
            print(f"Error calculating NFT details price: {str(e)}")
            # Return default price on error
            return {
                'amount': 0.001,
                'currency': 'ETH',
                'price_basis': 'fallback',
                'error': str(e),
                'timestamp': datetime.now().timestamp()
            }
    
    def get_collection_analytics_price(self, collection_address, data_type='basic'):
        """
        Calculate appropriate price for collection analytics access
        
        Args:
            collection_address: The NFT collection address
            data_type: Type of analytics (basic, advanced, premium)
            
        Returns:
            dict: Price information for collection analytics access
        """
        try:
            # Base pricing by data type
            base_prices = {
                'basic': 0.005,      # Basic collection stats
                'advanced': 0.01,    # Advanced analytics
                'premium': 0.05      # Premium data and predictions
            }
            
            base_price = base_prices.get(data_type, 0.005)
            
            # Adjust based on collection floor price and volume
            floor_data = self.get_collection_floor_price(collection_address)
            floor_price = floor_data.get('floor_price', 0.01)
            
            # Get collection volume (or estimate)
            volume_data = self._get_collection_volume(collection_address)
            volume = volume_data.get('volume', 0)
            
            # Adjust price based on collection popularity
            price_multiplier = 1.0
            
            if volume > 1000:
                price_multiplier = 2.0  # High volume collection
            elif volume > 100:
                price_multiplier = 1.5  # Medium volume
                
            if floor_price > 10:
                price_multiplier *= 1.5  # Premium collection
                
            adjusted_price = base_price * price_multiplier
            
            return {
                'amount': round(adjusted_price, 6),
                'currency': 'ETH',
                'floor_price': floor_price,
                'volume': volume,
                'data_type': data_type,
                'price_basis': 'dynamic',
                'timestamp': datetime.now().timestamp()
            }
            
        except Exception as e:
            print(f"Error calculating collection analytics price: {str(e)}")
            # Return default price on error
            return {
                'amount': base_prices.get(data_type, 0.005),
                'currency': 'ETH',
                'data_type': data_type,
                'price_basis': 'fallback',
                'error': str(e),
                'timestamp': datetime.now().timestamp()
            }
    
    def _fetch_reservoir_floor_price(self, collection_address, blockchain='ethereum'):
        """Fetch floor price from Reservoir API"""
        try:
            url = f"https://api.reservoir.tools/collections/v5"
            params = {
                'id': collection_address,
                'limit': 1
            }
            headers = {
                'accept': '*/*',
                'x-api-key': self.api_keys['reservoir']
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'collections' in data and len(data['collections']) > 0:
                    collection = data['collections'][0]
                    return {
                        'floorPrice': collection.get('floorAsk', {}).get('price', {}).get('amount', {}).get('native', 0),
                        'currency': 'ETH'  # Reservoir uses native currency (ETH for Ethereum)
                    }
            
            return None
            
        except Exception as e:
            print(f"Reservoir API error: {str(e)}")
            return None
    
    def _fetch_opensea_floor_price(self, collection_address):
        """Fetch floor price from OpenSea API"""
        try:
            url = f"https://api.opensea.io/api/v1/asset_contract/{collection_address}"
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': self.api_keys['opensea']
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"OpenSea API error: {str(e)}")
            return None
    
    def _fetch_nftgo_floor_price(self, collection_address):
        """Fetch floor price from NFTGo API"""
        try:
            url = f"https://data-api.nftgo.io/eth/v1/collection/{collection_address}/metrics"
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': self.api_keys['nftgo']
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"NFTGo API error: {str(e)}")
            return None
    
    def _get_collection_volume(self, collection_address):
        """Get collection trading volume"""
        # In a real implementation, fetch this from an API
        # For now, return mock data
        return {
            'volume': 50,  # Default medium volume
            'currency': 'ETH'
        }
    
    def _check_cache(self, key):
        """Check if we have fresh cached data"""
        if key in self.price_cache:
            cached_item = self.price_cache[key]
            now = datetime.now().timestamp()
            
            # Return if cache is fresh
            if now - cached_item['timestamp'] < self.cache_expiry:
                return cached_item['data']
        
        return None
    
    def _update_cache(self, key, data):
        """Update the price cache"""
        self.price_cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }


class DynamicPricingAgent:
    """
    AI Agent integration for handling payments with dynamic pricing
    and interactive buttons
    """
    
    def __init__(self):
        """Initialize the payment agent"""
        self.supported_currencies = config['payment']['supported_currencies']
        self.default_currency = config['payment']['default_currency']
        self.price_oracle = NFTPriceOracle()
    
    def get_payment_options(self, resource_path, collection_address=None, token_id=None, data_type=None):
        """
        Get payment options with button actions for a resource,
        with pricing dynamically calculated based on NFT data
        
        Args:
            resource_path: Resource path being requested
            collection_address: NFT collection address (if applicable)
            token_id: NFT token ID (if applicable)
            data_type: Type of data being requested (basic, advanced, premium)
            
        Returns:
            dict: Payment options with button actions
        """
        try:
            # Calculate price based on resource and NFT data
            price_info = self._calculate_dynamic_price(
                resource_path=resource_path,
                collection_address=collection_address,
                token_id=token_id,
                data_type=data_type
            )
            
            if not price_info or 'amount' not in price_info:
                return {
                    "success": False,
                    "error": f"Could not calculate price for {resource_path}"
                }
                
            amount = price_info['amount']
            currency = price_info['currency']
            
            # Create a unique transaction ID
            transaction_id = f"tx_{uuid.uuid4().hex[:8]}"
            
            # Generate buttons for different payment actions
            buttons = [
                {
                    "text": f"Pay {amount} {currency}",
                    "action": "initiate_payment",
                    "payload": {
                        "transaction_id": transaction_id,
                        "amount": amount,
                        "currency": currency,
                        "resource": resource_path,
                        "collection_address": collection_address,
                        "token_id": token_id
                    }
                }
            ]
            
            # If there are multiple currencies, add options
            if len(self.supported_currencies) > 1:
                for alt_currency in self.supported_currencies:
                    if alt_currency != currency:
                        # Add alternative currency options
                        buttons.append({
                            "text": f"Pay with {alt_currency}",
                            "action": "change_currency",
                            "payload": {
                                "transaction_id": transaction_id,
                                "currency": alt_currency,
                                "resource": resource_path,
                                "collection_address": collection_address,
                                "token_id": token_id
                            }
                        })
            
            # Add pricing details to the response
            pricing_details = {
                "price_basis": price_info.get('price_basis', 'dynamic'),
                "timestamp": price_info.get('timestamp')
            }
            
            if 'floor_price' in price_info:
                pricing_details["floor_price"] = price_info['floor_price']
                
            if 'volume' in price_info:
                pricing_details["volume"] = price_info['volume']
                
            if 'data_type' in price_info:
                pricing_details["data_type"] = price_info['data_type']
            
            return {
                "success": True,
                "message": f"Payment required for {resource_path}",
                "amount": amount,
                "currency": currency,
                "buttons": buttons,
                "transaction_id": transaction_id,
                "pricing_details": pricing_details
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating payment options: {str(e)}"
            }
    
    def process_payment_action(self, action, payload):
        """
        Process payment action from agent button click
        
        Args:
            action: Action type (initiate_payment, change_currency, etc.)
            payload: Action payload with details
            
        Returns:
            dict: Action result
        """
        try:
            if action == "initiate_payment":
                return self.initiate_payment(
                    wallet_address=payload.get('wallet_address'),
                    amount=payload.get('amount'),
                    currency=payload.get('currency'),
                    resource=payload.get('resource'),
                    collection_address=payload.get('collection_address'),
                    token_id=payload.get('token_id'),
                    transaction_id=payload.get('transaction_id')
                )
            
            elif action == "change_currency":
                # Get price in the new currency
                resource_path = payload.get('resource')
                currency = payload.get('currency')
                collection_address = payload.get('collection_address')
                token_id = payload.get('token_id')
                data_type = payload.get('data_type')
                transaction_id = payload.get('transaction_id')
                
                # Calculate price in the new currency
                price_info = self._calculate_dynamic_price(
                    resource_path=resource_path,
                    collection_address=collection_address,
                    token_id=token_id,
                    data_type=data_type,
                    target_currency=currency
                )
                
                price = price_info['amount']
                
                return {
                    "success": True,
                    "message": f"Currency changed to {currency}",
                    "amount": price,
                    "currency": currency,
                    "transaction_id": transaction_id,
                    "buttons": [{
                        "text": f"Pay {price} {currency}",
                        "action": "initiate_payment",
                        "payload": {
                            "transaction_id": transaction_id,
                            "amount": price,
                            "currency": currency,
                            "resource": resource_path,
                            "collection_address": collection_address,
                            "token_id": token_id
                        }
                    }]
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing payment action: {str(e)}"
            }
    
    def initiate_payment(self, wallet_address, amount, currency, resource=None, 
                         collection_address=None, token_id=None, transaction_id=None):
        """
        Initiate payment automatically in the background
        
        Args:
            wallet_address: Recipient wallet address
            amount: Payment amount
            currency: Payment currency
            resource: Resource being purchased
            collection_address: NFT collection address (if applicable)
            token_id: NFT token ID (if applicable)
            transaction_id: Unique transaction ID
            
        Returns:
            dict: Payment result with notification
        """
        if not wallet_address:
            return {
                "success": False,
                "error": "Wallet address is required"
            }
            
        if not amount:
            return {
                "success": False,
                "error": "Payment amount is required"
            }
            
        # Process payment automatically in the background
        payment_result = payment_processor.settle_x402_payment({
            'from': 'system_wallet',
            'to': wallet_address,
            'amount': amount,
            'currency': currency,
            'resource': resource,
            'collection_address': collection_address,
            'token_id': token_id,
            'transaction_id': transaction_id
        })
        
        # Enhance the response with additional details
        payment_details = {
            'resource': resource,
            'amount': amount,
            'currency': currency
        }
        
        if collection_address:
            payment_details['collection_address'] = collection_address
            
        if token_id:
            payment_details['token_id'] = token_id
        
        # Add notification info for the agent to display
        payment_result['notification'] = {
            'show': True,
            'message': f"Payment of {amount} {currency} to {wallet_address} has been initiated.",
            'type': 'info'
        }
        
        # Add the payment details
        payment_result['payment_details'] = payment_details
            
        return payment_result
    
    def _calculate_dynamic_price(self, resource_path, collection_address=None, 
                                token_id=None, data_type=None, target_currency=None):
        """
        Calculate dynamic price based on resource and NFT data
        
        Args:
            resource_path: Resource path being requested
            collection_address: NFT collection address (if applicable)
            token_id: NFT token ID (if applicable)
            data_type: Type of data being requested
            target_currency: Target currency for conversion
            
        Returns:
            dict: Price information
        """
        # Determine resource type and calculate appropriate price
        if resource_path.startswith('api/nft/details'):
            # NFT details pricing
            price_info = self.price_oracle.get_nft_details_price(
                token_id=token_id,
                collection_address=collection_address
            )
        
        elif resource_path.startswith('api/collection'):
            # Collection analytics pricing
            price_info = self.price_oracle.get_collection_analytics_price(
                collection_address=collection_address,
                data_type=data_type or 'basic'
            )
            
        else:
            # Default resource pricing from config
            resource_prices = config['payment'].get('resource_prices', {})
            
            # Try to find exact match in config
            if resource_path in resource_prices:
                price_info = resource_prices[resource_path]
            else:
                # Use default pricing
                price_info = {
                    'amount': config['payment'].get('min_amount', 0.001),
                    'currency': self.default_currency,
                    'timestamp': datetime.now().timestamp()
                }
        
        # Convert currency if needed
        if target_currency and target_currency != price_info['currency']:
            price_info['amount'] = self._convert_currency(
                amount=price_info['amount'],
                from_currency=price_info['currency'],
                to_currency=target_currency
            )
            price_info['currency'] = target_currency
            
        return price_info
    
    def _convert_currency(self, amount, from_currency, to_currency):
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return amount
            
        # Simple conversion rates for demonstration
        conversion_rates = {
            "ETH_USDC": 3000,  # 1 ETH = 3000 USDC
            "ETH_USDT": 3000,  # 1 ETH = 3000 USDT
            "ETH_DAI": 3000,   # 1 ETH = 3000 DAI
            "USDC_ETH": 0.00033,  # 1 USDC = 0.00033 ETH
            "USDT_ETH": 0.00033,  # 1 USDT = 0.00033 ETH
            "DAI_ETH": 0.00033    # 1 DAI = 0.00033 ETH
        }
        
        conversion_key = f"{from_currency}_{to_currency}"
        
        if conversion_key in conversion_rates:
            converted_amount = amount * conversion_rates[conversion_key]
            
            # Round to appropriate decimal places
            if to_currency in ["USDC", "USDT", "DAI"]:
                return round(converted_amount, 2)
            else:
                return round(converted_amount, 6)
                
        # If conversion not found, return original amount
        return amount
