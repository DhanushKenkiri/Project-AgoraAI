# This file is required for the utils package to be recognized as a Python module
# Importing utility functions to make them available when importing from the utils package

from .utils import check_api_availability, generate_search_query
from .recommendations import generate_recommendations
from .sentiment import fetch_social_sentiment