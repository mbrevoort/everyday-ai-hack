#!/bin/bash

# make package directory and copy function there
rm -rf package
mkdir -p package
cp email_receiver_lambda.py package/
cp connect_gmail_lambda.py package/

# install dependencies
pip install --force-reinstall --upgrade -t ./package boto3
pip install --force-reinstall --upgrade -t ./package requests
pip install --force-reinstall --upgrade -t ./package openai
pip install --force-reinstall --upgrade -t ./package pydantic

cd package

zip -r function.zip email_receiver_lambda.py *


upsert_function() {
    FUNCTION_NAME=$1
    HANDLER=$2
    ZIP_FILE=fileb://function.zip
    RUNTIME=python3.11
    ROLE="arn:aws:iam::463881414897:role/lambda-ex"

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
}

upsert_function_url() {
    FUNCTION_NAME=$1

    if aws lambda get-function-url-config --function-name $FUNCTION_NAME --no-cli-pager 2>/dev/null; then
        echo "Function URL for $FUNCTION_NAME config exists"
    else
        aws lambda create-function-url-config \
            --function-name $FUNCTION_NAME \
            --auth-type NONE
    fi

    aws lambda get-function-url-config --function-name $FUNCTION_NAME --query 'FunctionUrl' --output text
}


upsert_function "email-ingest" "email_receiver_lambda.lambda_handler"
upsert_function "connect-gmail" "connect_gmail_lambda.lambda_handler"



cd ..
rm -rf package