# CDP Wallet Handler
# This file handles CDP wallet connection and transactions

import json
import os
import uuid
import time
import requests
import boto3
from datetime import datetime

# Import the CDP wallet connector - this is a JavaScript module that's executed via a Node.js runtime
# We'll use native Python methods to directly call CDP APIs instead of relying on the JS connector

def get_cdp_app_id():
    """Get CDP app ID from environment"""
    app_id = os.environ.get('CDP_WALLET_APP_ID', '')
    if not app_id:
        raise ValueError("CDP_WALLET_APP_ID environment variable is not set")
    return app_id

def get_cdp_api_endpoint():
    """Get CDP API endpoint from environment or use default"""
    return os.environ.get('CDP_API_ENDPOINT', 'https://api.cdp.io')

def connect_cdp_wallet(wallet_address, wallet_type):
    """
    Connect a wallet to CDP
    
    Args:
        wallet_address: The wallet address to connect
        wallet_type: The type of wallet (metamask, coinbase)
        
    Returns:
        dict: CDP connection result
    """
    app_id = get_cdp_app_id()
    api_endpoint = get_cdp_api_endpoint()
    
    # Prepare request payload
    payload = {
        "app_id": app_id,
        "wallet_address": wallet_address,
        "wallet_type": wallet_type or "metamask",
        "connection_type": "server_side"
    }
    
    try:
        # Call CDP API to connect wallet
        response = requests.post(
            f"{api_endpoint}/v1/connect",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app_id}"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "connected": True,
                "wallet_address": wallet_address,
                "wallet_type": wallet_type,
                "cdp_session": result.get("session_id", str(uuid.uuid4())),
                "timestamp": int(time.time())
            }
        else:
            error_message = "Failed to connect to CDP"
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_message = error_json["error"]
            except:
                error_message = f"HTTP error {response.status_code}"
                
            return {
                "connected": False,
                "error": error_message
            }
    
    except Exception as e:
        return {
            "connected": False,
            "error": f"CDP connection error: {str(e)}"
        }

def execute_cdp_transaction(wallet_address, amount, currency):
    """
    Execute a transaction via CDP
    
    Args:
        wallet_address: The wallet address to use
        amount: The transaction amount
        currency: The currency to use
        
    Returns:
        dict: Transaction result
    """
    app_id = get_cdp_app_id()
    api_endpoint = get_cdp_api_endpoint()
    
    # Prepare transaction payload
    payload = {
        "app_id": app_id,
        "wallet_address": wallet_address,
        "amount": amount,
        "currency": currency,
        "transaction_type": "payment"
    }
    
    try:
        # Call CDP API to execute transaction
        response = requests.post(
            f"{api_endpoint}/v1/transact",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app_id}"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "transaction_id": result.get("transaction_id", f"cdp-tx-{str(uuid.uuid4())[:8]}"),
                "wallet_address": wallet_address,
                "amount": amount,
                "currency": currency,
                "status": result.get("status", "pending"),
                "timestamp": int(time.time())
            }
        else:
            error_message = "Failed to execute CDP transaction"
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_message = error_json["error"]
            except:
                error_message = f"HTTP error {response.status_code}"
                
            return {
                "success": False,
                "error": error_message
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"CDP transaction error: {str(e)}"
        }

