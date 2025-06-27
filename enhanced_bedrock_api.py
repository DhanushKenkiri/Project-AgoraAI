"""
Enhanced Bedrock REST API Handler for Rich Media Support

This module provides a REST API for the Bedrock Agent with support for
rich media responses including images and formatted text.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
import base64
from datetime import datetime

# Import Bedrock connector
from bedrock_agent_connector import get_connector, DEFAULT_REGION, DEFAULT_AGENT_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bedrock_rest_api")

class EnhancedBedrockAPI:
    """
    Enhanced Bedrock API handler with support for rich media
    """
    def __init__(self):
        """Initialize the API handler"""
        self.region = os.environ.get('BEDROCK_REGION', DEFAULT_REGION)
        self.agent_id = os.environ.get('BEDROCK_AGENT_ID', DEFAULT_AGENT_ID)
        
    def handle_request(self, event):
        """
        Handle REST API request for Bedrock agent
        
        Args:
            event: API Gateway event
            
        Returns:
            API Gateway response
        """
        try:
            # Extract HTTP method
            method = event.get('httpMethod', 'POST')
            
            # Handle preflight OPTIONS request
            if method == 'OPTIONS':
                return self._handle_cors_preflight()
                
            # Extract request body
            body = event.get('body', '{}')
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    return self._create_response(400, {
                        "success": False,
                        "error": "Invalid JSON in request body"
                    })
            
            # Handle different API endpoints
            path = event.get('path', '/')
            resource = event.get('resource', '/')
            
            # Extract common parameters
            session_id = body.get('sessionId', str(uuid.uuid4()))
            user_id = body.get('userId')
            message = body.get('message', '')
            
            if path.endswith('/chat') or resource == '/chat':
                return self._handle_chat_request(body, session_id, user_id)
            elif path.endswith('/upload') or resource == '/upload':
                return self._handle_image_upload(body, session_id, user_id)
            else:
                # Default to chat endpoint
                return self._handle_chat_request(body, session_id, user_id)
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return self._create_response(500, {
                "success": False,
                "error": str(e)
            })
    
    def _handle_chat_request(self, body, session_id, user_id=None):
        """
        Handle chat request to Bedrock agent
        
        Args:
            body: Request body
            session_id: Session ID
            user_id: Optional user ID
            
        Returns:
            API response with agent message
        """
        # Extract message
        message = body.get('message', '')
        if not message:
            return self._create_response(400, {
                "success": False,
                "error": "Message is required"
            })
            
        # Get message history if provided
        message_history = body.get('messageHistory', [])
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Get connector and invoke agent
        connector = get_connector(self.region, self.agent_id)
        result = connector.invoke_agent(message, session_id, request_id)
        
        if result.get("success"):
            # Get agent response
            agent_message = result.get("data", {}).get("message", "")
            
            # Extract any images/media from the message if present
            media = self._extract_media_from_message(agent_message)
            
            # Create enhanced response
            response_data = {
                "success": True,
                "message": self._process_agent_message(agent_message),
                "sessionId": session_id,
                "timestamp": datetime.now().isoformat(),
                "media": media,
                "metadata": result.get("metadata", {})
            }
            
            return self._create_response(200, response_data)
        else:
            return self._create_response(500, {
                "success": False,
                "error": result.get("error", "Unknown error")
            })
    
    def _handle_image_upload(self, body, session_id, user_id=None):
        """
        Handle image upload for sending to Bedrock agent
        
        Args:
            body: Request body with base64 image
            session_id: Session ID
            user_id: Optional user ID
            
        Returns:
            API response confirming upload
        """
        # Extract image data
        image_data = body.get('imageData')
        if not image_data:
            return self._create_response(400, {
                "success": False,
                "error": "Image data is required"
            })
            
        # Store the image temporarily (in a real implementation, this would save to S3)
        # For now we'll just acknowledge the upload
        
        return self._create_response(200, {
            "success": True,
            "message": "Image uploaded successfully",
            "sessionId": session_id,
            "imageId": str(uuid.uuid4())  # In a real implementation, this would be the S3 key
        })
    
    def _extract_media_from_message(self, message):
        """
        Extract media elements from agent message
        
        Args:
            message: Agent message text
            
        Returns:
            List of media objects
        """
        media = []
        
        # Simple parser for markdown image syntax
        # In a real implementation, this would be more robust
        import re
        
        # Match markdown image syntax: ![alt](url)
        image_matches = re.findall(r'!\[(.*?)\]\((.*?)\)', message)
        
        for alt, url in image_matches:
            media.append({
                "type": "image",
                "alt": alt,
                "url": url
            })
            
        return media
    
    def _process_agent_message(self, message):
        """
        Process agent message to enhance it for display
        
        Args:
            message: Raw agent message
            
        Returns:
            Processed message
        """
        # In a real implementation, this would do more processing
        # For now, just return the original message
        return message
    
    def _handle_cors_preflight(self):
        """Handle CORS preflight request"""
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": ""
        }
    
    def _create_response(self, status_code, body):
        """Create API response"""
        return {
            "statusCode": status_code,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Content-Type": "application/json"
            },
            "body": json.dumps(body)
        }

# Create singleton instance
api_handler = EnhancedBedrockAPI()

def handler(event, context):
    """Lambda handler for enhanced Bedrock REST API"""
    return api_handler.handle_request(event)
