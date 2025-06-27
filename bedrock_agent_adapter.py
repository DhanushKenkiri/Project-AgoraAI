"""
AWS Bedrock Agent Integration for NFT Payment System

This module adapts the AWS MCP server to work with AWS Bedrock Agents.
It translates between Bedrock agent requests and our existing MCP endpoints.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bedrock_agent_adapter")

# Import session manager for persistent wallet storage
try:
    from session_manager import get_wallet_address, store_wallet_address
except ImportError:
    logger.warning("Could not import session_manager module, using mocks")
    def get_wallet_address(session_id, user_id=None):
        return None
    def store_wallet_address(session_id, wallet_address, user_id=None):
        return True

# Mock imports for testing
try:
    from wallet_login import wallet_login, get_wallet_info
except ImportError:
    logger.warning("Could not import wallet_login module, using mocks")
    def wallet_login(wallet_address):
        return {"success": True, "wallet_address": wallet_address, "message": "Mock wallet login successful"}
    def get_wallet_info(wallet_address):
        return {"success": True, "wallet_address": wallet_address, "balance": "0.5 ETH"}

try:
    from nft_wallet import get_wallet_nfts, get_wallet_details
except ImportError:
    logger.warning("Could not import nft_wallet module, using mocks")
    def get_wallet_nfts(wallet_address):
        return {"success": True, "nfts": [{"id": "1", "name": "MockNFT", "contract": "0x123"}]}
    def get_wallet_details(wallet_address):
        return {"success": True, "wallet_address": wallet_address, "balance": "0.5 ETH"}

try:
    from x402_payment_handler import handle_payment_request
except ImportError:
    logger.warning("Could not import x402_payment_handler, using mocks")
    def handle_payment_request(params):
        return {"success": True, "payment": "Processing", "transaction_id": "0x123abc"}

try:
    from lambda_handler import handle_transaction_status
except ImportError:
    logger.warning("Could not import handle_transaction_status, using mocks")
    def handle_transaction_status(event):
        return {"success": True, "status": "pending"}

# Try to import AWS MCP server components
try:
    from aws_mcp_server import app as mcp_app
except ImportError as e:
    logger.warning(f"Could not import MCP server app: {e}")

# Bedrock agent action group mapping
ACTION_GROUP_MAP = {
    "NFTPaymentActions": {
        "wallet_login": lambda params: wallet_login_with_session(params),
        "get_wallet_info": lambda params: get_wallet_info_with_session(params),
        "get_wallet_nfts": lambda params: get_wallet_nfts_with_session(params),
        "process_payment": lambda params: process_payment_with_session(params),
        "check_transaction": lambda params: handle_transaction_status({
            "queryStringParameters": {
                "transaction_id": params.get("transaction_id")
            }
        })
    }
}

def parse_bedrock_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the AWS Bedrock agent request
    
    Args:
        event: The Lambda event from Bedrock agent
        
    Returns:
        Dict containing the parsed request information
    """
    logger.info(f"Received Bedrock agent request: {json.dumps(event)}")
    
    try:
        # Extract action group and API details
        request_body = event.get("requestBody", {})
        api_path = request_body.get("apiPath", "")
        action_group = request_body.get("actionGroup", "")
        parameters = {}
        
        # Extract session information
        session_id = event.get("sessionId")
        if session_id:
            logger.info(f"Found session ID in request: {session_id}")
            parameters["session_id"] = session_id
            
        # Extract user ID if available (for multi-user scenarios)
        user_id = event.get("userId")
        if user_id:
            logger.info(f"Found user ID in request: {user_id}")
            parameters["user_id"] = user_id
            
        # Extract parameters
        if "parameters" in request_body:
            for param in request_body.get("parameters", []):
                name = param.get("name", "")
                value = param.get("value", "")
                parameters[name] = value
        
        # Extract from body if parameters are not in the standard format
        body = {}
        if "body" in request_body:
            try:
                if isinstance(request_body.get("body"), str):
                    body = json.loads(request_body.get("body", "{}"))
                else:
                    body = request_body.get("body", {})
                # If parameters are empty but body has data, use body as parameters
                if not parameters and body:
                    parameters = body
            except json.JSONDecodeError:
                logger.warning("Could not parse request body as JSON")
        
        # Get the API operation name from the path
        operation = api_path.split("/")[-1] if api_path else ""
        if not operation and "api" in request_body:
            operation = request_body.get("api", "")
        
        # Special case handling for webhook validation
        if "rawPath" in event and event.get("rawPath", "") == "/validate":
            return {
                "type": "validation",
                "token": event.get("headers", {}).get("x-amzn-bedrock-validation-token", "")
            }
        
        return {
            "action_group": action_group,
            "operation": operation,
            "parameters": parameters,
            "body": body,
            "type": "invocation"
        }
    except Exception as e:
        logger.error(f"Error parsing Bedrock request: {e}")
        return {
            "action_group": "",
            "operation": "",
            "parameters": {},
            "body": {},
            "type": "error",
            "error": str(e)
        }

