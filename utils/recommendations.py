def generate_recommendations(nft_data, market_data, rarity_data, sentiment_data, web_search_data=None):
    """
    Generate AI-based recommendations with fallback to web search data
    """
    recommendations = {
        'buy': {
            'recommendation': None,  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
            'confidence': None,      # 0-1 score
            'reasoning': []
        },
        'price_prediction': {
            'short_term': None,      # direction and percentage
            'long_term': None,
            'confidence': None
        }
    }
    
    # Basic implementation with some logic to provide recommendations
    factors = []
    buy_score = 0.5  # Neutral starting point
    
    # Factor 1: Rarity
    if rarity_data and 'rarity' in rarity_data:
        rank = rarity_data['rarity'].get('rank', 0)
        max_rank = rarity_data['rarity'].get('max_rank', 1)
        
        if max_rank > 0 and rank > 0:
            rarity_percentile = 1 - (rank / max_rank)
            
            if rarity_percentile > 0.95:
                factors.append("Extremely rare NFT (top 5%)")
                buy_score += 0.2
            elif rarity_percentile > 0.8:
                factors.append("Very rare NFT (top 20%)")
                buy_score += 0.1
            elif rarity_percentile < 0.2:
                factors.append("Common NFT (bottom 20%)")
                buy_score -= 0.1
    
    # Factor 2: Floor price trend
    if market_data:
        floor_change_1d = market_data.get('floor_price_change_1d')
        floor_change_7d = market_data.get('floor_price_change_7d')
        
        if floor_change_1d is not None and floor_change_7d is not None:
            # Rising floor price
            if floor_change_1d > 0.1 and floor_change_7d > 0.2:
                factors.append("Strong upward trend in floor price")
                buy_score += 0.15
            elif floor_change_1d < -0.1 and floor_change_7d < -0.2:
                factors.append("Declining floor price trend")
                buy_score -= 0.15
            
            # Reversal pattern
            if floor_change_1d > 0.05 and floor_change_7d < -0.1:
                factors.append("Possible bullish reversal pattern")
                buy_score += 0.05
    
    # Factor 3: Social sentiment
    if sentiment_data:
        # Check overall sentiment
        overall_sentiment = sentiment_data.get('overall', {})
        sentiment_score = overall_sentiment.get('score')
        
        if sentiment_score is not None:
            if sentiment_score > 0.7:
                factors.append("Very positive social sentiment")
                buy_score += 0.1
            elif sentiment_score < 0.3:
                factors.append("Negative social sentiment")
                buy_score -= 0.1
        
        # Check Twitter mentions as engagement indicator
        twitter_mentions = sentiment_data.get('twitter', {}).get('mentions')
        if twitter_mentions is not None and twitter_mentions > 100:
            factors.append("High social media engagement")
            buy_score += 0.05
        
        # Check Discord activity
        discord_users = sentiment_data.get('discord', {}).get('users')
        discord_activity = sentiment_data.get('discord', {}).get('activity')
        
        if discord_users is not None and discord_users > 1000:
            factors.append("Active community on Discord")
            buy_score += 0.05
        
        if discord_activity is not None and discord_activity > 200:
            factors.append("High Discord engagement")
            buy_score += 0.05
    
    # Factor 4: Web search results if available
    if web_search_data:
        # Check market sentiment from web search
        if web_search_data.get('market_info', {}).get('sentiment') == 'positive':
            factors.append("Positive mentions in online sources")
            buy_score += 0.05
        elif web_search_data.get('market_info', {}).get('sentiment') == 'negative':
            factors.append("Negative mentions in online sources")
            buy_score -= 0.05
            
        # Check the number of sources as a proxy for popularity
        source_count = len(web_search_data.get('sources', []))
        if source_count > 5:
            factors.append("High online visibility (multiple sources)")
            buy_score += 0.05
    
    # Generate buy recommendation
    if buy_score > 0.7:
        recommendations['buy']['recommendation'] = 'strong_buy'
        recommendations['buy']['confidence'] = min(1.0, buy_score)
    elif buy_score > 0.55:
        recommendations['buy']['recommendation'] = 'buy'
        recommendations['buy']['confidence'] = min(1.0, buy_score)
    elif buy_score < 0.3:
        recommendations['buy']['recommendation'] = 'strong_sell'
        recommendations['buy']['confidence'] = min(1.0, 1 - buy_score)
    elif buy_score < 0.45:
        recommendations['buy']['recommendation'] = 'sell'
        recommendations['buy']['confidence'] = min(1.0, 1 - buy_score)
    else:
        recommendations['buy']['recommendation'] = 'hold'
        recommendations['buy']['confidence'] = 0.5
    
    recommendations['buy']['reasoning'] = factors
    
    # Simple price predictions
    if buy_score > 0.6:
        recommendations['price_prediction']['short_term'] = f"+{int((buy_score - 0.5) * 100)}%"
        recommendations['price_prediction']['long_term'] = f"+{int((buy_score - 0.5) * 200)}%"
    elif buy_score < 0.4:
        recommendations['price_prediction']['short_term'] = f"{int((buy_score - 0.5) * 100)}%"
        recommendations['price_prediction']['long_term'] = f"{int((buy_score - 0.5) * 200)}%"
    else:
        recommendations['price_prediction']['short_term'] = "0%"
        recommendations['price_prediction']['long_term'] = f"{int((buy_score - 0.5) * 100)}%"
    
    recommendations['price_prediction']['confidence'] = abs(buy_score - 0.5) * 2
    
    # Add a note if recommendations are based on limited data
    if not nft_data or not market_data or (web_search_data and not factors):
        recommendations['limited_data'] = True
        recommendations['note'] = "Recommendations based on limited data - treat with caution"
    
    return recommendations