import requests
from config import TIMEOUTS
from apis.opensea_api import fetch_opensea_data
from apis.nftscan_api import fetch_nftscan_data, fetch_nftscan_rarity
from apis.nftgo_api import fetch_nftgo_data

def fetch_collection_data(contract_address, api_keys, available_apis):
    """Combine collection data from multiple sources with fallbacks"""
    result = {
        'success': False,
        'data': {},
        'error': None
    }
    
    # Try OpenSea first if available
    if 'opensea' in available_apis:
        opensea_result = fetch_opensea_data(contract_address, None, api_keys['opensea'])
        if opensea_result['success']:
            result['data'] = opensea_result['data']
            result['success'] = True
    
    # Try NFTScan to complement data if available
    if 'nftscan' in available_apis:
        nftscan_result = fetch_nftscan_data(contract_address, None, 'eth', api_keys['nftscan'])
        if nftscan_result['success']:
            # Merge data, preferring NFTScan for certain fields
            for key, value in nftscan_result['data'].items():
                if key in ['twitter_username', 'discord_url', 'instagram_username', 'item_count', 'owner_count', 'floor_price', 'volume_all']:
                    result['data'][key] = value
                elif key not in result['data'] or not result['data'][key]:
                    result['data'][key] = value
            
            result['success'] = True
    
    # Add Reservoir data for more comprehensive market data
    if 'reservoir' in available_apis:
        try:
            url = f"https://api.reservoir.tools/collections/v5?contract={contract_address}"
            headers = {
                "accept": "application/json",
                "x-api-key": api_keys['reservoir']
            }
            
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
            
            if response.status_code == 200:
                data = response.json()
                collection = data.get('collections', [])[0] if data.get('collections') else {}
                
                if collection:
                    result['data'].update({
                        'market_cap': collection.get('market', {}).get('marketCap'),
                        'all_time_volume': collection.get('volume', {}).get('allTime'),
                        'volume_change_1d': collection.get('volume', {}).get('change1d'),
                        'volume_change_7d': collection.get('volume', {}).get('change7d'),
                        'volume_change_30d': collection.get('volume', {}).get('change30d'),
                        'floor_ask': collection.get('floorAsk', {}).get('price'),
                        'floor_ask_change_1d': collection.get('floorAsk', {}).get('change1d'),
                        'floor_ask_change_7d': collection.get('floorAsk', {}).get('change7d'),
                        'floor_ask_change_30d': collection.get('floorAsk', {}).get('change30d')
                    })
                    
                    result['success'] = True
        except Exception:
            # Continue if Reservoir fails - we already have data from other sources
            pass
    
    if not result['success']:
        result['error'] = "Failed to fetch collection data from any source"
    
    return result

