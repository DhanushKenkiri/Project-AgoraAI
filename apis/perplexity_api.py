import requests
import re
from config import TIMEOUTS

def search_web_with_perplexity(query, api_key):
    """
    Search the web for NFT information using Perplexity API when other APIs fail
    """
    if not api_key:
        return {'success': False, 'error': 'Perplexity API key not provided'}
    
    try:
        url = "https://api.perplexity.ai/search"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "source": "web_search",  # Use web search mode
            "highlight": False,      # Don't need highlighting
            "follow_up": False       # No follow-up questions
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUTS['web_search'])
        
        if response.status_code == 200:
            result = response.json()
            
            # Process the response into structured NFT data
            processed_data = parse_perplexity_response(result, query)
            
            return {
                'success': True,
                'data': processed_data,
                'raw_answer': result.get('answer', ''),
                'search_context': result.get('search_context', {})
            }
        else:
            return {'success': False, 'error': f"Perplexity API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Error searching with Perplexity: {str(e)}"}

def parse_perplexity_response(perplexity_result, original_query):
    """
    Parse the natural language response from Perplexity into structured NFT data
    """
    answer = perplexity_result.get('answer', '')
    
    # Initialize structured data
    structured_data = {
        'nft_info': {},
        'collection_info': {},
        'market_info': {},
        'community_info': {},
        'summary': answer[:200] + '...' if len(answer) > 200 else answer
    }
    
    # Extract NFT/collection name
    name_match = re.search(r'(?:called|named|titled)\s+[""]?([^""\.]+)[""]?', answer)
    if name_match:
        structured_data['nft_info']['name'] = name_match.group(1).strip()
    
    # Extract collection name
    collection_match = re.search(r'(?:collection|project)\s+(?:called|named|titled)\s+[""]?([^""\.]+)[""]?', answer)
    if collection_match:
        structured_data['collection_info']['name'] = collection_match.group(1).strip()
    
    # Extract floor price
    floor_price_match = re.search(r'(?:floor price|price) (?:is|of) (?:about |approximately |around |roughly )?(\d+\.?\d*)\s*(ETH|eth|Ether|ether)', answer)
    if floor_price_match:
        structured_data['market_info']['floor_price'] = float(floor_price_match.group(1))
        structured_data['market_info']['currency'] = 'ETH'
    
    # Extract total supply
    supply_match = re.search(r'(?:total supply|supply) (?:is|of) (?:about |approximately |around |roughly )?(\d[\d,]+)', answer)
    if supply_match:
        supply = supply_match.group(1).replace(',', '')
        structured_data['collection_info']['total_supply'] = int(supply)
    
    # Extract description
    description_match = re.search(r'description:?\s*[""]?([^""\.]{10,}?)[""]?\.', answer, re.IGNORECASE)
    if not description_match:
        description_match = re.search(r'((?:It|The collection|This NFT) is [^\.]{10,}?)\.',  answer)
    if description_match:
        structured_data['nft_info']['description'] = description_match.group(1).strip()
    
    # Extract creator/artist
    creator_match = re.search(r'(?:created by|artist is|founder is|made by)\s+[""]?([^""\.]+)[""]?', answer, re.IGNORECASE)
    if creator_match:
        structured_data['collection_info']['creator'] = creator_match.group(1).strip()
    
    # Extract image URL if present in the context
    image_match = re.search(r'(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp))', str(perplexity_result))
    if image_match:
        structured_data['nft_info']['image_url'] = image_match.group(1)
    
    # Add links if present in the context
    opensea_match = re.search(r'(https?://opensea.io/[^\s]+)', str(perplexity_result))
    if opensea_match:
        structured_data['collection_info']['opensea_link'] = opensea_match.group(1)
    
    # Extract market sentiment if present
    if re.search(r'popular|trending|high demand|sought[- ]after', answer, re.IGNORECASE):
        structured_data['market_info']['sentiment'] = 'positive'
    elif re.search(r'declining|losing value|dropping|decreased interest', answer, re.IGNORECASE):
        structured_data['market_info']['sentiment'] = 'negative'
    
    # Add extra information that might be useful
    structured_data['sources'] = []
    for source in perplexity_result.get('search_context', {}).get('documents', []):
        if 'url' in source:
            structured_data['sources'].append({
                'title': source.get('title', ''),
                'url': source.get('url', '')
            })
    
    return structured_data