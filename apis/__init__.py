# This file is required for the APIs package to be recognized as a Python module
# Importing API functions to make them available when importing from the apis package

from .alchemy_api import fetch_alchemy_data
from .etherscan_api import fetch_gas_prices
from .moralis_api import fetch_moralis_data, fetch_moralis_token_price, fetch_moralis_nft_transfers
from .nftgo_api import fetch_nftgo_data
from .nftscan_api import fetch_nftscan_data
from .opensea_api import fetch_opensea_data
from .perplexity_api import search_web_with_perplexity
from .reservoir_api import fetch_collection_data, fetch_market_data, fetch_rarity_data