def fetch_market_data(contract_address, api_keys, available_apis):
    """Fetch comprehensive market data for a collection with fallbacks"""
    result = {
        'success': False,
        'data': {},
        'error': None
    }
    
    # Fetch from Reservoir for most accurate market data if available
    if 'reservoir' in available_apis:
        try:
            # Get collection stats
            url = f"https://api.reservoir.tools/stats/v2?collection={contract_address}"
            headers = {
                "accept": "application/json",
                "x-api-key": api_keys['reservoir']
            }
            
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                
                result['data'].update({
                    'floor_price': stats.get('floor_price'),
                    'one_day_volume': stats.get('one_day_volume'),
                    'seven_day_volume': stats.get('seven_day_volume'),
                    'thirty_day_volume': stats.get('thirty_day_volume'),
                    'all_time_volume': stats.get('all_time_volume'),
                    'floor_price_change_1d': stats.get('floor_price_1d_change'),
                    'floor_price_change_7d': stats.get('floor_price_7d_change'),
                    'floor_price_change_30d': stats.get('floor_price_30d_change'),
                    'listed_count': stats.get('listed_count'),
                    'average_price': stats.get('average_price')
                })
                
                result['success'] = True
            
            # Get live sales for recent market activity
            url = f"https://api.reservoir.tools/sales/v6?contract={contract_address}&limit=10&sortBy=timestamp&includeMetadata=true"
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
            
            if response.status_code == 200:
                data = response.json()
                sales = data.get('sales', [])
                
                recent_sales = []
                for sale in sales:
                    recent_sales.append({
                        'token_id': sale.get('token', {}).get('tokenId'),
                        'name': sale.get('token', {}).get('name'),
                        'price': sale.get('price', {}).get('amount', {}).get('decimal'),
                        'price_currency': sale.get('price', {}).get('currency', {}).get('symbol'),
                        'timestamp': sale.get('timestamp'),
                        'buyer': sale.get('buyer'),
                        'seller': sale.get('seller')
                    })
                
                result['data']['recent_sales'] = recent_sales
                result['success'] = True
        except Exception:
            pass
    
    # If Reservoir failed or we need more data, try OpenSea if available
    if (not result['success'] or not result['data']) and 'opensea' in available_apis:
        try:
            # Get collection stats from OpenSea
            # First, get the collection slug
            collection_url = f"https://api.opensea.io/api/v1/asset_contract/{contract_address}"
            headers = {
                "accept": "application/json",
                "X-API-KEY": api_keys['opensea']
            }
            
            response = requests.get(collection_url, headers=headers, timeout=TIMEOUTS['default'])
            
            if response.status_code == 200:
                collection_data = response.json()
                collection_slug = collection_data.get('collection', {}).get('slug')
                
                if collection_slug:
                    # Now get the collection stats
                    url = f"https://api.opensea.io/api/v1/collection/{collection_slug}/stats"
                    response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
                    
                    if response.status_code == 200:
                        data = response.json()
                        stats = data.get('stats', {})
                        
                        result['data'].update({
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
                        })
                        
                        result['success'] = True
        except Exception:
            pass
    
    # If both Reservoir and OpenSea failed, try NFTScan if available
    if (not result['success'] or not result['data']) and 'nftscan' in available_apis:
        try:
            url = f"https://restapi.nftscan.com/api/v2/statistics/collection/{contract_address}"
            headers = {
                "X-API-KEY": api_keys['nftscan'],
                "accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=TIMEOUTS['default'])
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {})
                
                result['data'].update({
                    'floor_price': stats.get('floor_price'),
                    'volume_24h': stats.get('volume_24h'),
                    'volume_7d': stats.get('volume_7d'),
                    'volume_30d': stats.get('volume_30d'),
                    'volume_all': stats.get('volume_all'),
                    'sales_24h': stats.get('sales_24h'),
                    'average_price_24h': stats.get('average_price_24h'),
                    'owners_count': stats.get('owners_count')
                })
                
                result['success'] = True
        except Exception:
            pass
    
    if not result['success']:
        result['error'] = "Failed to fetch market data from any source"
    
    return result

def fetch_rarity_data(contract_address, token_id, api_keys, available_apis):
    """Fetch rarity data for a specific NFT with fallbacks"""
    # First try NFTGO for rarity if available
    if 'nftgo' in available_apis:
        nftgo_result = fetch_nftgo_data(contract_address, token_id, api_keys['nftgo'])
        if nftgo_result['success']:
            return nftgo_result
    
    # If NFTGO fails, try NFTScan if available
    if 'nftscan' in available_apis:
        nftscan_result = fetch_nftscan_rarity(contract_address, token_id, api_keys['nftscan'])
        if nftscan_result['success']:
            return nftscan_result
    
    # If both failed, try to estimate rarity from OpenSea traits
    if 'opensea' in available_apis:
        try:
            opensea_data = fetch_opensea_data(contract_address, token_id, api_keys['opensea'])
            if opensea_data['success'] and 'traits' in opensea_data['data']:
                traits = opensea_data['data']['traits']
                
                # Simple rarity calculation based on trait rarity
                estimated_rarity = {
                    'rarity': {
                        'estimated': True,
                        'score': 0
                    },
                    'trait_rarity': []
                }
                
                for trait in traits:
                    if 'trait_count' in trait and trait['trait_count'] > 0:
                        # Lower trait count means higher rarity
                        trait_rarity = 1 / trait['trait_count']
                        estimated_rarity['rarity']['score'] += trait_rarity
                        
                        estimated_rarity['trait_rarity'].append({
                            'trait_type': trait['trait_type'],
                            'value': trait['value'],
                            'rarity': trait_rarity
                        })
                
                return {'success': True, 'data': estimated_rarity}
        except:
            pass
    
    return {'success': False, 'error': 'Could not fetch rarity data from any source'}