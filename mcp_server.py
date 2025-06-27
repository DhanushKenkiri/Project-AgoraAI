"""
NFT Payment System - Model Context Protocol (MCP) Server

This module implements a Model Context Protocol server for the NFT payment system.
The MCP server exposes wallet login, NFT queries, and payment functions through
a standardized API that can be used by AI agents and other services.
"""

import json
import os
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

try:
    import fastapi
    from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("FastAPI not installed. Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "fastapi", "uvicorn"])
    import fastapi
    from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

# Import core functions
try:
    from wallet_login import wallet_login, get_wallet_info
    from nft_wallet import get_wallet_nfts, get_wallet_details
    from x402_payment_handler import handle_payment_request
    from lambda_handler import handle_transaction_status
except ImportError:
    # Mock implementations for testing
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

# Create FastAPI app
app = FastAPI(
    title="NFT Payment MCP Server",
    description="Model Context Protocol server for the NFT payment system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MCP Protocol Models ---

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

# --- Function Parameter Models ---

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

# --- API Routes ---

@app.get("/")
async def root():
    return {"message": "NFT Payment MCP Server is running"}

@app.get("/mcp/health")
async def health():
    return {"status": "ok"}

@app.get("/mcp/manifest")
async def get_manifest():
    """Get the MCP manifest describing capabilities and functions"""
    return {
        "name": "NFT Payment System",
        "description": "NFT Payment and Wallet Management System",
        "capabilities": [
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
                    },
                    {
                        "name": "check_transaction",
                        "description": "Check transaction status",
                        "parameters": [
                            {
                                "name": "transaction_id",
                                "type": "string",
                                "description": "Transaction ID to check",
                                "required": True
                            }
                        ]
                    }
                ]
            },
            {
                "name": "nft",
                "description": "NFT query capabilities",
                "functions": [
                    {
                        "name": "query_nft",
                        "description": "Query NFT information",
                        "parameters": [
                            {
                                "name": "collection",
                                "type": "string",
                                "description": "NFT collection name or slug",
                                "required": True
                            },
                            {
                                "name": "chain",
                                "type": "string",
                                "description": "Blockchain (e.g., ethereum)",
                                "required": True
                            },
                            {
                                "name": "token_id",
                                "type": "string",
                                "description": "NFT token ID",
                                "required": False
                            }
                        ]
                    }
                ]
            }
        ]
    }

@app.post("/mcp/call")
async def call_function(function_call: MCPFunctionCall):
    """
    Execute a function via MCP protocol
    """
    try:
        function_name = function_call.function_name
        params = function_call.parameters
        
        if function_name == "wallet_login":
            result = wallet_login(params.get("wallet_address"), params.get("wallet_type"))
        elif function_name == "get_wallet_info":
            result = get_wallet_info(params.get("wallet_address"))
        elif function_name == "get_wallet_nfts":
            result = get_wallet_nfts(params.get("wallet_address"))
        elif function_name == "process_payment":
            # Format the payment request as expected by handle_payment_request
            payment_event = {
                "body": {
                    "amount": params.get("amount"),
                    "currency": params.get("currency", "ETH"),
                    "paymentReason": params.get("payment_reason"),
                    "x402": {
                        "payment_type": "x402",
                        "wallet_address": params.get("wallet_address"),
                        "contract_address": params.get("contract_address", "0x123abc")
                    }
                }
            }
            result = handle_payment_request(payment_event)
        elif function_name == "check_transaction":
            transaction_event = {
                "queryStringParameters": {
                    "transaction_id": params.get("transaction_id")
                }
            }
            result = handle_transaction_status(transaction_event)
        elif function_name == "query_nft":
            # Mock implementation for NFT query - in production, you'd import the actual function
            # For now, returning a placeholder
            result = {
                "success": True,
                "collection": params.get("collection"),
                "chain": params.get("chain"),
                "token_id": params.get("token_id"),
                "data": {
                    "message": "NFT data would be returned here"
                }
            }
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                },
                status_code=400
            )
        
        return JSONResponse(content={"success": True, "result": result})
    
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

# --- Individual Endpoint Routes ---

@app.post("/mcp/wallet_login")
async def mcp_wallet_login(req: WalletLoginRequest):
    result = wallet_login(req.wallet_address, req.wallet_type)
    return JSONResponse(content=result)

@app.post("/mcp/get_wallet_info")
async def mcp_get_wallet_info(req: WalletInfoRequest):
    result = get_wallet_info(req.wallet_address)
    return JSONResponse(content=result)

@app.post("/mcp/get_wallet_nfts")
async def mcp_get_wallet_nfts(req: WalletNFTsRequest):
    result = get_wallet_nfts(req.wallet_address)
    return JSONResponse(content=result)

@app.post("/wallet/login")
async def endpoint_wallet_login(params: WalletLoginRequest):
    """Connect a wallet and create a session"""
    try:
        result = wallet_login(params.wallet_address, params.wallet_type)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/wallet/info")
async def endpoint_wallet_info(wallet_address: str = Query(...)):
    """Get wallet information"""
    try:
        result = get_wallet_info(wallet_address)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/wallet/nfts")
async def endpoint_wallet_nfts(wallet_address: str = Query(...)):
    """Get NFTs owned by a wallet"""
    try:
        result = get_wallet_nfts(wallet_address)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/payment/init")
async def endpoint_process_payment(params: PaymentParams):
    """Process a payment"""
    try:
        payment_event = {
            "body": {
                "amount": params.amount,
                "currency": params.currency,
                "paymentReason": params.payment_reason,
                "x402": {
                    "payment_type": "x402",
                    "wallet_address": params.wallet_address,
                    "contract_address": params.contract_address or "0x123abc"
                }
            }
        }
        result = handle_payment_request(payment_event)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/transaction/status")
async def endpoint_transaction_status(transaction_id: str = Query(...)):
    """Check transaction status"""
    try:
        transaction_event = {
            "queryStringParameters": {
                "transaction_id": transaction_id
            }
        }
        result = handle_transaction_status(transaction_event)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/nft/query")
async def endpoint_query_nft(params: NFTQueryParams):
    """Query NFT information"""
    try:
        # This would connect to your actual NFT query implementation
        # For now, returning a placeholder
        result = {
            "success": True,
            "collection": params.collection,
            "chain": params.chain,
            "token_id": params.token_id,
            "data": {
                "message": "NFT data would be returned here"
            }
        }
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    # Run the server if executed directly
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, reload=True)