def get_cdp_balance(wallet_address):
    """
    Get balance information for a CDP wallet
    
    Args:
        wallet_address: The wallet address to check
        
    Returns:
        dict: Balance information
    """
    app_id = get_cdp_app_id()
    api_endpoint = get_cdp_api_endpoint()
    
    try:
        # Call CDP API to get balance
        response = requests.get(
            f"{api_endpoint}/v1/balance/{wallet_address}",
            headers={
                "Authorization": f"Bearer {app_id}"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "wallet_address": wallet_address,
                "balances": result.get("balances", []),
                "timestamp": int(time.time())
            }
        else:
            error_message = "Failed to get CDP balance"
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_message = error_json["error"]
            except:
                error_message = f"HTTP error {response.status_code}"
                
            return {
                "success": False,
                "error": error_message
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"CDP balance check error: {str(e)}"
        }

def handle_cdp_connection(wallet_address, wallet_type=None):
    """
    Handle CDP wallet connection
    
    Args:
        wallet_address: The wallet address to connect
        wallet_type: The type of wallet (metamask, coinbase)
        
    Returns:
        dict: Connection result
    """
    try:
        connection_result = connect_cdp_wallet(wallet_address, wallet_type)
        
        if connection_result.get('connected', False):
            # Store CDP session in DynamoDB if available
            try:
                dynamodb = boto3.resource('dynamodb')
                table_name = os.environ.get('CDP_SESSIONS_TABLE', 'CDPWalletSessions')
                
                # Check if table exists and create if needed
                try:
                    table = dynamodb.Table(table_name)
                    table.put_item(Item={
                        'wallet_address': wallet_address,
                        'cdp_session': connection_result.get('cdp_session'),
                        'wallet_type': wallet_type or 'metamask',
                        'created_at': datetime.now().isoformat(),
                        'timestamp': int(time.time())
                    })
                except Exception as db_error:
                    print(f"Warning: Could not store CDP session: {str(db_error)}")
            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
            
            return {
                'success': True,
                'cdp_connected': True,
                'wallet_address': wallet_address,
                'wallet_type': wallet_type,
                'cdp_session': connection_result.get('cdp_session'),
                'message': f"Your {wallet_type or 'wallet'} has been successfully connected to CDP!",
                'timestamp': connection_result.get('timestamp', int(time.time()))
            }
        else:
            return {
                'success': False,
                'cdp_connected': False,
                'error': connection_result.get('error', 'Failed to connect to CDP')
            }
    except Exception as e:
        return {
            'success': False,
            'cdp_connected': False,
            'error': f"CDP connection error: {str(e)}"
        }

def process_cdp_transaction(wallet_address, amount, currency="ETH", transaction_type="payment"):
    """
    Process a transaction through the CDP wallet
    
    Args:
        wallet_address: The wallet address to use
        amount: The amount to transact
        currency: The currency (default ETH)
        transaction_type: The type of transaction
        
    Returns:
        dict: Transaction result
    """
    try:
        transaction_result = execute_cdp_transaction(wallet_address, amount, currency)
        
        if transaction_result.get('transaction_id'):
            # Store transaction in DynamoDB if available
            try:
                dynamodb = boto3.resource('dynamodb')
                table_name = os.environ.get('TRANSACTION_TABLE_NAME', 'NFTPaymentTransactions')
                
                try:
                    table = dynamodb.Table(table_name)
                    table.put_item(Item={
                        'transaction_id': transaction_result.get('transaction_id'),
                        'wallet_address': wallet_address,
                        'amount': amount,
                        'currency': currency,
                        'payment_method': 'cdp',
                        'status': transaction_result.get('status', 'pending'),
                        'created_at': datetime.now().isoformat(),
                        'timestamp': int(time.time())
                    })
                except Exception as db_error:
                    print(f"Warning: Could not store CDP transaction: {str(db_error)}")
            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
            
            return {
                'success': True,
                'transaction_id': transaction_result.get('transaction_id'),
                'status': transaction_result.get('status', 'pending'),
                'amount': amount,
                'currency': currency,
                'timestamp': transaction_result.get('timestamp', int(time.time()))
            }
        else:
            return {
                'success': False,
                'error': transaction_result.get('error', 'Failed to execute CDP transaction')
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"CDP transaction error: {str(e)}"
        }

def get_cdp_wallet_info(wallet_address):
    """
    Get CDP wallet information
    
    Args:
        wallet_address: The wallet address to check
        
    Returns:
        dict: Wallet information
    """
    try:
        # Get balance from CDP
        balance_result = get_cdp_balance(wallet_address)
        
        if balance_result.get('balances'):
            # Get CDP session info from DynamoDB if available
            session_info = {}
            try:
                dynamodb = boto3.resource('dynamodb')
                table_name = os.environ.get('CDP_SESSIONS_TABLE', 'CDPWalletSessions')
                
                try:
                    table = dynamodb.Table(table_name)
                    response = table.get_item(Key={'wallet_address': wallet_address})
                    if 'Item' in response:
                        session_info = {
                            'cdp_session': response['Item'].get('cdp_session'),
                            'wallet_type': response['Item'].get('wallet_type'),
                            'created_at': response['Item'].get('created_at')
                        }
                except Exception as db_error:
                    print(f"Warning: Could not retrieve CDP session: {str(db_error)}")
            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
            
            return {
                'success': True,
                'wallet_address': wallet_address,
                'balances': balance_result.get('balances', []),
                'is_cdp_connected': True,
                'session_info': session_info,
                'timestamp': balance_result.get('timestamp', int(time.time()))
            }
        else:
            return {
                'success': False,
                'error': balance_result.get('error', 'Failed to get CDP wallet information')
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"CDP wallet info error: {str(e)}"
        }
