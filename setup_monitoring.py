#!/usr/bin/env python
"""
CDP Wallet and X402 Payment Integration - Monitoring Setup Script

This script sets up CloudWatch monitoring and alerting for the CDP Wallet and X402 Payment integration.
"""
import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime

def check_aws_cli():
    """Check if AWS CLI is installed and configured"""
    try:
        result = subprocess.run(['aws', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode != 0:
            print("Error: AWS CLI is not installed or not in PATH")
            print("Please install AWS CLI: https://aws.amazon.com/cli/")
            sys.exit(1)
            
        # Check if AWS is configured
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode != 0:
            print("Error: AWS CLI is not configured properly")
            print("Please run 'aws configure' to set up your AWS credentials")
            sys.exit(1)
            
        account_info = json.loads(result.stdout)
        print(f"AWS CLI is configured for account: {account_info['Account']}")
        return account_info
        
    except FileNotFoundError:
        print("Error: AWS CLI is not installed")
        print("Please install AWS CLI: https://aws.amazon.com/cli/")
        sys.exit(1)

def create_sns_topic(topic_name, region="us-east-1"):
    """Create an SNS topic for alerts"""
    print(f"Creating SNS topic for alerts: {topic_name}")
    
    result = subprocess.run([
        'aws', 'sns', 'create-topic',
        '--name', topic_name,
        '--region', region,
        '--output', 'json'
    ], capture_output=True, text=True, check=True)
    
    topic_arn = json.loads(result.stdout)['TopicArn']
    print(f"Created SNS topic: {topic_arn}")
    return topic_arn

def subscribe_email_to_topic(topic_arn, email, region="us-east-1"):
    """Subscribe an email address to SNS topic"""
    print(f"Subscribing {email} to SNS topic")
    
    result = subprocess.run([
        'aws', 'sns', 'subscribe',
        '--topic-arn', topic_arn,
        '--protocol', 'email',
        '--notification-endpoint', email,
        '--region', region,
        '--output', 'json'
    ], capture_output=True, text=True, check=True)
    
    print(f"Subscription initiated. Please check {email} to confirm the subscription.")
    return json.loads(result.stdout)['SubscriptionArn']

def create_lambda_error_alarm(function_name, topic_arn, region="us-east-1"):
    """Create a CloudWatch alarm for Lambda errors"""
    alarm_name = f"{function_name}-Errors-Alarm"
    print(f"Creating CloudWatch alarm: {alarm_name}")
    
    result = subprocess.run([
        'aws', 'cloudwatch', 'put-metric-alarm',
        '--alarm-name', alarm_name,
        '--alarm-description', 'Alarm when Lambda errors exceed threshold',
        '--metric-name', 'Errors',
        '--namespace', 'AWS/Lambda',
        '--statistic', 'Sum',
        '--period', '300',
        '--threshold', '5',
        '--comparison-operator', 'GreaterThanThreshold',
        '--dimensions', f'Name=FunctionName,Value={function_name}',
        '--evaluation-periods', '1',
        '--alarm-actions', topic_arn,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Created Lambda error alarm: {alarm_name}")
    else:
        print(f"Error creating Lambda error alarm: {result.stderr}")

def create_lambda_duration_alarm(function_name, topic_arn, region="us-east-1"):
    """Create a CloudWatch alarm for Lambda duration"""
    alarm_name = f"{function_name}-Duration-Alarm"
    print(f"Creating CloudWatch alarm: {alarm_name}")
    
    result = subprocess.run([
        'aws', 'cloudwatch', 'put-metric-alarm',
        '--alarm-name', alarm_name,
        '--alarm-description', 'Alarm when Lambda duration exceeds threshold',
        '--metric-name', 'Duration',
        '--namespace', 'AWS/Lambda',
        '--statistic', 'Average',
        '--period', '300',
        '--threshold', '5000',  # 5000 ms (5 seconds)
        '--comparison-operator', 'GreaterThanThreshold',
        '--dimensions', f'Name=FunctionName,Value={function_name}',
        '--evaluation-periods', '3',
        '--alarm-actions', topic_arn,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Created Lambda duration alarm: {alarm_name}")
    else:
        print(f"Error creating Lambda duration alarm: {result.stderr}")

def create_api_gateway_alarm(api_name, topic_arn, region="us-east-1"):
    """Create CloudWatch alarms for API Gateway"""
    # 4XX Errors
    alarm_name_4xx = f"{api_name}-4XXError-Alarm"
    print(f"Creating CloudWatch alarm: {alarm_name_4xx}")
    
    result = subprocess.run([
        'aws', 'cloudwatch', 'put-metric-alarm',
        '--alarm-name', alarm_name_4xx,
        '--alarm-description', 'Alarm when 4XX errors exceed threshold',
        '--metric-name', '4XXError',
        '--namespace', 'AWS/ApiGateway',
        '--statistic', 'Sum',
        '--period', '300',
        '--threshold', '10',
        '--comparison-operator', 'GreaterThanThreshold',
        '--dimensions', f'Name=ApiName,Value={api_name}',
        '--evaluation-periods', '1',
        '--alarm-actions', topic_arn,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Created API Gateway 4XX error alarm: {alarm_name_4xx}")
    else:
        print(f"Error creating API Gateway 4XX error alarm: {result.stderr}")
    
    # 5XX Errors
    alarm_name_5xx = f"{api_name}-5XXError-Alarm"
    print(f"Creating CloudWatch alarm: {alarm_name_5xx}")
    
    result = subprocess.run([
        'aws', 'cloudwatch', 'put-metric-alarm',
        '--alarm-name', alarm_name_5xx,
        '--alarm-description', 'Alarm when 5XX errors exceed threshold',
        '--metric-name', '5XXError',
        '--namespace', 'AWS/ApiGateway',
        '--statistic', 'Sum',
        '--period', '300',
        '--threshold', '1',
        '--comparison-operator', 'GreaterThanThreshold',
        '--dimensions', f'Name=ApiName,Value={api_name}',
        '--evaluation-periods', '1',
        '--alarm-actions', topic_arn,
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Created API Gateway 5XX error alarm: {alarm_name_5xx}")
    else:
        print(f"Error creating API Gateway 5XX error alarm: {result.stderr}")

def create_dashboard(function_name, api_name, region="us-east-1"):
    """Create a CloudWatch dashboard for monitoring"""
    dashboard_name = "CDPWalletX402Dashboard"
    print(f"Creating CloudWatch dashboard: {dashboard_name}")
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Invocations", "FunctionName", function_name, { "stat": "Sum", "period": 300 } ],
                        [ ".", "Errors", ".", ".", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Duration", ".", ".", { "stat": "Average", "period": 300 } ],
                        [ ".", "Throttles", ".", ".", { "stat": "Sum", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Lambda Metrics"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "4XXError", "ApiName", api_name, { "stat": "Sum", "period": 300 } ],
                        [ ".", "5XXError", ".", ".", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Count", ".", ".", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Latency", ".", ".", { "stat": "Average", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "API Gateway Metrics"
                }
            }
        ]
    }
    
    result = subprocess.run([
        'aws', 'cloudwatch', 'put-dashboard',
        '--dashboard-name', dashboard_name,
        '--dashboard-body', json.dumps(dashboard_body),
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Created CloudWatch dashboard: {dashboard_name}")
        return True
    else:
        print(f"Error creating CloudWatch dashboard: {result.stderr}")
        return False

def enable_xray_tracing(function_name, region="us-east-1"):
    """Enable X-Ray tracing for Lambda function"""
    print(f"Enabling X-Ray tracing for Lambda function: {function_name}")
    
    result = subprocess.run([
        'aws', 'lambda', 'update-function-configuration',
        '--function-name', function_name,
        '--tracing-config', 'Mode=Active',
        '--region', region
    ], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print(f"Enabled X-Ray tracing for Lambda function: {function_name}")
        return True
    else:
        print(f"Error enabling X-Ray tracing: {result.stderr}")
        return False

def setup_scheduled_testing(test_function_name, api_url, topic_arn, region="us-east-1"):
    """Set up a scheduled test Lambda function that runs every 15 minutes"""
    print(f"Setting up scheduled testing with Lambda function: {test_function_name}")
    
    # Create the Lambda execution role
    role_name = f"{test_function_name}-role"
    
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        result = subprocess.run([
            'aws', 'iam', 'create-role',
            '--role-name', role_name,
            '--assume-role-policy-document', json.dumps(assume_role_policy),
            '--region', region
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0 and "EntityAlreadyExists" not in result.stderr:
            print(f"Error creating role: {result.stderr}")
            return False
        
        # Get role ARN
        result = subprocess.run([
            'aws', 'iam', 'get-role',
            '--role-name', role_name,
            '--query', 'Role.Arn',
            '--output', 'text',
            '--region', region
        ], capture_output=True, text=True, check=True)
        
        role_arn = result.stdout.strip()
        
        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
            "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
        ]
        
        for policy in policies:
            subprocess.run([
                'aws', 'iam', 'attach-role-policy',
                '--role-name', role_name,
                '--policy-arn', policy,
                '--region', region
            ], capture_output=True, text=True, check=False)
        
        # Wait for role to propagate
        print("Waiting for IAM role to propagate...")
        time.sleep(10)
        
        # Create Lambda function code
        test_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_deployed_api.py')
        if not os.path.exists(test_script_path):
            print(f"Error: Test script not found at {test_script_path}")
            return False
        
        # Create a zip file for Lambda
        import zipfile
        zip_path = "/tmp/lambda_test_function.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(test_script_path, 'lambda_function.py')
        
        # Create Lambda function
        result = subprocess.run([
            'aws', 'lambda', 'create-function',
            '--function-name', test_function_name,
            '--runtime', 'python3.9',
            '--role', role_arn,
            '--handler', 'lambda_function.lambda_handler',
            '--zip-file', f'fileb://{zip_path}',
            '--environment', f'Variables={{API_URL={api_url},SNS_TOPIC_ARN={topic_arn}}}',
            '--timeout', '60',
            '--region', region
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0 and "Function already exist" not in result.stderr:
            print(f"Error creating Lambda function: {result.stderr}")
            return False
        
        # Create EventBridge rule for scheduling
        rule_name = f"{test_function_name}-schedule"
        result = subprocess.run([
            'aws', 'events', 'put-rule',
            '--name', rule_name,
            '--schedule-expression', 'rate(15 minutes)',
            '--region', region
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            print(f"Error creating EventBridge rule: {result.stderr}")
            return False
        
        # Add Lambda permission for EventBridge
        result = subprocess.run([
            'aws', 'lambda', 'add-permission',
            '--function-name', test_function_name,
            '--statement-id', 'EventBridgeInvoke',
            '--action', 'lambda:InvokeFunction',
            '--principal', 'events.amazonaws.com',
            '--source-arn', f'arn:aws:events:{region}:{account_info["Account"]}:rule/{rule_name}',
            '--region', region
        ], capture_output=True, text=True, check=False)
        
        # Connect EventBridge rule to Lambda
        result = subprocess.run([
            'aws', 'events', 'put-targets',
            '--rule', rule_name,
            '--targets', f'Id=1,Arn=arn:aws:lambda:{region}:{account_info["Account"]}:function:{test_function_name}',
            '--region', region
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            print(f"Error adding EventBridge target: {result.stderr}")
            return False
        
        print(f"Successfully set up scheduled testing with Lambda function: {test_function_name}")
        return True
    
    except Exception as e:
        print(f"Error setting up scheduled testing: {str(e)}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Set up CloudWatch monitoring for CDP Wallet and X402 Payment integration'
    )
    
    parser.add_argument(
        '--function-name', 
        default='PaymentHandler-dev',
        help='Lambda function name to monitor'
    )
    
    parser.add_argument(
        '--api-name', 
        default='nft-payment-api-dev',
        help='API Gateway name to monitor'
    )
    
    parser.add_argument(
        '--api-url', 
        default='',
        help='API endpoint URL for testing (e.g., https://abcdef123.execute-api.us-east-1.amazonaws.com/dev)'
    )
    
    parser.add_argument(
        '--email', 
        required=True,
        help='Email address for alarm notifications'
    )
    
    parser.add_argument(
        '--scheduled-tests', 
        action='store_true',
        default=False,
        help='Set up scheduled testing of API endpoints'
    )
    
    parser.add_argument(
        '--region', 
        default='us-east-1',
        help='AWS region for resources'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    print("=== CDP Wallet and X402 Payment Integration - Monitoring Setup ===")
    
    # Parse arguments
    args = parse_arguments()
    
    # Check AWS CLI
    account_info = check_aws_cli()
    
    # Create SNS topic for alerts
    topic_arn = create_sns_topic(f"CDP-Wallet-X402-Alerts", args.region)
    
    # Subscribe email to topic
    subscribe_email_to_topic(topic_arn, args.email, args.region)
    
    # Create Lambda alarms
    create_lambda_error_alarm(args.function_name, topic_arn, args.region)
    create_lambda_duration_alarm(args.function_name, topic_arn, args.region)
    
    # Create API Gateway alarms
    create_api_gateway_alarm(args.api_name, topic_arn, args.region)
    
    # Create CloudWatch dashboard
    create_dashboard(args.function_name, args.api_name, args.region)
    
    # Enable X-Ray tracing
    enable_xray_tracing(args.function_name, args.region)
    
    # Set up scheduled testing if requested
    if args.scheduled_tests:
        if not args.api_url:
            print("Error: --api-url is required for scheduled testing")
            sys.exit(1)
        
        setup_scheduled_testing(
            f"CDPWalletX402-TestFunction",
            args.api_url,
            topic_arn,
            args.region
        )
    
    print("\n=== Monitoring Setup Complete ===")
    print(f"CloudWatch alarms will be sent to: {args.email}")
    print(f"View the dashboard at: https://{args.region}.console.aws.amazon.com/cloudwatch/home?region={args.region}#dashboards:name={dashboard_name}")
    
if __name__ == "__main__":
    main()
