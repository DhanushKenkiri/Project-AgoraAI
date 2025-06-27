import requests
from config import TIMEOUTS

def fetch_alchemy_data(contract_address, token_id, api_key):
    """Fetch NFT data from Alchemy API"""
    if not api_key:
        return {'success': False, 'error': 'Alchemy API key not provided'}
    
    if not token_id:
        return {'success': False, 'error': 'Token ID required for Alchemy API'}
    
    try:
        url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{api_key}/getNFTMetadata"
        params = {
            "contractAddress": contract_address,
            "tokenId": token_id,
            "refreshCache": "false"
        }
        
        response = requests.get(url, params=params, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            processed_data = {
                'token_id': data.get('id', {}).get('tokenId'),
                'title': data.get('title'),
                'description': data.get('description'),
                'token_type': data.get('id', {}).get('tokenMetadata', {}).get('tokenType'),
                'image_url': data.get('media', [{}])[0].get('gateway') if data.get('media') else None,
                'raw_metadata': data.get('metadata'),
                'timeLastUpdated': data.get('timeLastUpdated'),
                'contract_metadata': {
                    'name': data.get('contract', {}).get('name'),
                    'symbol': data.get('contract', {}).get('symbol'),
                    'totalSupply': data.get('contract', {}).get('totalSupply'),
                    'tokenType': data.get('contract', {}).get('tokenType'),
                    'openSea': data.get('contract', {}).get('openSea', {})
                },
                'alchemy_metadata': {
                    'attributes': data.get('metadata', {}).get('attributes', [])
                }
            }
            
            return {'success': True, 'data': processed_data}
            
        else:
            return {'success': False, 'error': f"Alchemy API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching from Alchemy: {str(e)}"}