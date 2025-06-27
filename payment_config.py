# CDP Wallet and X402 Payment Gateway Configuration
# This file contains settings for the payment integration

# X402 Payment Gateway Integration
X402_API_KEY=""  # Fill this in with your X402 API key
X402_API_SECRET=""  # Fill this in with your X402 API secret
X402_API_ENDPOINT="https://api.x402.com/v1"
X402_MERCHANT_ID=""  # Your X402 merchant ID

# CDP Wallet Integration
CDP_WALLET_APP_ID=""  # Your CDP Wallet app ID
CDP_WALLET_REDIRECT_URL=""  # Where to redirect after wallet connection

# Payment Settings
MAX_PAYMENT_AMOUNT=10.0  # Maximum payment amount in ETH
MIN_PAYMENT_AMOUNT=0.001  # Minimum payment amount in ETH
DEFAULT_GAS_LIMIT=250000  # Default gas limit for transactions
DEFAULT_CURRENCY="ETH"  # Default currency for payments
SUPPORTED_CURRENCIES=["ETH", "USDC", "USDT", "DAI"]  # Supported currencies
WAITING_TIMEOUT=300  # Seconds to wait for transaction confirmation

# AWS Configuration
PAYMENT_LAMBDA_ARN=""  # ARN of the payment Lambda function
TRANSACTION_TABLE_NAME="NFTPaymentTransactions"  # DynamoDB table for transaction records
KMS_KEY_ID=""  # KMS key ID for encrypting sensitive data

# Security Settings
SESSION_EXPIRY=3600  # Wallet session expiry in seconds (1 hour)
MAX_FAILED_ATTEMPTS=5  # Maximum number of failed payment attempts before lockout
NONCE_EXPIRY=300  # Nonce expiry in seconds (5 minutes)
VERIFICATION_REQUIRED=True  # Require transaction verification
SIGNATURE_ALGORITHM="HMAC-SHA256"  # Algorithm for transaction signatures

# Blockchain Network Settings
DEFAULT_CHAIN_ID=1  # Ethereum Mainnet
SUPPORTED_CHAINS={
    "1": "Ethereum Mainnet",
    "137": "Polygon Mainnet",
    "56": "Binance Smart Chain",
    "42161": "Arbitrum One",
    "10": "Optimism"
}

# Transaction Settings
CONFIRMATION_BLOCKS=2  # Number of blocks required for confirmation
MAX_GAS_PRICE=100  # Maximum gas price in Gwei

# Monitoring and Alerts
ENABLE_ALERTS=True  # Enable payment alerts
ALERT_EMAIL=""  # Email for payment alerts
LARGE_PAYMENT_THRESHOLD=5.0  # Threshold for large payment alerts in ETH

def load_payment_config():
    """
    Load payment configuration settings
    
    Returns:
        dict: Payment configuration settings
    """
    return {
        "x402": {
            "api_key": X402_API_KEY,
            "api_secret": X402_API_SECRET,
            "api_endpoint": X402_API_ENDPOINT,
            "merchant_id": X402_MERCHANT_ID
        },
        "cdp_wallet": {
            "app_id": CDP_WALLET_APP_ID,
            "redirect_url": CDP_WALLET_REDIRECT_URL
        },
        "payment": {
            "max_amount": MAX_PAYMENT_AMOUNT,
            "min_amount": MIN_PAYMENT_AMOUNT,
            "default_gas_limit": DEFAULT_GAS_LIMIT,
            "default_currency": DEFAULT_CURRENCY,
            "supported_currencies": SUPPORTED_CURRENCIES,
            "waiting_timeout": WAITING_TIMEOUT
        },
        "aws": {
            "payment_lambda_arn": PAYMENT_LAMBDA_ARN,
            "transaction_table": TRANSACTION_TABLE_NAME,
            "kms_key_id": KMS_KEY_ID
        },
        "security": {
            "session_expiry": SESSION_EXPIRY,
            "max_failed_attempts": MAX_FAILED_ATTEMPTS,
            "nonce_expiry": NONCE_EXPIRY,
            "verification_required": VERIFICATION_REQUIRED,
            "signature_algorithm": SIGNATURE_ALGORITHM
        },
        "blockchain": {
            "default_chain_id": DEFAULT_CHAIN_ID,
            "supported_chains": SUPPORTED_CHAINS,
            "confirmation_blocks": CONFIRMATION_BLOCKS,
            "max_gas_price": MAX_GAS_PRICE
        },
        "monitoring": {
            "enable_alerts": ENABLE_ALERTS,
            "alert_email": ALERT_EMAIL,
            "large_payment_threshold": LARGE_PAYMENT_THRESHOLD
        }
    }
