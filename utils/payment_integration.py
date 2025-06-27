import json
import os
import boto3
import uuid
import time
from urllib.parse import urlencode
from botocore.exceptions import ClientError

class NFTPaymentIntegration:
    """
    Integration class for handling NFT payments via CDP wallet and X402 gateway
    This class is meant to be used within your main Lambda handler to facilitate payments
    """
    
    def __init__(self, payment_lambda_arn=None, api_endpoint=None, region_name='us-east-1'):
        """Initialize the payment integration"""
        self.payment_lambda_arn = payment_lambda_arn or os.environ.get('PAYMENT_LAMBDA_ARN')
        self.api_endpoint = api_endpoint or os.environ.get('PAYMENT_API_ENDPOINT')
        self.region_name = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        
    def create_wallet_connection_url(self, callback_url=None, state=None):
        """
        Create a URL for connecting a CDP wallet
        
        Args:
            callback_url: URL to return to after wallet connection
            state: Optional state parameter for security
        
        Returns:
            str: A URL that will prompt the user to connect their CDP wallet
        """
        if not state:
            state = str(uuid.uuid4())
            
        # Create query parameters
        params = {
            'callback': callback_url,
            'state': state,
            'timestamp': int(time.time())
        }
        
        # Generate the CDP wallet connection URL
        connect_url = f"cdp://connect?{urlencode(params)}"
        
        return {
            'connection_url': connect_url,
            'state': state
        }
    
    def create_payment_intent(self, wallet_address, amount, nft_contract, nft_token_id=None, currency='ETH'):
        """
        Create a payment intent for purchasing an NFT
        
        Args:
            wallet_address: The user's crypto wallet address
            amount: Amount to charge
            nft_contract: The NFT contract address
            nft_token_id: Optional NFT token ID
            currency: The currency to charge in (default: ETH)
            
        Returns:
            dict: Payment intent information including URLs for completing payment
        """
        try:
            # Input validation
            if not wallet_address or not amount or not nft_contract:
                return {
                    'success': False,
                    'error': 'Missing required parameters: wallet_address, amount, nft_contract'
                }
            
            # Prepare the payment request payload
            payment_payload = {
                'action': 'initiate_payment',
                'wallet_address': wallet_address,
                'amount': amount,
                'currency': currency,
                'nft_contract': nft_contract,
                'nft_token_id': nft_token_id,
                'timestamp': int(time.time())
            }
            
            # Invoke the payment Lambda function
            response = self.lambda_client.invoke(
                FunctionName=self.payment_lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payment_payload)
            )
            
            # Parse the response
            response_payload = json.loads(response['Payload'].read().decode())
            
            if not response_payload.get('success'):
                return {
                    'success': False,
                    'error': response_payload.get('error', 'Unknown error creating payment intent')
                }
                
            return response_payload
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error creating payment intent: {str(e)}"
            }
    
    def check_payment_status(self, payment_id):
        """
        Check the status of a payment
        
        Args:
            payment_id: The ID of the payment to check
            
        Returns:
            dict: Payment status information
        """
        try:
            if not payment_id:
                return {
                    'success': False,
                    'error': 'Payment ID is required'
                }
                
            # Prepare the status check payload
            status_payload = {
                'action': 'check_status',
                'payment_id': payment_id,
                'timestamp': int(time.time())
            }
            
            # Invoke the payment Lambda function
            response = self.lambda_client.invoke(
                FunctionName=self.payment_lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(status_payload)
            )
            
            # Parse the response
            response_payload = json.loads(response['Payload'].read().decode())
            
            return response_payload
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking payment status: {str(e)}"
            }
    
    def format_wallet_response(self, message, connect_details=None, payment_details=None):
        """
        Format a response for the Bedrock agent with wallet connection instructions
        
        Args:
            message: The message to show the user
            connect_details: Optional wallet connection details
            payment_details: Optional payment details
            
        Returns:
            dict: Formatted response for the Bedrock agent
        """
        response = {
            'message': message
        }
        
        if connect_details:
            response['wallet_connection'] = connect_details
            
        if payment_details:
            response['payment'] = payment_details
        
        return response
        
    def handle_payment_intent(self, event, context):
        """
        Handler for payment intents from Bedrock agent
        This is intended to be called from your main Lambda function when 
        a payment intent is detected in the user's request
        
        Args:
            event: The Lambda event containing payment information
            context: The Lambda context
            
        Returns:
            dict: Payment information and next steps
        """
        try:
            # Extract payment information from the event
            wallet_address = event.get('walletAddress')
            amount = event.get('amount')
            nft_contract = event.get('contractAddress')
            nft_token_id = event.get('tokenId')
            currency = event.get('currency', 'ETH')
            
            # Check if we have wallet address, if not, we need to prompt for connection
            if not wallet_address:
                connection_details = self.create_wallet_connection_url(
                    callback_url=event.get('callbackUrl')
                )
                
                return self.format_wallet_response(
                    message="Please connect your CDP wallet to continue with the purchase.",
                    connect_details=connection_details
                )
            
            # Create a payment intent
            payment_result = self.create_payment_intent(
                wallet_address=wallet_address,
                amount=amount,
                nft_contract=nft_contract,
                nft_token_id=nft_token_id,
                currency=currency
            )
            
            if not payment_result.get('success'):
                return self.format_wallet_response(
                    message=f"Unable to create payment: {payment_result.get('error')}",
                )
                
            # Format the response with payment details
            return self.format_wallet_response(
                message="Your payment has been initiated. Please complete the transaction in your CDP wallet.",
                payment_details={
                    'payment_id': payment_result.get('payment_id'),
                    'payment_url': payment_result.get('payment_url'),
                    'status': payment_result.get('status'),
                    'amount': amount,
                    'currency': currency,
                    'nft_contract': nft_contract,
                    'nft_token_id': nft_token_id
                }
            )
            
        except Exception as e:
            return self.format_wallet_response(
                message=f"Error processing payment request: {str(e)}"
            )
