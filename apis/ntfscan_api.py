import requests
from config import TIMEOUTS

def fetch_nftscan_data(contract_address, token_id, chain, api_key):
    """Fetch NFT data from NFTScan API"""
    if not api_key:
        return {'success': False, 'error': 'NFTScan API key not provided'}
    
    chain_prefix = "eth" if chain == "eth" else chain
    
    try:
        # Different endpoints depending on whether we're fetching a specific NFT or collection info
        if token_id:
            url = f"https://restapi.nftscan.com/api/v2/{chain_prefix}/asset/{contract_address}/{token_id}"
        else:
            url = f"https://restapi.nftscan.com/api/v2/{chain_prefix}/collection/{contract_address}"
        
        headers = {
            "X-API-KEY": api_key,
            "accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            if token_id:
                # Process specific NFT data
                nft_data = data.get('data', {})
                processed_data = {
                    'nftscan_id': nft_data.get('id'),
                    'contract_name': nft_data.get('contract_name'),
                    'token_id': nft_data.get('token_id'),
                    'image_uri': nft_data.get('image_uri'),
                    'name': nft_data.get('name'),
                    'description': nft_data.get('description'),
                    'content_type': nft_data.get('content_type'),
                    'content_uri': nft_data.get('content_uri'),
                    'external_link': nft_data.get('external_link'),
                    'latest_trade_price': nft_data.get('latest_trade_price'),
                    'latest_trade_symbol': nft_data.get('latest_trade_symbol'),
                    'latest_trade_timestamp': nft_data.get('latest_trade_timestamp'),
                    'attributes': nft_data.get('attributes', [])
                }
            else:
                # Process collection data
                collection_data = data.get('data', {})
                processed_data = {
                    'nftscan_collection_id': collection_data.get('id'),
                    'name': collection_data.get('name'),
                    'description': collection_data.get('description'),
                    'image_url': collection_data.get('logo_url'),
                    'banner_image_url': collection_data.get('banner_url'),
                    'external_url': collection_data.get('website'),
                    'twitter_username': collection_data.get('twitter'),
                    'discord_url': collection_data.get('discord'),
                    'instagram_username': collection_data.get('instagram'),
                    'medium_username': collection_data.get('medium'),
                    'telegram_url': collection_data.get('telegram'),
                    'item_count': collection_data.get('items_total'),
                    'owner_count': collection_data.get('owners_total'),
                    'floor_price': collection_data.get('floor_price'),
                    'volume_all': collection_data.get('volume_all')
                }
            
            return {'success': True, 'data': processed_data}
            
        else:
            return {'success': False, 'error': f"NFTScan API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching from NFTScan: {str(e)}"}

def fetch_nftscan_rarity(contract_address, token_id, api_key):
    """Fetch rarity data from NFTScan API"""
    if not api_key:
        return {'success': False, 'error': 'NFTScan API key not provided'}
    
    try:
        url = f"https://restapi.nftscan.com/api/v2/eth/asset/{contract_address}/{token_id}/rarity"
        headers = {
            "X-API-KEY": api_key,
            "accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            rarity_data = data.get('data', {})
            
            processed_data = {
                'rarity': {
                    'rank': rarity_data.get('rank'),
                    'score': rarity_data.get('score'),
                    'max_rank': rarity_data.get('total')
                },
                'trait_rarity': []
            }
            
            # Process trait rarity if available
            if 'trait' in rarity_data:
                for trait in rarity_data['trait']:
                    processed_data['trait_rarity'].append({
                        'trait_type': trait.get('trait_type'),
                        'value': trait.get('value'),
                        'rarity': trait.get('rarity')
                    })
            
            return {'success': True, 'data': processed_data}
        
        else:
            return {'success': False, 'error': f"NFTScan rarity API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching rarity from NFTScan: {str(e)}"}