import json
import os
import uuid
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

class PaymentAgent:
    """
    AI Agent integration for handling payments with interactive buttons
    """
    
    def __init__(self):
        """Initialize the payment agent"""
        self.supported_currencies = config['payment']['supported_currencies']
        self.default_currency = config['payment']['default_currency']
    
    def get_payment_options(self, resource_path, user_id=None):
        """
        Get payment options with button actions for a resource
        
        Args:
            resource_path: Resource path being requested
            user_id: Optional user identifier for tracking
            
        Returns:
            dict: Payment options with button actions
        """
        try:
            # Get the price for this resource
            price_info = self._get_resource_price(resource_path)
            
            if not price_info:
                return {
                    "success": False,
                    "error": f"No pricing information available for {resource_path}"
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
                        "resource": resource_path
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
                                "resource": resource_path
                            }
                        })
            
            return {
                "success": True,
                "message": f"Payment required for {resource_path}",
                "amount": amount,
                "currency": currency,
                "buttons": buttons,
                "transaction_id": transaction_id
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
                    transaction_id=payload.get('transaction_id')
                )
            
            elif action == "change_currency":
                # Get price in the new currency
                resource_path = payload.get('resource')
                currency = payload.get('currency')
                transaction_id = payload.get('transaction_id')
                
                # Recalculate price in new currency
                price = self._convert_price_to_currency(resource_path, currency)
                
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
                            "resource": resource_path
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
    
    def initiate_payment(self, wallet_address, amount, currency, resource=None, transaction_id=None):
        """
        Initiate payment automatically in the background
        
        Args:
            wallet_address: Recipient wallet address
            amount: Payment amount
            currency: Payment currency
            resource: Resource being purchased
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
            'transaction_id': transaction_id
        })
        
        # Add notification info for the agent to display
        payment_result['notification'] = {
            'show': True,
            'message': f"Payment of {amount} {currency} to {wallet_address} has been initiated.",
            'type': 'info'
        }
        
        # Add the resource information for tracking
        if resource:
            payment_result['resource'] = resource
            
        return payment_result
    
    def _get_resource_price(self, resource_path):
        """Get the price for a resource from configuration"""
        resource_prices = config['payment'].get('resource_prices', {})
        
        # Try to find exact match
        if resource_path in resource_prices:
            return resource_prices[resource_path]
        
        # Try to find a pattern match
        for path, price_info in resource_prices.items():
            if resource_path.startswith(path):
                return price_info
        
        # Return default price if no match found
        return {
            "amount": config['payment'].get('min_amount', 0.001),
            "currency": self.default_currency
        }
    
    def _convert_price_to_currency(self, resource_path, target_currency):
        """Convert price to different currency"""
        # In a real implementation, you would use exchange rates
        # For now, use simple conversion factors
        
        price_info = self._get_resource_price(resource_path)
        original_amount = price_info['amount']
        original_currency = price_info['currency']
        
        if original_currency == target_currency:
            return original_amount
            
        # Simple conversion rates for demonstration
        conversion_rates = {
            "ETH_USDC": 3000,  # 1 ETH = 3000 USDC
            "ETH_USDT": 3000,  # 1 ETH = 3000 USDT
            "ETH_DAI": 3000,   # 1 ETH = 3000 DAI
            "USDC_ETH": 0.00033,  # 1 USDC = 0.00033 ETH
            "USDT_ETH": 0.00033,  # 1 USDT = 0.00033 ETH
            "DAI_ETH": 0.00033    # 1 DAI = 0.00033 ETH
        }
        
        conversion_key = f"{original_currency}_{target_currency}"
        
        if conversion_key in conversion_rates:
            converted_amount = original_amount * conversion_rates[conversion_key]
            
            # Round to appropriate decimal places
            if target_currency in ["USDC", "USDT", "DAI"]:
                converted_amount = round(converted_amount, 2)
            else:
                converted_amount = round(converted_amount, 6)
                
            return converted_amount
        
        # If conversion not found, return original amount
        return original_amount
