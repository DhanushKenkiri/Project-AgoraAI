#!/bin/bash
# test_wallet_login.sh - Test the wallet login functionality

# Import test event from test.json
echo "Loading test events from test.json..."
TEST_EVENTS_JSON=$(cat test.json)

# Extract the wallet login test event
WALLET_LOGIN_EVENT=$(echo "$TEST_EVENTS_JSON" | python -c "import sys, json; print(json.dumps(json.load(sys.stdin)['testEvents']['walletLogin']))")
DEMO_WALLET_EVENT=$(echo "$TEST_EVENTS_JSON" | python -c "import sys, json; print(json.dumps(json.load(sys.stdin)['testEvents']['demoWalletLogin']))")
WALLET_NFTS_EVENT=$(echo "$TEST_EVENTS_JSON" | python -c "import sys, json; print(json.dumps(json.load(sys.stdin)['testEvents']['getWalletNFTs']))")

# Set up mock environment variables
export ENVIRONMENT=test
export RESERVOIR_API_KEY=test_key
export OPENSEA_API_KEY=test_key
export NFTGO_API_KEY=test_key
export MORALIS_API_KEY=test_key
export ALCHEMY_API_KEY=test_key
export PERPLEXITY_API_KEY=test_key
export ETHERSCAN_API_KEY=test_key
export MAX_PAYMENT_AMOUNT=10.0
export MIN_PAYMENT_AMOUNT=0.001
export DEFAULT_CURRENCY=ETH
export SUPPORTED_CURRENCIES="ETH,USDC,USDT,DAI"
export NETWORK=base-sepolia
export TOKEN_CONTRACT_ADDRESS=0x123456789abcdef123456789abcdef123456789a
export RPC_URL=https://sepolia.base.org
export CDP_WALLET_APP_ID=test_app_id
export TRANSACTION_TABLE_NAME=NFTPaymentTransactions-test
export WALLET_SESSIONS_TABLE=NFTWalletSessions-test
export RESOURCE_PRICES="{\"text_search\": 0.001, \"image_search\": 0.002, \"premium_content\": 0.005}"

# Test regular wallet login
echo "Testing regular wallet login..."
echo $WALLET_LOGIN_EVENT | python -c "import sys, json, lambda_handler; event = json.load(sys.stdin); result = lambda_handler.handle_wallet_request(event); print(json.dumps(result, indent=2))"

echo "-------------------"

# Test demo wallet login
echo "Testing demo wallet login..."
echo $DEMO_WALLET_EVENT | python -c "import sys, json, lambda_handler; event = json.load(sys.stdin); result = lambda_handler.handle_wallet_request(event); print(json.dumps(result, indent=2))"

echo "-------------------"

# Test getting NFTs
echo "Testing get wallet NFTs..."
echo $WALLET_NFTS_EVENT | python -c "import sys, json, lambda_handler; event = json.load(sys.stdin); result = lambda_handler.handle_wallet_nfts_request(event); print(json.dumps(result, indent=2))"

echo "All tests completed!"
