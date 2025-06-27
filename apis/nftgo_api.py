import requests
from config import TIMEOUTS

def fetch_nftgo_data(contract_address, token_id, api_key):
    """Fetch NFT rarity and valuation data from NFTGO API"""
    if not api_key:
        return {'success': False, 'error': 'NFTGO API key not provided'}
    
    if not token_id:
        return {'success': False, 'error': 'Token ID required for NFTGO API'}
    
    try:
        url = f"https://data-api.nftgo.io/eth/v1/nft/{contract_address}/{token_id}/metrics"
        
        headers = {
            "accept": "application/json",
            "X-API-KEY": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            processed_data = {
                'rarity': {
                    'rank': data.get('rarity', {}).get('rank'),
                    'score': data.get('rarity', {}).get('score'),
                    'max_rank': data.get('rarity', {}).get('max_rank')
                },
                'valuation': {
                    'price': data.get('valuation', {}).get('price'),
                    'currency': data.get('valuation', {}).get('currency')
                },
                'whale_stats': {
                    'whale_ownership': data.get('whales', {}).get('percentage'),
                    'whale_holdings': data.get('whales', {}).get('num')
                }
            }
            
            return {'success': True, 'data': processed_data}
            
        else:
            return {'success': False, 'error': f"NFTGO API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching from NFTGO: {str(e)}"}