# Bedrock Agent Configuration
# This file contains the configuration for the AWS Bedrock Agent integration

# AWS Bedrock agent settings
BEDROCK_AGENT_ID="LRKVLMX55I"  # AgoraAI_BASEMain
BEDROCK_REGION="ap-south-1"
BEDROCK_AGENT_ALIAS="default-runtime-alias"

# These settings can be overridden via environment variables:
# BEDROCK_AGENT_ID - The ID of the Bedrock agent to use
# BEDROCK_REGION - The AWS region where the Bedrock agent is deployed
# BEDROCK_AGENT_ALIAS - The alias name to use for the Bedrock agent

# Update Lambda environment variables with these settings using the CLI:
# aws lambda update-function-configuration \
#   --function-name YOUR_LAMBDA_FUNCTION_NAME \
#   --environment "Variables={BEDROCK_AGENT_ID=LRKVLMX55I,BEDROCK_REGION=ap-south-1}"

# For local development, you can set these environment variables in your shell:
# export BEDROCK_AGENT_ID=LRKVLMX55I
# export BEDROCK_REGION=ap-south-1

# Make sure to add these IAM permissions to your Lambda execution role:
# - bedrock:InvokeAgent
# - bedrock-agent:InvokeAgent
# - bedrock:ListFoundationModels
# - bedrock-agent:CreateAgentAlias
# - bedrock-agent:ListAgentAliases
