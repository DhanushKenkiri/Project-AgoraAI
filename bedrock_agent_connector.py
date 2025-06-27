"""
Bedrock Agent Connector for NFT Payment System

This module provides direct integration with AWS Bedrock Agent runtime.
It connects to the specified Bedrock agent and sends/receives messages.
"""

import json
import boto3
import uuid
import time
from botocore.exceptions import ClientError
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bedrock_agent_connector")

# Default agent ID and region from configuration file or environment
DEFAULT_AGENT_ID = os.environ.get('BEDROCK_AGENT_ID', "LRKVLMX55I")  # AgoraAI_BASEMain
DEFAULT_REGION = os.environ.get('BEDROCK_REGION', "ap-south-1")

class BedrockAgentConnector:
    """
    Handles direct connection to AWS Bedrock Agent
    """
    def __init__(self, region_name=DEFAULT_REGION, agent_id=DEFAULT_AGENT_ID, alias_name="default-runtime-alias"):
        """
        Initialize the Bedrock Agent connector
        
        Args:
            region_name: AWS region where the Bedrock agent is deployed
            agent_id: The ID of the Bedrock agent
            alias_name: The alias name to use or create
        """
        self.region_name = region_name
        self.agent_id = agent_id
        self.alias_name = alias_name
        
        # Load agent ID from environment if not provided
        if not self.agent_id:
            self.agent_id = os.environ.get('BEDROCK_AGENT_ID')
            if not self.agent_id:
                logger.warning("No Bedrock Agent ID provided or found in environment")
        
        # Initialize AWS clients
        try:
            self.agent_mgmt = boto3.client('bedrock-agent', region_name=self.region_name)
            self.agent_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region_name)
        except Exception as e:
            logger.warning(f"Error initializing Bedrock clients (normal in test environment): {str(e)}")
            self.agent_mgmt = None
            self.agent_runtime = None
        
        # Cache for alias ID
        self.alias_id = None
    
    def get_agent_alias(self):
        """
        Get or create a Bedrock agent alias
        
        Returns:
            str: The agent alias ID
        """
        # In test mode, return a dummy alias ID
        if self.agent_runtime is None or self.agent_mgmt is None:
            return "test-alias-id"
            
        if self.alias_id:
            return self.alias_id
            
        try:
            # Try to find an existing prepared alias
            aliases = self.agent_mgmt.list_agent_aliases(agentId=self.agent_id).get("agentAliasSummaries", [])
            for alias in aliases:
                if alias["agentAliasStatus"] == "PREPARED":
                    self.alias_id = alias["agentAliasId"]
                    logger.info(f"Found existing alias: {self.alias_id}")
                    return self.alias_id
            
            # If no suitable alias found, create a new one
            logger.info(f"Creating new agent alias '{self.alias_name}'")
            new_alias = self.agent_mgmt.create_agent_alias(
                agentId=self.agent_id,
                agentAliasName=self.alias_name,
                routingConfiguration=[{"agentVersion": "1"}]
            )
            self.alias_id = new_alias["agentAlias"]["agentAliasId"]
            
            # Wait for alias to propagate
            time.sleep(2)
            return self.alias_id
            
        except Exception as e:
            logger.error(f"Error getting agent alias: {str(e)}")
            raise
    
    def invoke_agent(self, user_input, session_id=None, request_id=None, agent_name=None):
        """
        Invoke the Bedrock agent with user input
        
        Args:
            user_input: The user's message
            session_id: Optional session ID for conversation tracking
            request_id: Optional request ID for tracking
            agent_name: Optional agent name for response metadata
            
        Returns:
            dict: The agent's response
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if not request_id:
            request_id = str(uuid.uuid4())
            
        if not agent_name:
            agent_name = "AgoraAI_BASEMain"
            
        if not self.agent_id:
            return {
                "success": False,
                "error": "No Bedrock Agent ID configured"
            }
        
        # For testing purposes, if agent_runtime is None, return a mock response
        if self.agent_runtime is None:
            # Mock response for testing
            logger.info("Using mock response for testing")
            return {
                "success": True,
                "data": {
                    "message": f"This is a mock response to: '{user_input}'. In a real environment, this would come from AWS Bedrock Agent.",
                    "agentName": agent_name,
                    "sessionId": session_id
                },
                "metadata": {
                    "agentId": self.agent_id,
                    "aliasId": "test-alias-id",
                    "timestamp": str(uuid.uuid4()),
                    "requestId": request_id
                }
            }
            
        try:
            # Get alias ID
            alias_id = self.get_agent_alias()
            
            # Call Bedrock Agent
            response = self.agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=user_input
            )
            
            # Parse response chunks
            output_text = ""
            for chunk_event in response.get("completion", []):
                if "chunk" in chunk_event and "bytes" in chunk_event["chunk"]:
                    output_text += chunk_event["chunk"]["bytes"].decode("utf-8")
              
            return {
                "success": True,
                "data": {
                    "message": output_text.strip(),
                    "agentName": agent_name,
                    "sessionId": session_id
                },
                "metadata": {
                    "agentId": self.agent_id,
                    "aliasId": alias_id,
                    "timestamp": str(uuid.uuid4()),
                    "requestId": request_id
                }
            }
            
        except ClientError as e:
            logger.error(f"Bedrock agent client error: {str(e)}")
            return {
                "success": False,
                "error": {
                    "type": e.response["Error"]["Code"],
                    "message": e.response["Error"]["Message"]
                }
            }
        except Exception as e:
            logger.error(f"Bedrock agent error: {str(e)}")
            return {
                "success": False,
                "error": {
                    "type": "InternalError",
                    "message": str(e)
                }
            }
            
# Singleton instance for reuse
_connector_instance = None

def get_connector(region_name=None, agent_id=None):
    """
    Get or create a BedrockAgentConnector instance
    
    Args:
        region_name: AWS region for Bedrock Agent
        agent_id: Bedrock Agent ID
        
    Returns:
        BedrockAgentConnector: An instance of the connector
    """
    global _connector_instance
    
    if _connector_instance is None:
        # Get region from environment if not provided
        if not region_name:
            import os
            region_name = os.environ.get('BEDROCK_REGION', 'ap-south-1')
            
        _connector_instance = BedrockAgentConnector(
            region_name=region_name,
            agent_id=agent_id
        )
    
    return _connector_instance

def process_agent_request(event):
    """
    Process a request for the Bedrock agent
    
    Args:
        event: Lambda event containing user message
        
    Returns:
        dict: Response from Bedrock agent
    """
    try:
        # Parse user input from event
        body = event.get("body", {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization"
                    },
                    "body": json.dumps({"success": False, "error": {"message": "Invalid JSON"}})
                }
        
        # Extract the user input message
        user_input = None
        session_id = None
        
        if "messages" in body and isinstance(body["messages"], list):
            for message in reversed(body["messages"]):
                if message.get("role", "") == "user" and message.get("content"):
                    user_input = message["content"]
                    break
        
        if not user_input:
            user_input = body.get("message") or body.get("input") or body.get("query") or "Hello!"
        
        # Check for session ID - Important for persistent storage
        session_id = body.get("sessionId") or event.get("sessionId") or str(uuid.uuid4())
        logger.info(f"Using session ID: {session_id}")
        
        # Get agent ID from request or environment
        agent_id = body.get("agentId") or event.get("agentId") or DEFAULT_AGENT_ID
        
        # Get region from request or default
        region_name = body.get("region") or event.get("region") or DEFAULT_REGION
        
        # Get request ID for tracking
        request_id = body.get("requestId") or event.get("requestId") or str(uuid.uuid4())
        
        # Get agent name if provided
        agent_name = body.get("agentName") or event.get("agentName") or "AgoraAI_BASEMain"
        
        # Get connector and invoke agent
        connector = get_connector(region_name, agent_id)
        result = connector.invoke_agent(user_input, session_id, request_id, agent_name)
          
        if result["success"]:
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "success": True,
                    "data": result["data"],
                    "metadata": result["metadata"]
                })
            }
        else:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                },
                "body": json.dumps({
                    "success": False,
                    "error": result.get("error", {"message": "Unknown error"})
                })
            }
              
    except ClientError as e:
        logger.error(f"Bedrock agent client error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({
                "success": False,
                "error": {
                    "type": e.response["Error"]["Code"],
                    "message": e.response["Error"]["Message"]
                }
            })
        }
    except Exception as e:
        logger.error(f"Error processing agent request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({
                "success": False,
                "error": {
                    "type": "InternalError",
                    "message": str(e)
                }
            })
        }

def lambda_handler(event, context):
    """
    Lambda handler for direct Bedrock agent requests
    This handler processes requests directly to the Bedrock agent
    and is compatible with the format from API Gateway
    """
    return process_agent_request(event)
