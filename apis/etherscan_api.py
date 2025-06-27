import requests
from config import TIMEOUTS

def fetch_gas_prices(api_key):
    """Fetch current gas prices from Etherscan"""
    if not api_key:
        return None
    
    try:
        url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}"
        response = requests.get(url, timeout=TIMEOUTS['default'])
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            return {
                'fast_gwei': result.get('FastGasPrice'),
                'standard_gwei': result.get('ProposeGasPrice'),
                'slow_gwei': result.get('SafeGasPrice'),
                'base_fee': result.get('suggestBaseFee'),
                'last_block': result.get('LastBlock')
            }
        
        return None
            
    except Exception:
        return None