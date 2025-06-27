# Monitoring and Alerting Guide for CDP Wallet and X402 Payment Integration

This guide covers best practices for monitoring your CDP Wallet and X402 Payment integration after deployment to AWS Lambda.

## CloudWatch Metrics to Monitor

### Lambda Function Metrics

1. **Invocations**
   - Monitor the number of API requests
   - Set up alarms for unexpected spikes or drops

2. **Errors**
   - Track error rate and set thresholds
   - Alarm if error rate exceeds 5% of total invocations

3. **Duration**
   - Monitor execution time
   - Set alarms if duration approaches timeout limit (e.g., >80% of configured timeout)

4. **Throttles**
   - Alert on throttled invocations
   - Consider increasing concurrency limits if needed

5. **IteratorAge (for event sources)**
   - If using event sources, monitor processing lag

### DynamoDB Metrics

1. **Read/Write Capacity Units**
   - Monitor consumed capacity
   - Set alarms if approaching provisioned limits

2. **Throttled Requests**
   - Alert on throttling events
   - Consider auto-scaling if needed

3. **System Errors**
   - Track internal DynamoDB errors

### API Gateway Metrics

1. **4xx/5xx Errors**
   - Set alarms for client and server errors
   - Investigate if error rate exceeds thresholds

2. **Latency**
   - Monitor API response times
   - Set percentile-based alarms (e.g., p95 latency > 1000ms)

3. **Integration Latency**
   - Track backend processing time

4. **Count**
   - Monitor overall API usage patterns

## Setting Up CloudWatch Alarms

### Lambda Error Alarm

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "PaymentHandler-Errors-Alarm" \
    --alarm-description "Alarm when errors exceed threshold" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=PaymentHandler-dev \
    --evaluation-periods 1 \
    --alarm-actions <sns-topic-arn>
```

### API Gateway Latency Alarm

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "API-Gateway-Latency-Alarm" \
    --alarm-description "Alarm when API latency exceeds threshold" \
    --metric-name Latency \
    --namespace AWS/ApiGateway \
    --extended-statistic p95 \
    --period 300 \
    --threshold 1000 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ApiName,Value=nft-payment-api-dev \
    --evaluation-periods 3 \
    --alarm-actions <sns-topic-arn>
```

## Custom CloudWatch Metrics

Implement these custom metrics in your Lambda code:

1. **Wallet Connection Success Rate**
   ```python
   import boto3
   
   cloudwatch = boto3.client('cloudwatch')
   
   def track_wallet_connection(success):
       cloudwatch.put_metric_data(
           Namespace='CDPWallet',
           MetricData=[
               {
                   'MetricName': 'ConnectionSuccess',
                   'Value': 1 if success else 0,
                   'Unit': 'Count'
               }
           ]
       )
   ```

2. **Payment Processing Metrics**
   ```python
   def track_payment_metrics(amount, duration_ms, success):
       cloudwatch.put_metric_data(
           Namespace='X402Payment',
           MetricData=[
               {
                   'MetricName': 'PaymentAmount',
                   'Value': amount,
                   'Unit': 'None'
               },
               {
                   'MetricName': 'PaymentDuration',
                   'Value': duration_ms,
                   'Unit': 'Milliseconds'
               },
               {
                   'MetricName': 'PaymentSuccess',
                   'Value': 1 if success else 0,
                   'Unit': 'Count'
               }
           ]
       )
   ```

## Creating a CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
    --dashboard-name "CDPWalletX402Dashboard" \
    --dashboard-body '{
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Invocations", "FunctionName", "PaymentHandler-dev", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Errors", ".", ".", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Duration", ".", ".", { "stat": "Average", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": "us-east-1",
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
                        [ "AWS/ApiGateway", "4XXError", "ApiName", "nft-payment-api-dev", { "stat": "Sum", "period": 300 } ],
                        [ ".", "5XXError", ".", ".", { "stat": "Sum", "period": 300 } ],
                        [ ".", "Count", ".", ".", { "stat": "Sum", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": "us-east-1",
                    "title": "API Gateway Metrics"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "CDPWallet", "ConnectionSuccess", { "stat": "Sum", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": "us-east-1",
                    "title": "CDP Wallet Connections"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "X402Payment", "PaymentSuccess", { "stat": "Sum", "period": 300 } ],
                        [ ".", "PaymentAmount", { "stat": "Sum", "period": 300 } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": "us-east-1",
                    "title": "X402 Payment Metrics"
                }
            }
        ]
    }'
```

## Log Insights Queries

Use these CloudWatch Logs Insights queries to analyze issues:

### Error Analysis

```
fields @timestamp, @message
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

### Payment Processing Analysis

```
fields @timestamp, @message
| filter @message like "Payment processed"
| stats count() as paymentCount, avg(duration) as avgDurationMs by resource
| sort paymentCount desc
```

### Wallet Connection Analysis

```
fields @timestamp, @message
| filter @message like "Connected wallet"
| stats count() as connectionCount by bin(30m)
| sort @timestamp desc
```

## X-Ray Tracing

Enable X-Ray tracing for your Lambda function to get detailed traces:

1. **Add X-Ray SDK to Lambda function code**:

   ```python
   from aws_xray_sdk.core import xray_recorder
   from aws_xray_sdk.core import patch_all
   
   patch_all()
   
   @xray_recorder.capture('payment_processing')
   def process_payment(event, context):
       # Your payment processing code
       pass
   ```

2. **Add annotations for better search**:

   ```python
   xray_recorder.put_annotation('wallet_address', wallet_address)
   xray_recorder.put_annotation('payment_amount', amount)
   ```

3. **Add custom subsegments**:

   ```python
   with xray_recorder.in_subsegment('verify_signature'):
       # Code to verify signature
       pass
   ```

## Health Check Endpoint

Implement a health check endpoint in your API to monitor system health:

```python
def health_check():
    try:
        # Check DynamoDB connection
        table = dynamodb.Table(os.environ['WALLET_SESSIONS_TABLE'])
        table_status = table.table_status
        
        # Check other dependencies
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'healthy',
                'version': '1.0.0',
                'dependencies': {
                    'dynamodb': 'ok',
                    'x402_api': 'ok'
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e)
            })
        }
```

## Automated Testing

Set up a monitoring Lambda that periodically tests your API endpoints:

1. **Create a separate Lambda function** that runs the `test_deployed_api.py` script
2. **Schedule it with EventBridge** to run every 15 minutes
3. **Send alerts** if tests fail

## Security Monitoring

1. **CloudTrail Alerts** for sensitive operations
   - Monitor for changes to Lambda code or configuration
   - Alert on changes to IAM roles or policies

2. **AWS Config Rules** for compliance monitoring
   - Monitor for exposed API keys or credentials
   - Ensure encryption is enabled on all resources

3. **GuardDuty** for threat detection
   - Enable GuardDuty in your AWS account
   - Create findings for unusual API calls or compromised credentials

## References

- [CloudWatch Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html)
- [X-Ray Documentation](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Monitoring](https://docs.aws.amazon.com/apigateway/latest/developerguide/monitoring-cloudwatch.html)
