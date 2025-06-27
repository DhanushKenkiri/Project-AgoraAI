import requests
from config import TIMEOUTS, REQUEST_HEADERS

def fetch_moralis_data(contract_address, token_id, chain, api_key):
    """Fetch NFT data from Moralis API"""
    if not api_key:
        return {'success': False, 'error': 'Moralis API key not provided'}
    
    # If token_id is not provided, return error as we need specific token for Moralis NFT endpoint
    if not token_id:
        return {'success': False, 'error': 'Token ID required for Moralis API NFT endpoint'}
    
    try:
        # Convert chain parameter to Moralis format
        chain_map = {
            'eth': 'ethereum',
            'polygon': 'polygon',
            'bsc': 'bsc',
            'avalanche': 'avalanche',
            'fantom': 'fantom',
            'cronos': 'cronos',
            'arbitrum': 'arbitrum'
        }
        
        moralis_chain = chain_map.get(chain.lower(), 'ethereum')
        
        # Endpoint for getting NFT metadata
        url = f"https://deep-index.moralis.io/api/v2/nft/{contract_address}/{token_id}"
        
        # Set required headers
        headers = {
            'accept': 'application/json',
            'X-API-Key': api_key
        }
        
        # Setup parameters
        params = {
            'chain': moralis_chain,
            'format': 'decimal'
        }
        
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            # Process and structure the data in a standardized format
            processed_data = {
                'token_id': data.get('token_id'),
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'token_uri': data.get('token_uri'),
                'contract_type': data.get('contract_type'),  # ERC721 or ERC1155
                'token_address': data.get('token_address'),
                'owner_of': data.get('owner_of'),
                'block_number': data.get('block_number'),
                'block_number_minted': data.get('block_number_minted'),
                'token_hash': data.get('token_hash'),
                'amount': data.get('amount'),
                'image_url': None,  # Will be populated from metadata if available
                'metadata': None,
                'last_token_uri_sync': data.get('last_token_uri_sync'),
                'last_metadata_sync': data.get('last_metadata_sync')
            }
            
            # Extract additional details from metadata if available
            if data.get('metadata'):
                try:
                    if isinstance(data.get('metadata'), str):
                        import json
                        metadata = json.loads(data.get('metadata'))
                    else:
                        metadata = data.get('metadata')
                    
                    processed_data['metadata'] = metadata
                    processed_data['name'] = metadata.get('name') or processed_data['name']
                    processed_data['description'] = metadata.get('description')
                    
                    # Try to get image URL from metadata
                    if metadata.get('image'):
                        processed_data['image_url'] = metadata.get('image')
                    elif metadata.get('image_url'):
                        processed_data['image_url'] = metadata.get('image_url')
                    
                    # Add attributes if available
                    if metadata.get('attributes'):
                        processed_data['attributes'] = metadata.get('attributes')
                except Exception as e:
                    # If there's an error parsing the metadata, continue without it
                    processed_data['metadata_error'] = str(e)
            
            return {'success': True, 'data': processed_data}
        else:
            return {'success': False, 'error': f"Moralis API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching from Moralis: {str(e)}"}

def fetch_moralis_token_price(token_address, chain, api_key):
    """Fetch token price data from Moralis API"""
    if not api_key:
        return {'success': False, 'error': 'Moralis API key not provided'}
    
    try:
        # Convert chain parameter to Moralis format
        chain_map = {
            'eth': 'ethereum',
            'polygon': 'polygon',
            'bsc': 'bsc',
            'avalanche': 'avalanche',
            'fantom': 'fantom',
            'cronos': 'cronos',
            'arbitrum': 'arbitrum'
        }
        
        moralis_chain = chain_map.get(chain.lower(), 'ethereum')
        
        # Endpoint for getting token price
        url = f"https://deep-index.moralis.io/api/v2/erc20/{token_address}/price"
        
        # Set required headers
        headers = {
            'accept': 'application/json',
            'X-API-Key': api_key
        }
        
        # Setup parameters
        params = {
            'chain': moralis_chain
        }
        
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                'success': True,
                'data': {
                    'usd_price': data.get('usdPrice'),
                    'native_price': data.get('nativePrice', {}).get('value'),
                    'native_price_decimals': data.get('nativePrice', {}).get('decimals'),
                    'native_token_symbol': data.get('nativePrice', {}).get('symbol'),
                    'exchange_name': data.get('exchangeName'),
                    'exchange_address': data.get('exchangeAddress')
                }
            }
        else:
            return {'success': False, 'error': f"Moralis Price API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching price from Moralis: {str(e)}"}

def fetch_moralis_nft_transfers(contract_address, token_id, chain, api_key, limit=10):
    """Fetch NFT transfer history from Moralis API"""
    if not api_key:
        return {'success': False, 'error': 'Moralis API key not provided'}
    
    try:
        # Convert chain parameter to Moralis format
        chain_map = {
            'eth': 'ethereum',
            'polygon': 'polygon',
            'bsc': 'bsc',
            'avalanche': 'avalanche',
            'fantom': 'fantom',
            'cronos': 'cronos',
            'arbitrum': 'arbitrum'
        }
        
        moralis_chain = chain_map.get(chain.lower(), 'ethereum')
        
        # Endpoint for getting NFT transfers
        url = f"https://deep-index.moralis.io/api/v2/nft/{contract_address}/transfers"
        
        # Set required headers
        headers = {
            'accept': 'application/json',
            'X-API-Key': api_key
        }
        
        # Setup parameters
        params = {
            'chain': moralis_chain,
            'format': 'decimal',
            'limit': limit
        }
        
        # Add token_id to parameters if provided
        if token_id:
            params['token_id'] = token_id
        
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', [])
            
            transfers = []
            for transfer in result:
                transfers.append({
                    'token_id': transfer.get('token_id'),
                    'from_address': transfer.get('from_address'),
                    'to_address': transfer.get('to_address'),
                    'value': transfer.get('value'),
                    'amount': transfer.get('amount'),
                    'block_number': transfer.get('block_number'),
                    'block_timestamp': transfer.get('block_timestamp'),
                    'transaction_hash': transfer.get('transaction_hash')
                })
            
            return {
                'success': True,
                'data': {
                    'transfers': transfers,
                    'total': data.get('total'),
                    'page': data.get('page'),
                    'page_size': data.get('page_size')
                }
            }
        else:
            return {'success': False, 'error': f"Moralis Transfers API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error fetching transfers from Moralis: {str(e)}"}