def format_bedrock_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the response for AWS Bedrock agent
    
    Args:
        response_data: The data to return to Bedrock
        
    Returns:
        Dict containing the formatted response
    """
    if not response_data:
        response_data = {"error": "No response data"}
    
    # Format for Bedrock agent
    bedrock_response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "NFTPaymentActions",
            "apiPath": "/",
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": json.dumps(response_data)
            }
        }
    }
    
    logger.info(f"Sending response to Bedrock: {json.dumps(bedrock_response)}")
    return bedrock_response

def validate_webhook(token: str) -> Dict[str, Any]:
    """
    Handle webhook validation request from Bedrock agent
    
    Args:
        token: The validation token from Bedrock
        
    Returns:
        Dict containing the validation response
    """
    return {
        "messageVersion": "1.0",
        "response": {
            "httpMethod": "GET",
            "httpStatusCode": 200,
            "headers": {
                "Content-Type": "text/plain"
            },
            "body": token
        }
    }

def handle_bedrock_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for Bedrock agent requests
    
    Args:
        event: The Lambda event from Bedrock agent
        
    Returns:
        Dict containing the response for Bedrock
    """
    parsed_request = parse_bedrock_request(event)
    
    # Handle webhook validation
    if parsed_request.get("type") == "validation":
        return validate_webhook(parsed_request.get("token", ""))
    
    action_group = parsed_request.get("action_group")
    operation = parsed_request.get("operation")
    parameters = parsed_request.get("parameters")
    
    # Log request details
    logger.info(f"Processing request: {action_group}.{operation}")
    logger.info(f"Parameters: {parameters}")
    
    try:
        # Look up the handler function
        if action_group in ACTION_GROUP_MAP and operation in ACTION_GROUP_MAP[action_group]:
            handler_func = ACTION_GROUP_MAP[action_group][operation]
            
            # Call the handler
            result = handler_func(parameters)
            logger.info(f"Handler result: {result}")
            
            # Format and return the response
            return format_bedrock_response(result)
        else:
            logger.warning(f"No handler found for {action_group}.{operation}")
            return format_bedrock_response({
                "error": f"Operation {action_group}.{operation} not supported"
            })
    except Exception as e:
        logger.error(f"Error handling Bedrock request: {e}")
        return format_bedrock_response({
            "error": str(e)
        })

def bedrock_lambda_handler(event, context):
    """
    Lambda handler for Bedrock agent action requests
    
    Args:
        event: The Lambda event from Bedrock agent
        context: The Lambda context
        
    Returns:
        Dict containing the response for Bedrock
    """
    logger.info("Bedrock agent request received")
    
    # Handle the request
    return handle_bedrock_request(event)

def lambda_handler(event, context):
    """
    Lambda handler for REST API requests via API Gateway
    
    Args:
        event: The Lambda event from API Gateway
        context: The Lambda context
        
    Returns:
        Dict containing the response for API Gateway
    """
    from bedrock_agent_connector import process_agent_request
    return process_agent_request(event)

def wallet_login_with_session(params):
    """
    Handle wallet login with session persistence
    
    Args:
        params: Parameters from Bedrock agent
        
    Returns:
        dict: Login result with session info
    """
    wallet_address = params.get("wallet_address")
    session_id = params.get("session_id")
    user_id = params.get("user_id")
    
    # If we have a session ID but no wallet address, try to retrieve it
    if session_id and not wallet_address:
        stored_address = get_wallet_address(session_id, user_id)
        if stored_address:
            wallet_address = stored_address
            logger.info(f"Retrieved wallet address {wallet_address} from session {session_id}")
            
    # Check if this is a connect request or a query about connection status
    is_connect_request = params.get("connect", "false").lower() == "true"
    
    # If we still don't have a wallet address
    if not wallet_address:
        if is_connect_request:
            # If this is an explicit connect request, we need the address
            return {
                "success": False,
                "error": "Wallet address is required to connect",
                "needs_wallet": True
            }
        else:
            # If just checking status, return not connected
            return {
                "success": True,
                "connected": False,
                "message": "No wallet is currently connected."
            }
    
    # Call the actual wallet login function
    result = wallet_login(wallet_address, params.get("wallet_type", "metamask"))
    
    # If login successful, store wallet address in session
    if result.get("success") and session_id:
        store_wallet_address(session_id, wallet_address, user_id)
        logger.info(f"Stored wallet address {wallet_address} in session {session_id}")
        result["connected"] = True
        result["wallet_address"] = wallet_address
        
    return result

