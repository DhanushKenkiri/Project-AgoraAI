# Wallet Login Wrapper Functions
import uuid
import time
import json
import os
import boto3
from datetime import datetime, timedelta

# Import X402 wallet connection handler
from x402_payment_handler import handle_wallet_connection as x402_handle_wallet_connection

# Import CDP wallet handler
from cdp_wallet_handler import handle_cdp_connection, process_cdp_transaction, get_cdp_wallet_info

def wallet_login(wallet_address, wallet_type=None):
    """
    Handle wallet login for both X402 and CDP wallets
    
    Args:
        wallet_address: The wallet address to connect
        wallet_type: The type of wallet (metamask, coinbase, etc)
        
    Returns:
        dict: Login result with success status, session info
    """
    if not wallet_address:
        return {
            'success': False, 
            'error': 'Wallet address is required'
        }
    
    # Default to metamask if wallet type not provided
    if not wallet_type:
        wallet_type = 'metamask'
    
    try:
        # Create DynamoDB session record
        session_id = str(uuid.uuid4())
        expiration = int(time.time()) + 3600  # 1 hour expiration
        
        # Store session in DynamoDB
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(os.environ.get('WALLET_SESSIONS_TABLE', 'NFTWalletSessions'))
            
            table.put_item(Item={
                'session_id': session_id,
                'wallet_address': wallet_address,
                'wallet_type': wallet_type,
                'created_at': int(time.time()),
                'expiration': expiration,
                'status': 'active'
            })
        except Exception as db_error:
            print(f"Warning: Failed to store wallet session: {str(db_error)}")
        
        # Handle CDP wallet connection if CDP app ID is configured
        cdp_app_id = os.environ.get('CDP_WALLET_APP_ID')
        if cdp_app_id:
            try:
                cdp_result = handle_cdp_connection(wallet_address, wallet_type)
                if cdp_result.get('success'):
                    return {
                        'success': True,
                        'wallet_address': wallet_address,
                        'wallet_type': wallet_type,
                        'session_token': session_id,
                        'expiration': expiration,
                        'cdp_connected': True,
                        'cdp_session': cdp_result.get('cdp_session')
                    }
                else:
                    print(f"CDP connection warning: {cdp_result.get('error')}")
            except Exception as cdp_error:
                print(f"CDP connection error: {str(cdp_error)}")
        
        # Return successful login response
        return {
            'success': True,
            'wallet_address': wallet_address,
            'wallet_type': wallet_type,
            'session_token': session_id,
            'expiration': expiration
        }
        
    except Exception as e:
        print(f"Wallet login error: {str(e)}")
        return {
            'success': False,
            'error': f'Wallet login failed: {str(e)}'
        }
