import json
import os
import boto3
from dynamic_pricing_agent import DynamicPricingAgent
from agent_payment_integration import PaymentAgent

# Initialize the dynamic pricing agent for NFT-aware pricing
pricing_agent = DynamicPricingAgent()
# Keep the standard payment agent as fallback
payment_agent = PaymentAgent()

def lambda_handler(event, context):
    """
    AWS Lambda handler for agent payment integration with dynamic NFT pricing
    """
    try:
        print(f"Received agent event: {json.dumps({k: v for k, v in event.items() if k not in ['wallet_address']})}")
          # Extract action and payload
        action = event.get('action')
        payload = event.get('payload', {})
        
        if action == 'get_payment_options':
            # Agent is requesting payment options for a resource
            resource_path = payload.get('resource_path')
            user_id = payload.get('user_id')
            collection_address = payload.get('collection_address')
            token_id = payload.get('token_id')
            data_type = payload.get('data_type')
            
            # Use dynamic pricing agent if NFT data is provided
            if collection_address or token_id:
                return pricing_agent.get_payment_options(
                    resource_path=resource_path,
                    collection_address=collection_address,
                    token_id=token_id,
                    data_type=data_type
                )            else:
                # Fall back to standard pricing for non-NFT resources
                return payment_agent.get_payment_options(resource_path, user_id)
                
        elif action == 'process_payment_action':
            # User clicked a payment button in the agent
            button_action = payload.get('button_action')
            button_payload = payload.get('button_payload', {})
            
            # Check if payload contains NFT-specific data
            if 'collection_address' in button_payload or 'token_id' in button_payload:
                return pricing_agent.process_payment_action(button_action, button_payload)
            else:
                return payment_agent.process_payment_action(button_action, button_payload)
              elif action == 'initiate_payment':
            # Direct payment initiation from agent
            wallet_address = payload.get('wallet_address')
            amount = payload.get('amount')
            currency = payload.get('currency', 'ETH')
            resource = payload.get('resource')
            transaction_id = payload.get('transaction_id')
            collection_address = payload.get('collection_address')
            token_id = payload.get('token_id')
            
            # Use dynamic pricing agent if NFT data is available
            if collection_address or token_id:
                return pricing_agent.initiate_payment(
                    wallet_address=wallet_address,
                    amount=amount,
                    currency=currency,
                    resource=resource,
                    collection_address=collection_address,
                    token_id=token_id,
                    transaction_id=transaction_id
                )
            else:
                return payment_agent.initiate_payment(
                    wallet_address=wallet_address,
                    amount=amount,
                    currency=currency,
                    resource=resource,
                    transaction_id=transaction_id
                )
              elif action == 'check_payment_status':
            # Check status of a payment
            transaction_id = payload.get('transaction_id')
            payment_id = payload.get('payment_id')
            
            # Use payment ID if provided, otherwise use transaction ID
            identifier = payment_id or transaction_id
            
            if not identifier:
                return {
                    'success': False,
                    'error': 'Payment identifier is required'
                }
            
            # Call payment processor to check status
            from utils.x402_processor import X402PaymentProcessor
            processor = X402PaymentProcessor()
            return processor.check_payment_status(identifier)
            
        elif action == 'get_nft_price':
            # Get dynamic pricing for an NFT collection or token
            collection_address = payload.get('collection_address')
            
            if not collection_address:
                return {
                    'success': False,
                    'error': 'Collection address is required for NFT pricing'
                }
                
            # Get floor price information
            floor_price_data = pricing_agent.price_oracle.get_collection_floor_price(
                collection_address=collection_address,
                blockchain=payload.get('blockchain', 'ethereum')
            )
            
            return {
                'success': True,
                'floor_price_data': floor_price_data
            }
            
        else:
            return {
                'success': False,
                'error': f"Unknown action: {action}"
            }
    
    except Exception as e:
        print(f"Error processing agent request: {str(e)}")
        return {
            'success': False,
            'error': f"Error processing agent request: {str(e)}"
        }
