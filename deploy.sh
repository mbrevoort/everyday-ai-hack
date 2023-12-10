#!/bin/bash

FUNCTION_NAME="email-ingest"
ZIP_FILE="fileb://function.zip"
HANDLER="email_receiver_lambda.lambda_handler"
RUNTIME="python3.8"
ROLE="arn:aws:iam::463881414897:role/lambda-ex"

#!/bin/bash
zip -r function.zip email_receiver_lambda.py requirements.txt

# Check if the Lambda function exists
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    # Function exists, update it
    echo "Updating existing Lambda function: $FUNCTION_NAME"
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file $ZIP_FILE
else
    # Function doesn't exist, create it
    echo "Creating new Lambda function: $FUNCTION_NAME"
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --zip-file $ZIP_FILE \
        --handler $HANDLER \
        --runtime $RUNTIME \
        --role $ROLE
fi
