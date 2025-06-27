# AWS CLI script to configure Lambda function
# You need the AWS CLI installed and configured for this to work

# Replace this with your actual Lambda function name
FUNCTION_NAME="YourLambdaFunctionName"

# Update the function configuration
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --timeout 60 \
  --memory-size 512
