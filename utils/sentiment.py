import requests
import re
from config import TIMEOUTS

def fetch_social_sentiment(collection_name, api_keys, available_apis):
    """Fetch social media sentiment data for a collection using Perplexity"""
    # First check if we have the collection name and Perplexity API access
    if not collection_name or 'perplexity' not in available_apis:
        return None
    
    api_key = api_keys.get('perplexity')
    if not api_key:
        return None
    
    try:
        # Craft a specific query for social sentiment
        query = f"What is the current social sentiment for the NFT collection {collection_name}? Include Twitter and Discord activity, overall sentiment (positive/negative/neutral), and recent trends. Provide specific metrics if possible."
        
        url = "https://api.perplexity.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "source": "web_search",  # Use web search mode
            "highlight": False,
            "follow_up": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUTS['web_search'])
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', '')
            
            # Parse the response
            sentiment_data = {
                'raw_analysis': answer[:300] + '...' if len(answer) > 300 else answer,
                'twitter': {},
                'discord': {},
                'overall': {}
            }
            
            # Extract overall sentiment using regex
            sentiment_match = re.search(r'(positive|negative|neutral|mixed|bullish|bearish)', answer, re.IGNORECASE)
            if sentiment_match:
                overall_sentiment = sentiment_match.group(1).lower()
                
                # Map sentiment terms to a normalized value
                sentiment_map = {
                    'positive': 'positive',
                    'bullish': 'positive',
                    'negative': 'negative',
                    'bearish': 'negative',
                    'neutral': 'neutral',
                    'mixed': 'neutral'
                }
                
                sentiment_data['overall']['sentiment'] = sentiment_map.get(overall_sentiment, 'neutral')
                
                # Create a numerical score based on sentiment
                if sentiment_data['overall']['sentiment'] == 'positive':
                    sentiment_data['overall']['score'] = 0.75  # 0.6-1.0 range for positive
                elif sentiment_data['overall']['sentiment'] == 'negative':
                    sentiment_data['overall']['score'] = 0.25  # 0-0.4 range for negative
                else:
                    sentiment_data['overall']['score'] = 0.5   # 0.4-0.6 range for neutral
            
            # Extract Twitter metrics
            twitter_mentions_match = re.search(r'(\d+)\s+(?:mentions|tweets|posts)(?:\s+on\s+Twitter|\s+on\s+X)?', answer, re.IGNORECASE)
            if twitter_mentions_match:
                sentiment_data['twitter']['mentions'] = int(twitter_mentions_match.group(1))
            
            twitter_sentiment_match = re.search(r'Twitter sentiment (?:is|appears to be|seems) (positive|negative|neutral|mixed)', answer, re.IGNORECASE)
            if twitter_sentiment_match:
                sentiment_data['twitter']['sentiment'] = twitter_sentiment_match.group(1).lower()
            
            # Extract Discord metrics
            discord_users_match = re.search(r'(\d[\d,]*)\s+(?:active users|members)(?:\s+on\s+Discord)?', answer, re.IGNORECASE)
            if discord_users_match:
                users = discord_users_match.group(1).replace(',', '')
                sentiment_data['discord']['users'] = int(users)
            
            discord_activity_match = re.search(r'(\d+)\s+(?:messages|posts|discussions)(?:\s+on\s+Discord)?', answer, re.IGNORECASE)
            if discord_activity_match:
                sentiment_data['discord']['activity'] = int(discord_activity_match.group(1))
            
            discord_sentiment_match = re.search(r'Discord sentiment (?:is|appears to be|seems) (positive|negative|neutral|mixed)', answer, re.IGNORECASE)
            if discord_sentiment_match:
                sentiment_data['discord']['sentiment'] = discord_sentiment_match.group(1).lower()
            
            # Extract trending topics or hashtags
            hashtags_match = re.search(r'(?:trending hashtags|popular hashtags|trending topics)(?:\s+include|\s+are)?\s+([^\.]+)', answer, re.IGNORECASE)
            if hashtags_match:
                hashtag_text = hashtags_match.group(1).strip()
                # Extract hashtags with # symbol or just words
                hashtags = re.findall(r'#\w+|\b[A-Za-z]\w+', hashtag_text)
                if hashtags:
                    sentiment_data['trending_topics'] = hashtags[:5]  # Limit to 5 hashtags
            
            # Indicate this data comes from Perplexity
            sentiment_data['source'] = 'perplexity'
            sentiment_data['real_time_data'] = True
            
            # Extract engagement metrics if available
            engagement_match = re.search(r'(?:engagement rate|interaction rate) (?:of|is) (\d+\.?\d*)%', answer, re.IGNORECASE)
            if engagement_match:
                sentiment_data['engagement_rate'] = float(engagement_match.group(1)) / 100
            
            # Add the search context sources
            sentiment_data['sources'] = []
            for source in result.get('search_context', {}).get('documents', []):
                if 'url' in source:
                    sentiment_data['sources'].append({
                        'title': source.get('title', ''),
                        'url': source.get('url', '')
                    })
            
            return sentiment_data
        
        return None
            
    except Exception as e:
        print(f"Error fetching sentiment with Perplexity: {str(e)}")
        return None