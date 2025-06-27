import os

def load_api_keys():
    """Load API keys from environment variables"""
    return {
        'moralis': os.environ.get('MORALIS_API_KEY'),
        'alchemy': os.environ.get('ALCHEMY_API_KEY'),
        'nftscan': os.environ.get('NFTSCAN_API_KEY'),
        'opensea': os.environ.get('OPENSEA_API_KEY'),
        'nftgo': os.environ.get('NFTGO_API_KEY'),
        'nftport': os.environ.get('NFTPORT_API_KEY'),
        'reservoir': os.environ.get('RESERVOIR_API_KEY'),
        'etherscan': os.environ.get('ETHERSCAN_API_KEY'),
        'perplexity': os.environ.get('PERPLEXITY_API_KEY')
    }

# API request timeouts (in seconds)
TIMEOUTS = {
    'default': 5,
    'health_check': 2,
    'web_search': 10
}

# Request headers
REQUEST_HEADERS = {
    'json': {'Content-Type': 'application/json'},
    'accept_json': {'accept': 'application/json'}
}