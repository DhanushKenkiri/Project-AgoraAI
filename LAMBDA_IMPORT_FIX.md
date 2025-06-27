# AWS Lambda "No module named 'botocore.docs'" Error Fix

## Error Description

When deploying your Lambda function, you encountered the following error:

```
{
  "errorMessage": "Unable to import module 'lambda_handler': No module named 'botocore.docs'",
  "errorType": "Runtime.ImportModuleError",
  "requestId": "",
  "stackTrace": []
}
```

This error occurs because your Lambda deployment is missing the proper `botocore` module with all its dependencies. The AWS Lambda runtime includes boto3 and botocore by default, but sometimes when you package your own version, there can be conflicts or missing components.

## Solution

We've created a two-part solution:

1. A boto3/botocore Lambda Layer that properly includes all dependencies
2. A fixed deployment package that removes the conflicting boto3/botocore modules

### Option 1: Use Lambda Layer (Recommended)

This approach separates boto3/botocore into a dedicated Lambda layer, which is the AWS recommended approach for handling shared libraries.

#### Steps to deploy:

1. Upload `boto3_layer.zip` as a Lambda Layer in AWS Console:
   - Go to AWS Lambda Console
   - Navigate to "Layers" section
   - Click "Create Layer"
   - Name it "boto3-layer"
   - Upload the `boto3_layer.zip` file
   - Select all compatible runtimes
   - Click "Create"

2. Upload `bedrock_deployment_fixed.zip` as your Lambda function code:
   - Go to your Lambda function
   - Under "Code" tab, click "Upload from"
   - Select ".zip file"
   - Upload `bedrock_deployment_fixed.zip`

3. Attach the boto3 layer to your Lambda function:
   - In your function configuration, scroll down to "Layers"
   - Click "Add a layer"
   - Select "Custom layers"
   - Choose the "boto3-layer" you created
   - Click "Add"

### Option 2: Fix Deployment Process

If you prefer to create a single deployment package that works without layers, modify your `create_bedrock_package.py` script to properly handle boto3/botocore dependencies:

1. Add boto3 and botocore to your requirements.txt with specific versions:
   ```
   boto3==1.34.23
   botocore==1.34.23
   ```

2. Modify the package creation to include all necessary dependencies, including the docs modules.

### What Caused the Issue?

This issue happens because:

1. The AWS Lambda environment includes boto3 and botocore by default, but your package includes its own versions
2. When packaging, pip sometimes doesn't include all the necessary submodules of botocore
3. The `botocore.docs` module is needed for boto3 to properly initialize, but it might be omitted in simplified installations

## Alternative Solutions

1. **Use default Lambda boto3**: Remove boto3 and botocore from your package entirely and rely on the versions provided by AWS Lambda.

2. **Use virtualenv**: Package your Lambda function using a virtual environment to ensure all dependencies are properly captured.

3. **Add explicit imports**: Ensure your code has explicit imports for all boto3/botocore modules you need.

## Verification

After applying the solution, your Lambda function should start successfully without the import error. If you encounter other issues, check CloudWatch Logs for detailed error messages.

---

Let me know if you need any additional assistance with your Lambda deployment!
