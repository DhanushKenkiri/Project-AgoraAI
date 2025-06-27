# NFT Wallet Integration
import json
import time
import uuid
import os
import random

# Import helpers
try:
    from wallet_login import wallet_login, get_wallet_info
except ImportError:
    def wallet_login(wallet_address, wallet_type=None):
        return {
            'success': True, 
            'wallet_address': wallet_address,
            'session_token': str(uuid.uuid4())
        }
    
    def get_wallet_info(wallet_address):
        return {
            'success': True,
            'wallet': {
                'address': wallet_address,
                'balances': [{'token': 'ETH', 'balance': '0.5'}]
            }
        }

# Sample NFT collections for demo purposes
SAMPLE_COLLECTIONS = [
    {
        "name": "Bored Ape Yacht Club",
        "tokens": [
            {"id": "1234", "name": "Bored Ape #1234", "image": "https://example.com/bored-ape-1234.jpg"},
            {"id": "5678", "name": "Bored Ape #5678", "image": "https://example.com/bored-ape-5678.jpg"},
            {"id": "9012", "name": "Bored Ape #9012", "image": "https://example.com/bored-ape-9012.jpg"}
        ]
    },
    {
        "name": "CryptoPunks",
        "tokens": [
            {"id": "5678", "name": "CryptoPunk #5678", "image": "https://example.com/cryptopunk-5678.jpg"},
            {"id": "1234", "name": "CryptoPunk #1234", "image": "https://example.com/cryptopunk-1234.jpg"}
        ]
    },
    {
        "name": "Azuki",
        "tokens": [
            {"id": "9839", "name": "Azuki #9839", "image": "https://example.com/azuki-9839.jpg"}
        ]
    }
]

# Demo wallet addresses with NFTs
DEMO_WALLETS = {
    "0x5e7eE927ce269023794b231465Ed53D66cbD564b": {
        "eth_balance": "0.5",
        "nfts": [
            {"collection": "Bored Ape Yacht Club", "token_id": "1234"},
            {"collection": "CryptoPunks", "token_id": "5678"}
        ]
    },
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": {
        "eth_balance": "1.245",
        "nfts": [
            {"collection": "Azuki", "token_id": "9839"},
            {"collection": "CryptoPunks", "token_id": "1234"}
        ]
    }
}

def get_wallet_nfts(wallet_address):
    """
    Get NFTs owned by the wallet address
    
    Args:
        wallet_address (str): The wallet address to check
        
    Returns:
        dict: NFT information
    """
    # Check if this is a demo wallet
    if wallet_address in DEMO_WALLETS:
        # For demo wallets, return the predefined NFTs
        nft_list = []
        for nft_ref in DEMO_WALLETS[wallet_address]["nfts"]:
            collection_name = nft_ref["collection"]
            token_id = nft_ref["token_id"]
            
            # Find the collection
            for collection in SAMPLE_COLLECTIONS:
                if collection["name"] == collection_name:
                    # Find the token in the collection
                    for token in collection["tokens"]:
                        if token["id"] == token_id:
                            nft_item = {
                                "collection": collection_name,
                                "token_id": token_id,
                                "name": token["name"],
                                "image": token.get("image", "")
                            }
                            nft_list.append(nft_item)
        
        return {
            "success": True,
            "wallet_address": wallet_address,
            "nft_count": len(nft_list),
            "nfts": nft_list
        }
    else:
        # For non-demo wallets, return random NFTs
        random_nfts = []
        num_nfts = random.randint(0, 3)  # Random number of NFTs (0-3)
        
        if num_nfts > 0:
            # Select random collections and tokens
            for _ in range(num_nfts):
                collection = random.choice(SAMPLE_COLLECTIONS)
                if collection["tokens"]:
                    token = random.choice(collection["tokens"])
                    random_nfts.append({
                        "collection": collection["name"],
                        "token_id": token["id"],
                        "name": token["name"],
                        "image": token.get("image", "")
                    })
        
        return {
            "success": True,
            "wallet_address": wallet_address,
            "nft_count": len(random_nfts),
            "nfts": random_nfts
        }

def get_wallet_details(wallet_address):
    """
    Get comprehensive wallet details including balance and NFTs
    
    Args:
        wallet_address (str): The wallet address to check
        
    Returns:
        dict: Complete wallet information
    """
    # Get basic wallet info
    wallet_info = get_wallet_info(wallet_address)
    
    # Get NFTs owned by the wallet
    nft_info = get_wallet_nfts(wallet_address)
    
    # Combine the information
    result = {
        "success": wallet_info.get("success", False) and nft_info.get("success", False),
        "wallet_address": wallet_address,
        "balance": wallet_info.get("wallet", {}).get("balances", [{"token": "ETH", "balance": "0"}])[0].get("balance", "0"),
        "nft_count": nft_info.get("nft_count", 0),
        "nfts": nft_info.get("nfts", []),
        "timestamp": int(time.time())
    }
    
    return result

def handle_wallet_login(wallet_address, wallet_type=None):
    """
    Handle the complete wallet login process including fetching wallet details
    
    Args:
        wallet_address (str): The wallet address to login
        wallet_type (str, optional): The wallet type (metamask, coinbase)
        
    Returns:
        dict: Wallet login and details response
    """
    # First, perform the wallet login
    login_result = wallet_login(wallet_address, wallet_type)
    
    # If login successful, get wallet details
    if login_result.get("success", False):
        wallet_details = get_wallet_details(wallet_address)
        
        # Merge the results
        result = {**login_result, **wallet_details}
        return result
    
    # If login failed, return the login result
    return login_result

def check_transaction_status(transaction_id):
    """
    Check the status of a transaction
    
    Args:
        transaction_id (str): The transaction ID to check
        
    Returns:
        dict: Transaction status
    """
    # In a real implementation, you would check the actual transaction status
    # This is a mock implementation for demonstration
    status_options = ["pending", "completed", "failed"]
    status = random.choice(status_options)
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "status": status,
        "timestamp": int(time.time())
    }
