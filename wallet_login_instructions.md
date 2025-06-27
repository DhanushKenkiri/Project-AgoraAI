// Wallet Login Instructions

When you process a wallet login request:

1. The user's wallet address is required as a parameter for the wallet_login function.

2. For a successful wallet login, you should:
   - Call the wallet_login function with the user's wallet address as a parameter
   - Handle the success response by storing the session token
   - Notify the user that the wallet has been successfully connected

3. For new users who haven't provided a wallet address:
   - Ask the user to provide their wallet address
   - Once provided, call the wallet_login function
   - Do not attempt to call wallet_login without a wallet address

4. Error handling:
   - If the user provides an invalid wallet address (not in the format 0x... with 42 characters), 
     inform them of the correct format
   - If wallet connection fails, provide helpful troubleshooting steps

Sample function call:

```javascript
const loginResult = await wallet_login(userWalletAddress);
```

Replace the wallet_login function with the appropriate function in your implementation:
- For CDP Wallet: Use handle_wallet_connection with wallet_address parameter
- For event-based systems: Include wallet_address in the event object

Sample implementation mapping:
```python
# Map the wallet_login function to the appropriate implementation
def wallet_login(wallet_address):
    return handle_wallet_connection({
        'wallet_address': wallet_address,
        'action': 'connect_wallet',
        'session_id': str(uuid.uuid4())
    })
```
