# Set environment variables for local testing
$env:RESERVOIR_API_KEY = "your-reservoir-api-key"
$env:OPENSEA_API_KEY = "your-opensea-api-key"
$env:NFTGO_API_KEY = "your-nftgo-api-key"

# Also set resource prices (optional if you already have these in your code)
$env:RESOURCE_PRICES = "{`"api/nft/details`":{`"amount`":0.001,`"currency`":`"ETH`"},`"api/collection`":{`"amount`":0.005,`"currency`":`"ETH`"}}"

Write-Host "Environment variables set for local testing"
Write-Host "You can now run: python test_local.py"
