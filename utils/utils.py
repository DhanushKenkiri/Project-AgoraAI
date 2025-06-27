import requests
from config import TIMEOUTS

def check_api_availability(api_keys):
    """
    Check which APIs are likely to be available based on API keys and quick health checks
    Returns list of available API names
    """
    available_apis = []
    
    # First, check if we have the API keys
    for api_name, api_key in api_keys.items():
        if api_key:
            available_apis.append(api_name)
    
    # For critical APIs, perform a quick health check
    if 'opensea' in available_apis:
        try:
            # Simple test request to OpenSea
            url = "https://api.opensea.io/api/v1/collections?offset=0&limit=1"
            headers = {"X-API-KEY": api_keys['opensea']}
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['health_check'])
            if response.status_code != 200:
                available_apis.remove('opensea')
                print(f"OpenSea health check failed: {response.status_code}")
        except:
            # If health check fails, remove from available APIs
            if 'opensea' in available_apis:
                available_apis.remove('opensea')
    
    if 'reservoir' in available_apis:
        try:
            # Simple test request to Reservoir
            url = "https://api.reservoir.tools/collections/v7?limit=1"
            headers = {"x-api-key": api_keys['reservoir']}
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['health_check'])
            if response.status_code != 200:
                available_apis.remove('reservoir')
                print(f"Reservoir health check failed: {response.status_code}")
        except:
            # If health check fails, remove from available APIs
            if 'reservoir' in available_apis:
                available_apis.remove('reservoir')
    
    return available_apis

def generate_search_query(contract_address, token_id, current_data):
    """Generate an effective search query for Perplexity when APIs fail"""
    # Start with the basic contract information
    query = f"NFT information for contract address {contract_address}"
    
    # If we have a token ID, add that
    if token_id:
        query += f" token ID {token_id}"
    
    # Add any collection information we might have
    if current_data.get('collection_data', {}).get('name'):
        collection_name = current_data['collection_data']['name']
        query += f" from the collection {collection_name}"
    
    # Ask for specific data we're interested in
    query += ". Please provide information about: "
    
    if token_id:
        query += "the NFT's name, description, image, rarity, and current value. "
    else:
        query += "the collection's details, floor price, volume, creator, and market trends. "
    
    query += "Include market statistics and community sentiment if available."
    
    return query