def get_wallet_info_with_session(params):
    """
    Get wallet info with session persistence
    
    Args:
        params: Parameters from Bedrock agent
        
    Returns:
        dict: Wallet information
    """
    wallet_address = params.get("wallet_address")
    session_id = params.get("session_id")
    user_id = params.get("user_id")
    is_required = params.get("is_required", "false").lower() == "true"
    
    # If we have a session ID but no wallet address, try to retrieve it
    if session_id and not wallet_address:
        stored_address = get_wallet_address(session_id, user_id)
        if stored_address:
            wallet_address = stored_address
            logger.info(f"Retrieved wallet address {wallet_address} from session {session_id}")
            
    # If we still don't have a wallet address and it's required for this operation
    if not wallet_address:
        if is_required:
            return {
                "success": False,
                "error": "Wallet address is required for this operation",
                "needs_wallet": True
            }
        else:
            # For non-payment operations, return a response indicating no wallet is connected
            # but don't treat it as an error
            return {
                "success": True,
                "message": "No wallet is currently connected. You can connect a wallet to view personalized information.",
                "wallet_connected": False
            }
    
    # Call the actual get wallet info function
    result = get_wallet_info(wallet_address)
    if result.get("success"):
        result["wallet_connected"] = True
    return result

def get_wallet_nfts_with_session(params):
    """
    Get wallet NFTs with session persistence
    
    Args:
        params: Parameters from Bedrock agent
        
    Returns:
        dict: NFTs owned by the wallet
    """
    wallet_address = params.get("wallet_address")
    session_id = params.get("session_id")
    user_id = params.get("user_id")
    is_required = params.get("is_required", "false").lower() == "true"
    
    # If we have a session ID but no wallet address, try to retrieve it
    if session_id and not wallet_address:
        stored_address = get_wallet_address(session_id, user_id)
        if stored_address:
            wallet_address = stored_address
            logger.info(f"Retrieved wallet address {wallet_address} from session {session_id}")
            
    # If we still don't have a wallet address
    if not wallet_address:
        if is_required:
            # For operations that explicitly require a wallet
            return {
                "success": False,
                "error": "Wallet address is required to view NFTs",
                "needs_wallet": True
            }
        else:
            # For general queries that don't necessarily need wallet connection
            return {
                "success": True,
                "message": "No wallet is currently connected. Please connect a wallet to view your NFTs.",
                "wallet_connected": False,
                "nfts": []
            }
    
    # Call the actual get wallet NFTs function
    result = get_wallet_nfts(wallet_address)
    if result.get("success"):
        result["wallet_connected"] = True
    return result

def process_payment_with_session(params):
    """
    Process payment with session persistence
    
    Args:
        params: Parameters from Bedrock agent
        
    Returns:
        dict: Payment processing result
    """
    wallet_address = params.get("wallet_address")
    session_id = params.get("session_id")
    user_id = params.get("user_id")
    
    # If we have a session ID but no wallet address, try to retrieve it
    if session_id and not wallet_address:
        stored_address = get_wallet_address(session_id, user_id)
        if stored_address:
            wallet_address = stored_address
            logger.info(f"Retrieved wallet address {wallet_address} from session {session_id}")
            
    # If we still don't have a wallet address, return error
    # Payments always require wallet address
    if not wallet_address:
        return {
            "success": False,
            "error": "Wallet address is required for payment processing",
            "needs_wallet": True,
            "payment_required": True
        }
        
    # Update params with the wallet address
    params["wallet_address"] = wallet_address
    
    # Call the payment handler
    result = handle_payment_request({
        "body": {
            "amount": params.get("amount"),
            "currency": params.get("currency", "ETH"),
            "paymentReason": params.get("payment_reason"),
            "x402": {
                "payment_type": "x402",
                "wallet_address": wallet_address,
                "contract_address": params.get("contract_address", "0x123abc")
            }
        }
    })
    
    # If payment is successful, ensure we store the wallet address for future use
    if result.get("success") and session_id:
        store_wallet_address(session_id, wallet_address, user_id)
        
    return result
