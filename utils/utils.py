import requests
from config import TIMEOUTS

def check_api_availability(api_keys):
    available_apis = []
    
    for api_name, api_key in api_keys.items():
        if api_key:
            available_apis.append(api_name)
    
    if 'opensea' in available_apis:
        try:
            url = "https://api.opensea.io/api/v1/collections?offset=0&limit=1"
            headers = {"X-API-KEY": api_keys['opensea']}
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['health_check'])
            if response.status_code != 200:
                available_apis.remove('opensea')
                print(f"OpenSea health check failed: {response.status_code}")
        except:
            if 'opensea' in available_apis:
                available_apis.remove('opensea')
    
    if 'reservoir' in available_apis:
        try:
            url = "https://api.reservoir.tools/collections/v7?limit=1"
            headers = {"x-api-key": api_keys['reservoir']}
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['health_check'])
            if response.status_code != 200:
                available_apis.remove('reservoir')
                print(f"Reservoir health check failed: {response.status_code}")
        except:
            if 'reservoir' in available_apis:
                available_apis.remove('reservoir')
    
    return available_apis

def generate_search_query(contract_address, token_id, current_data):
    query = f"NFT information for contract address {contract_address}"
    
    if token_id:
        query += f" token ID {token_id}"
    
    if current_data.get('collection_data', {}).get('name'):
        collection_name = current_data['collection_data']['name']
        query += f" from the collection {collection_name}"
    
    query += ". Please provide information about: "
    
    if token_id:
        query += "the NFT's name, description, image, rarity, and current value. "
    else:
        query += "the collection's details, floor price, volume, creator, and market trends. "
    
    query += "Include market statistics and community sentiment if available."
    
    return query