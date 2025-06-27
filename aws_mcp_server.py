"""
NFT Payment System - AWS-optimized Model Context Protocol (MCP) Server

This module extends the base MCP server with AWS-specific optimizations and 
adds interactive payment popups and user input capabilities. This server
is designed to be deployed on AWS Lambda or EC2 and integrates with AWS services.
"""

import os
import json
import time
import uuid
import base64
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Warning: boto3 not installed. AWS integration will be limited.")
    boto3 = None

# FastAPI imports
try:
    import fastapi
    from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query, Form
    from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
except ImportError:
    print("FastAPI not installed. Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "fastapi", "uvicorn", "jinja2", "aiofiles"])
    import fastapi
    from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query, Form
    from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

# Import core MCP server
try:
    from mcp_server import app as base_mcp_app
    # Import the models from the base MCP server
    from mcp_server import (
        MCPFunctionParameter, MCPFunction, MCPCapability,
        MCPManifest, MCPFunctionCall, MCPFunctionResult,
        WalletLoginRequest, WalletInfoRequest, WalletNFTsRequest,
        PaymentParams, TransactionParams, NFTQueryParams
    )
    # Use existing implementation as a base
    app = base_mcp_app
    print("Extending existing MCP server with AWS optimizations and payment UI...")
except ImportError:
    # If base MCP server is not available, create a new FastAPI app
    print("Base MCP server not found. Creating new AWS MCP server...")
    app = FastAPI(
        title="AWS NFT Payment MCP Server",
        description="AWS-optimized Model Context Protocol server for NFT payments with interactive UI",
        version="1.0.0"
    )
    
    # Define models that would normally be imported from mcp_server.py
    from pydantic import BaseModel, Field
    
    class MCPFunctionParameter(BaseModel):
        name: str
        type: str
        description: str
        required: bool = True

    class MCPFunction(BaseModel):
        name: str
        description: str
        parameters: List[MCPFunctionParameter]

    class MCPCapability(BaseModel):
        name: str
        description: str
        functions: List[MCPFunction]

    class MCPManifest(BaseModel):
        name: str
        description: str
        capabilities: List[MCPCapability]

    class MCPFunctionCall(BaseModel):
        function_name: str
        parameters: Dict[str, Any]

    class MCPFunctionResult(BaseModel):
        success: bool
        result: Any
        error: Optional[str] = None

    class WalletLoginRequest(BaseModel):
        wallet_address: str
        wallet_type: Optional[str] = None

    class WalletInfoRequest(BaseModel):
        wallet_address: str

    class WalletNFTsRequest(BaseModel):
        wallet_address: str

    class PaymentParams(BaseModel):
        amount: str
        currency: str = "ETH"
        payment_reason: str
        wallet_address: str
        contract_address: Optional[str] = None
        redirect_url: Optional[str] = None

    class TransactionParams(BaseModel):
        transaction_id: str

    class NFTQueryParams(BaseModel):
        collection: str
        chain: str = "ethereum"
        token_id: Optional[str] = None
        includeMetadata: Optional[bool] = False

# Import wallet and payment functions
try:
    from wallet_login import wallet_login, get_wallet_info
    from nft_wallet import get_wallet_nfts, get_wallet_details
    from x402_payment_handler import handle_payment_request
    from lambda_handler import handle_transaction_status
except ImportError:
    print("Warning: Core functions not found, using mock implementations")
    
    def wallet_login(wallet_address, wallet_type=None):
        return {
            "success": True, 
            "wallet_address": wallet_address,
            "wallet_type": wallet_type,
            "session_token": f"mock-session-{str(uuid.uuid4())[:8]}",
            "expiration": int(time.time()) + 3600
        }
    
    def get_wallet_info(wallet_address):
        return {
            "success": True, 
            "wallet": {
                "address": wallet_address,
                "balances": [{"token": "ETH", "balance": "0.5"}]
            }
        }
    
    def get_wallet_nfts(wallet_address):
        return {
            "success": True, 
            "nfts": [
                {"collection": "Bored Ape Yacht Club", "token_id": "1234"}
            ]
        }
    
    def get_wallet_details(wallet_address):
        return {
            "success": True,
            "wallet_address": wallet_address,
            "balance": "0.5",
            "nft_count": 1
        }
    
    def handle_payment_request(event):
        return {
            "success": True,
            "transaction_id": f"mock-tx-{str(uuid.uuid4())[:8]}",
            "amount": event.get('body', {}).get('amount', '0.005'),
            "currency": event.get('body', {}).get('currency', 'ETH')
        }
    
    def handle_transaction_status(event):
        tx_id = event.get('queryStringParameters', {}).get('transaction_id', 'unknown')
        return {
            "success": True,
            "transaction_id": tx_id,
            "status": "completed"
        }

# AWS integration helpers
def get_aws_session():
    """Get an AWS session with appropriate credentials"""
    if boto3 is None:
        return None
    
    try:
        return boto3.Session()
    except Exception as e:
        print(f"Error creating AWS session: {str(e)}")
        return None

def get_aws_secret(secret_name):
    """
    Retrieve a secret from AWS Secrets Manager
    """
    if boto3 is None:
        return None
    
    session = get_aws_session()
    if not session:
        return None
    
    try:
        client = session.client(service_name='secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            return base64.b64decode(response['SecretBinary'])
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {str(e)}")
        return None

def save_to_dynamodb(table_name, item):
    """Save an item to a DynamoDB table"""
    if boto3 is None:
        return False
    
    session = get_aws_session()
    if not session:
        return False
    
    try:
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error saving to DynamoDB table {table_name}: {str(e)}")
        return False

def get_from_dynamodb(table_name, key_name, key_value):
    """Get an item from a DynamoDB table"""
    if boto3 is None:
        return None
    
    session = get_aws_session()
    if not session:
        return None
    
    try:
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={key_name: key_value})
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving from DynamoDB table {table_name}: {str(e)}")
        return None

# Setup UI templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

try:
    templates = Jinja2Templates(directory=templates_dir)
except Exception as e:
    print(f"Error setting up templates: {str(e)}")
    templates = None

# Create static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Set up CORS middleware if not already set up
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to use static files if available
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {str(e)}")

# Enhanced models for UI interaction
class UIPaymentRequest(BaseModel):
    amount: str
    currency: str = "ETH"
    payment_reason: str
    wallet_address: Optional[str] = None
    contract_address: Optional[str] = None
    redirect_url: Optional[str] = None
    callback_url: Optional[str] = None
    cancel_url: Optional[str] = None

class UIWalletRequest(BaseModel):
    redirect_url: Optional[str] = None
    callback_url: Optional[str] = None
    cancel_url: Optional[str] = None

class WalletSession(BaseModel):
    session_id: str
    wallet_address: Optional[str] = None
    wallet_type: Optional[str] = None
    created_at: int
    expires_at: int
    status: str = "pending"

# AWS-specific enhanced endpoints
@app.get("/aws/health")
async def aws_health():
    """AWS health check endpoint"""
    aws_connected = get_aws_session() is not None
    return {
        "status": "ok",
        "aws_connected": aws_connected,
        "timestamp": int(time.time())
    }

# Payment UI endpoints
@app.get("/ui/payment", response_class=HTMLResponse)
async def payment_ui(
    request: Request,
    amount: Optional[str] = None,
    currency: Optional[str] = "ETH",
    payment_reason: Optional[str] = "NFT Payment",
    redirect_url: Optional[str] = None,
    callback_url: Optional[str] = None,
    cancel_url: Optional[str] = None
):
    """
    Payment UI page that can be embedded or opened in a popup
    """
    if templates is None:
        return HTMLResponse(content=get_payment_html_template(
            amount=amount,
            currency=currency, 
            payment_reason=payment_reason,
            redirect_url=redirect_url,
            callback_url=callback_url,
            cancel_url=cancel_url
        ))
    
    return templates.TemplateResponse(
        "payment.html", 
        {
            "request": request,
            "amount": amount,
            "currency": currency,
            "payment_reason": payment_reason,
            "redirect_url": redirect_url,
            "callback_url": callback_url,
            "cancel_url": cancel_url
        }
    )

@app.get("/ui/wallet", response_class=HTMLResponse)
async def wallet_ui(
    request: Request,
    session_id: Optional[str] = None,
    redirect_url: Optional[str] = None,
    callback_url: Optional[str] = None,
    cancel_url: Optional[str] = None
):
    """
    Wallet UI page that can be embedded or opened in a popup
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Create a wallet session
    wallet_session = {
        "session_id": session_id,
        "created_at": int(time.time()),
        "expires_at": int(time.time()) + 3600,  # 1 hour expiration
        "status": "pending"
    }
    
    # Save the session to DynamoDB if available
    wallet_sessions_table = os.environ.get("WALLET_SESSIONS_TABLE", "NFTWalletSessions")
    save_to_dynamodb(wallet_sessions_table, wallet_session)
    
    if templates is None:
        return HTMLResponse(content=get_wallet_html_template(
            session_id=session_id,
            redirect_url=redirect_url,
            callback_url=callback_url,
            cancel_url=cancel_url
        ))
    
    return templates.TemplateResponse(
        "wallet.html", 
        {
            "request": request,
            "session_id": session_id,
            "redirect_url": redirect_url,
            "callback_url": callback_url,
            "cancel_url": cancel_url
        }
    )

@app.post("/ui/wallet/connect")
async def connect_wallet_ui(
    wallet_address: str = Form(...),
    wallet_type: str = Form(...),
    session_id: str = Form(...),
    redirect_url: Optional[str] = Form(None)
):
    """
    Connect wallet endpoint for the UI
    """
    # Call the wallet login function
    result = wallet_login(wallet_address, wallet_type)
    
    # Update the session in DynamoDB if available
    if result.get("success"):
        wallet_session = {
            "session_id": session_id,
            "wallet_address": wallet_address,
            "wallet_type": wallet_type,
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + 3600,  # 1 hour expiration
            "status": "connected"
        }
        
        wallet_sessions_table = os.environ.get("WALLET_SESSIONS_TABLE", "NFTWalletSessions")
        save_to_dynamodb(wallet_sessions_table, wallet_session)
    
    # If redirect_url is provided, redirect to it
    if redirect_url and result.get("success"):
        return RedirectResponse(url=f"{redirect_url}?session_id={session_id}&wallet_address={wallet_address}&status=success")
    
    # Otherwise, return the result as JSON
    return JSONResponse(content=result)

@app.post("/ui/payment/process")
async def process_payment_ui(
    amount: str = Form(...),
    currency: str = Form(...),
    payment_reason: str = Form(...),
    wallet_address: str = Form(...),
    redirect_url: Optional[str] = Form(None)
):
    """
    Process payment endpoint for the UI
    """
    # Create the payment event
    payment_event = {
        "body": {
            "amount": amount,
            "currency": currency,
            "paymentReason": payment_reason,
            "x402": {
                "payment_type": "x402",
                "wallet_address": wallet_address
            }
        }
    }
    
    # Call the payment handler
    result = handle_payment_request(payment_event)
    
    # If redirect_url is provided, redirect to it
    if redirect_url and result.get("success"):
        transaction_id = result.get("transaction_id", "unknown")
        return RedirectResponse(url=f"{redirect_url}?transaction_id={transaction_id}&status=success")
    
    # Otherwise, return the result as JSON
    return JSONResponse(content=result)

@app.get("/ui/wallet/status")
async def check_wallet_session(session_id: str):
    """
    Check wallet session status
    """
    wallet_sessions_table = os.environ.get("WALLET_SESSIONS_TABLE", "NFTWalletSessions")
    session_data = get_from_dynamodb(wallet_sessions_table, "session_id", session_id)
    
    if not session_data:
        return JSONResponse(content={"success": False, "error": "Session not found"})
    
    # Check if the session has a connected wallet
    if session_data.get("status") == "connected" and session_data.get("wallet_address"):
        return JSONResponse(content={
            "success": True,
            "status": "connected",
            "wallet_address": session_data.get("wallet_address"),
            "wallet_type": session_data.get("wallet_type")
        })
    
    return JSONResponse(content={
        "success": True,
        "status": session_data.get("status", "pending")
    })

# --- MCP API Enhancements ---

@app.post("/mcp/popup")
async def mcp_popup(function_call: MCPFunctionCall):
    """
    Execute a function that requires a popup UI interaction
    Returns a URL that can be displayed in a popup or iframe
    """
    function_name = function_call.function_name
    params = function_call.parameters
    
    if function_name == "payment_popup":
        # Generate a payment UI URL
        amount = params.get("amount", "0.01")
        currency = params.get("currency", "ETH")
        payment_reason = params.get("payment_reason", "NFT Payment")
        redirect_url = params.get("redirect_url")
        callback_url = params.get("callback_url")
        cancel_url = params.get("cancel_url")
        
        # Base URL for the payment UI
        server_url = os.environ.get("SERVER_URL", "http://localhost:8000")
        payment_url = f"{server_url}/ui/payment?amount={amount}&currency={currency}&payment_reason={payment_reason}"
        
        if redirect_url:
            payment_url += f"&redirect_url={redirect_url}"
        if callback_url:
            payment_url += f"&callback_url={callback_url}"
        if cancel_url:
            payment_url += f"&cancel_url={cancel_url}"
        
        return JSONResponse(content={
            "success": True,
            "popup_type": "payment",
            "url": payment_url
        })
    
    elif function_name == "wallet_popup":
        # Generate a wallet UI URL
        session_id = str(uuid.uuid4())
        redirect_url = params.get("redirect_url")
        callback_url = params.get("callback_url")
        cancel_url = params.get("cancel_url")
        
        # Base URL for the wallet UI
        server_url = os.environ.get("SERVER_URL", "http://localhost:8000")
        wallet_url = f"{server_url}/ui/wallet?session_id={session_id}"
        
        if redirect_url:
            wallet_url += f"&redirect_url={redirect_url}"
        if callback_url:
            wallet_url += f"&callback_url={callback_url}"
        if cancel_url:
            wallet_url += f"&cancel_url={cancel_url}"
        
        return JSONResponse(content={
            "success": True,
            "popup_type": "wallet",
            "url": wallet_url,
            "session_id": session_id
        })
    
    else:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Unknown function: {function_name}"
            },
            status_code=400
        )

# --- HTML Templates ---

def get_payment_html_template(
    amount=None,
    currency="ETH",
    payment_reason="NFT Payment",
    redirect_url=None,
    callback_url=None,
    cancel_url=None
):
    """Generate HTML template for payment UI"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>NFT Payment</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 500px;
            padding: 30px;
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #222;
            text-align: center;
        }}
        .payment-details {{
            margin-bottom: 25px;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            background-color: #f9f9f9;
        }}
        .payment-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        .payment-label {{
            color: #666;
        }}
        .payment-value {{
            font-weight: bold;
            color: #333;
        }}
        .divider {{
            height: 1px;
            background-color: #eee;
            margin: 15px 0;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        input, select {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }}
        button {{
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 14px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        button:hover {{
            background-color: #1d4ed8;
        }}
        .cancel-link {{
            display: block;
            text-align: center;
            margin-top: 15px;
            color: #666;
            text-decoration: none;
        }}
        .cancel-link:hover {{
            text-decoration: underline;
        }}
        .wallet-info {{
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Complete Your Payment</h1>
        
        <div class="payment-details">
            <div class="payment-row">
                <div class="payment-label">Amount:</div>
                <div class="payment-value">{amount} {currency}</div>
            </div>
            <div class="payment-row">
                <div class="payment-label">Purpose:</div>
                <div class="payment-value">{payment_reason}</div>
            </div>
        </div>
        
        <form id="payment-form" action="/ui/payment/process" method="post">
            <input type="hidden" name="amount" value="{amount}">
            <input type="hidden" name="currency" value="{currency}">
            <input type="hidden" name="payment_reason" value="{payment_reason}">
            <input type="hidden" name="redirect_url" value="{redirect_url or ''}">
            
            <div class="form-group">
                <label for="wallet-address">Your Wallet Address</label>
                <input type="text" id="wallet-address" name="wallet_address" placeholder="0x..." required>
            </div>
            
            <div class="form-group">
                <label for="wallet-type">Wallet Type</label>
                <select id="wallet-type" name="wallet_type">
                    <option value="metamask">MetaMask</option>
                    <option value="coinbase">Coinbase Wallet</option>
                    <option value="walletconnect">WalletConnect</option>
                </select>
            </div>
            
            <button type="submit">Complete Payment</button>
        </form>
        
        <a href="{cancel_url or '#'}" class="cancel-link" id="cancel-link">Cancel Payment</a>
        
        <div class="wallet-info">
            <button type="button" id="connect-wallet-btn" style="background-color: #4c1d95;">Connect Wallet</button>
        </div>
    </div>
    
    <script>
        document.getElementById('connect-wallet-btn').addEventListener('click', function() {{
            // In a real implementation, this would connect to MetaMask or other wallets
            if (typeof window.ethereum !== 'undefined') {{
                ethereum.request({{ method: 'eth_requestAccounts' }})
                    .then(accounts => {{
                        document.getElementById('wallet-address').value = accounts[0];
                        alert('Wallet connected: ' + accounts[0]);
                    }})
                    .catch(error => {{
                        console.error('Error connecting wallet:', error);
                        alert('Error connecting wallet');
                    }});
            }} else {{
                alert('MetaMask is not installed. Please install MetaMask or enter your wallet address manually.');
            }}
        }});
        
        // Handle cancel
        const cancelLink = document.getElementById('cancel-link');
        cancelLink.addEventListener('click', function(e) {{
            if (!cancelLink.getAttribute('href') || cancelLink.getAttribute('href') === '#') {{
                e.preventDefault();
                window.close();
            }}
        }});
    </script>
</body>
</html>"""

def get_wallet_html_template(
    session_id=None,
    redirect_url=None,
    callback_url=None,
    cancel_url=None
):
    """Generate HTML template for wallet UI"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Connect Your Wallet</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 500px;
            padding: 30px;
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #222;
            text-align: center;
        }}
        .wallet-options {{
            margin: 25px 0;
        }}
        .wallet-button {{
            display: flex;
            align-items: center;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }}
        .wallet-button:hover {{
            border-color: #3b82f6;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        }}
        .wallet-icon {{
            width: 40px;
            height: 40px;
            margin-right: 15px;
        }}
        .wallet-name {{
            font-size: 18px;
            font-weight: 600;
        }}
        .form-section {{
            margin-top: 30px;
            display: none;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }}
        button {{
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 14px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        button:hover {{
            background-color: #1d4ed8;
        }}
        .cancel-link {{
            display: block;
            text-align: center;
            margin-top: 15px;
            color: #666;
            text-decoration: none;
        }}
        .cancel-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Connect Your Wallet</h1>
        
        <div class="wallet-options">
            <button class="wallet-button" id="metamask-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/3/36/MetaMask_Fox.svg" alt="MetaMask" class="wallet-icon">
                <span class="wallet-name">MetaMask</span>
            </button>
            
            <button class="wallet-button" id="coinbase-btn">
                <img src="https://seeklogo.com/images/C/coinbase-coin-logo-C86F46D7B8-seeklogo.com.png" alt="Coinbase" class="wallet-icon">
                <span class="wallet-name">Coinbase Wallet</span>
            </button>
            
            <button class="wallet-button" id="walletconnect-btn">
                <img src="https://avatars.githubusercontent.com/u/37784886" alt="WalletConnect" class="wallet-icon">
                <span class="wallet-name">WalletConnect</span>
            </button>
        </div>
        
        <div id="manual-form" class="form-section">
            <form id="wallet-form" action="/ui/wallet/connect" method="post">
                <input type="hidden" id="wallet-type" name="wallet_type" value="metamask">
                <input type="hidden" name="session_id" value="{session_id}">
                <input type="hidden" name="redirect_url" value="{redirect_url or ''}">
                
                <div class="form-group">
                    <label for="wallet-address">Your Wallet Address</label>
                    <input type="text" id="wallet-address" name="wallet_address" placeholder="0x..." required>
                </div>
                
                <button type="submit">Connect Wallet</button>
            </form>
        </div>
        
        <a href="{cancel_url or '#'}" class="cancel-link" id="cancel-link">Cancel</a>
    </div>
    
    <script>
        let selectedWalletType = 'metamask';
        const formSection = document.getElementById('manual-form');
        const walletTypeInput = document.getElementById('wallet-type');
        
        // Wallet button event listeners
        document.getElementById('metamask-btn').addEventListener('click', function() {{
            connectWallet('metamask');
        }});
        
        document.getElementById('coinbase-btn').addEventListener('click', function() {{
            connectWallet('coinbase');
        }});
        
        document.getElementById('walletconnect-btn').addEventListener('click', function() {{
            connectWallet('walletconnect');
        }});
        
        function connectWallet(walletType) {{
            selectedWalletType = walletType;
            walletTypeInput.value = walletType;
            
            // Show the form
            formSection.style.display = 'block';
            
            // Try to connect to wallet if it's MetaMask
            if (walletType === 'metamask' && typeof window.ethereum !== 'undefined') {{
                ethereum.request({{ method: 'eth_requestAccounts' }})
                    .then(accounts => {{
                        document.getElementById('wallet-address').value = accounts[0];
                        
                        // Auto-submit the form
                        document.getElementById('wallet-form').submit();
                    }})
                    .catch(error => {{
                        console.error('Error connecting wallet:', error);
                        alert('Error connecting wallet. Please enter your address manually.');
                    }});
            }}
            // Basic Coinbase Wallet connectivity (would use their SDK in production)
            else if (walletType === 'coinbase' && typeof window.coinbaseWalletExtension !== 'undefined') {{
                // Similar to MetaMask but using Coinbase's API
                alert('Please enter your Coinbase wallet address manually');
            }}
            else {{
                // For other wallets or if browser extensions not available
                alert('Please enter your wallet address manually');
            }}
        }}
        
        // Handle cancel
        const cancelLink = document.getElementById('cancel-link');
        cancelLink.addEventListener('click', function(e) {{
            if (!cancelLink.getAttribute('href') || cancelLink.getAttribute('href') === '#') {{
                e.preventDefault();
                window.close();
            }}
        }});
    </script>
</body>
</html>"""

# Add AWS-specific manifest endpoints
@app.get("/aws/manifest")
async def get_aws_manifest():
    """Get the AWS-enhanced MCP manifest"""
    manifest = {
        "name": "AWS NFT Payment System",
        "description": "AWS-optimized Model Context Protocol server for NFT payments with interactive UI",
        "capabilities": [
            # Include existing capabilities from base MCP
            {
                "name": "wallet",
                "description": "Wallet management capabilities",
                "functions": [
                    {
                        "name": "wallet_login",
                        "description": "Connect a user's wallet and create a session",
                        "parameters": [
                            {
                                "name": "wallet_address",
                                "type": "string",
                                "description": "The user's wallet address",
                                "required": True
                            },
                            {
                                "name": "wallet_type",
                                "type": "string",
                                "description": "Type of wallet (metamask or coinbase)",
                                "required": False
                            }
                        ]
                    },
                    {
                        "name": "get_wallet_info",
                        "description": "Get information about a wallet",
                        "parameters": [
                            {
                                "name": "wallet_address",
                                "type": "string",
                                "description": "The wallet address",
                                "required": True
                            }
                        ]
                    },
                    {
                        "name": "get_wallet_nfts",
                        "description": "Get NFTs owned by a wallet",
                        "parameters": [
                            {
                                "name": "wallet_address",
                                "type": "string",
                                "description": "The wallet address",
                                "required": True
                            }
                        ]
                    }
                ]
            },
            {
                "name": "payment",
                "description": "Payment processing capabilities",
                "functions": [
                    {
                        "name": "process_payment",
                        "description": "Process a payment",
                        "parameters": [
                            {
                                "name": "amount",
                                "type": "string",
                                "description": "Payment amount",
                                "required": True
                            },
                            {
                                "name": "currency",
                                "type": "string",
                                "description": "Payment currency (e.g., ETH)",
                                "required": True
                            },
                            {
                                "name": "payment_reason",
                                "type": "string",
                                "description": "Reason for the payment",
                                "required": True
                            },
                            {
                                "name": "wallet_address",
                                "type": "string",
                                "description": "Sender wallet address",
                                "required": True
                            },
                            {
                                "name": "contract_address",
                                "type": "string",
                                "description": "NFT contract address if applicable",
                                "required": False
                            }
                        ]
                    }
                ]
            },
            # Add AWS-specific UI capabilities
            {
                "name": "ui",
                "description": "Interactive UI capabilities",
                "functions": [
                    {
                        "name": "payment_popup",
                        "description": "Create a payment popup UI",
                        "parameters": [
                            {
                                "name": "amount",
                                "type": "string",
                                "description": "Payment amount",
                                "required": True
                            },
                            {
                                "name": "currency",
                                "type": "string",
                                "description": "Payment currency (e.g., ETH)",
                                "required": True
                            },
                            {
                                "name": "payment_reason",
                                "type": "string",
                                "description": "Reason for the payment",
                                "required": True
                            },
                            {
                                "name": "redirect_url",
                                "type": "string",
                                "description": "URL to redirect after successful payment",
                                "required": False
                            },
                            {
                                "name": "callback_url",
                                "type": "string",
                                "description": "URL to call with payment result",
                                "required": False
                            },
                            {
                                "name": "cancel_url",
                                "type": "string",
                                "description": "URL to redirect if payment is cancelled",
                                "required": False
                            }
                        ]
                    },
                    {
                        "name": "wallet_popup",
                        "description": "Create a wallet connection popup UI",
                        "parameters": [
                            {
                                "name": "redirect_url",
                                "type": "string",
                                "description": "URL to redirect after successful connection",
                                "required": False
                            },
                            {
                                "name": "callback_url",
                                "type": "string",
                                "description": "URL to call with wallet connection result",
                                "required": False
                            },
                            {
                                "name": "cancel_url",
                                "type": "string",
                                "description": "URL to redirect if wallet connection is cancelled",
                                "required": False
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return JSONResponse(content=manifest)

# Main entry point
if __name__ == "__main__":
    # Run the server if executed directly
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("aws_mcp_server:app", host="0.0.0.0", port=port, reload=True)
