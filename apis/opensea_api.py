import requests
from config import TIMEOUTS

def fetch_opensea_data(contract_address, token_id, api_key):
    """Fetch NFT data from OpenSea API"""
    if not api_key:
        return {'success': False, 'error': 'OpenSea API key not provided'}
    
    try:
        if token_id:
            # Fetch specific asset
            url = f"https://api.opensea.io/api/v1/asset/{contract_address}/{token_id}"
        else:
            # Fetch collection
            url = f"https://api.opensea.io/api/v1/asset_contract/{contract_address}"
        
        headers = {
            "Accept": "application/json",
            "X-API-KEY": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            if token_id:
                # Process specific NFT data
                processed_data = {
                    'opensea_id': data.get('id'),
                    'token_id': data.get('token_id'),
                    'name': data.get('name'),
                    'description': data.get('description'),
                    'permalink': data.get('permalink'),
                    'image_url': data.get('image_url'),
                    'image_thumbnail_url': data.get('image_thumbnail_url'),
                    'animation_url': data.get('animation_url'),
                    'background_color': data.get('background_color'),
                    'collection': {
                        'name': data.get('collection', {}).get('name'),
                        'slug': data.get('collection', {}).get('slug'),
                        'image_url': data.get('collection', {}).get('image_url')
                    },
                    'traits': data.get('traits', []),
                    'last_sale': data.get('last_sale'),
                    'top_bid': data.get('top_bid'),
                    'listing_date': data.get('listing_date')
                }
            else:
                # Process collection data
                processed_data = {
                    'name': data.get('name'),
                    'symbol': data.get('symbol'),
                    'description': data.get('description'),
                    'external_link': data.get('external_link'),
                    'image_url': data.get('image_url'),
                    'total_supply': data.get('total_supply'),
                    'created_date': data.get('created_date'),
                    'opensea_seller_fee_basis_points': data.get('opensea_seller_fee_basis_points'),
                    'dev_seller_fee_basis_points': data.get('dev_seller_fee_basis_points'),
                    'payout_address': data.get('payout_address')
                }
            
            return {'success': True, 'data': processed_data}
            
        else:
            return {'success': False, 'error': f"OpenSea API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching from OpenSea: {str(e)}"}

def fetch_opensea_collection_stats(collection_slug, api_key):
    """Fetch collection statistics from OpenSea API"""
    if not api_key or not collection_slug:
        return {'success': False, 'error': 'Missing required parameters'}
    
    try:
        url = f"https://api.opensea.io/api/v1/collection/{collection_slug}/stats"
        headers = {
            "accept": "application/json",
            "X-API-KEY": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            processed_data = {
                'floor_price': stats.get('floor_price'),
                'total_volume': stats.get('total_volume'),
                'total_sales': stats.get('total_sales'),
                'average_price': stats.get('average_price'),
                'num_owners': stats.get('num_owners'),
                'market_cap': stats.get('market_cap'),
                'one_day_volume': stats.get('one_day_volume'),
                'one_day_change': stats.get('one_day_change'),
                'one_day_sales': stats.get('one_day_sales'),
                'one_day_average_price': stats.get('one_day_average_price'),
                'seven_day_volume': stats.get('seven_day_volume'),
                'seven_day_change': stats.get('seven_day_change'),
                'seven_day_sales': stats.get('seven_day_sales'),
                'seven_day_average_price': stats.get('seven_day_average_price'),
                'thirty_day_volume': stats.get('thirty_day_volume'),
                'thirty_day_change': stats.get('thirty_day_change'),
                'thirty_day_sales': stats.get('thirty_day_sales'),
                'thirty_day_average_price': stats.get('thirty_day_average_price')
            }
            
            return {'success': True, 'data': processed_data}
            
        else:
            return {'success': False, 'error': f"OpenSea stats API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching collection stats from OpenSea: {str(e)}"}