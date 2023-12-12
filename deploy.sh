#!/bin/bash

FUNCTION_NAME="email-ingest"
ZIP_FILE="fileb://function.zip"
HANDLER="email_receiver_lambda.lambda_handler"
RUNTIME="python3.11"
ROLE="arn:aws:iam::463881414897:role/lambda-ex"

# make package directory and copy function there
rm -rf package
mkdir -p package
cp email_receiver_lambda.py package/
# install dependencies
pip install --force-reinstall --upgrade -t ./package boto3
pip install --force-reinstall --upgrade -t ./package openai
pip install --force-reinstall --upgrade -t ./package pydantic

cd package

#!/bin/bash
zip -r function.zip email_receiver_lambda.py *

# Check if the Lambda function exists
if aws lambda get-function --function-name $FUNCTION_NAME --no-cli-pager 2>/dev/null; then
    # Function exists, update it
    echo "Updating existing Lambda function: $FUNCTION_NAME"
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file $ZIP_FILE --no-cli-pager
else
    # Function doesn't exist, create it
    echo "Creating new Lambda function: $FUNCTION_NAME"
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --zip-file $ZIP_FILE \
        --handler $HANDLER \
        --runtime $RUNTIME \
        --role $ROLE \
        --no-cli-pager
fi

cd ..
rm -rf package