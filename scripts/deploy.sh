#!/bin/bash

# make package directory and copy function there
rm -rf package
mkdir -p package
cp -r src/* package/

# install dependencies
pip install --quiet --force-reinstall --upgrade -t ./package boto3 requests openai pydantic google-api-python-client google-auth-httplib2 google-auth-oauthlib bs4

cd package
zip  -q -r function.zip email_receiver_lambda.py *

update_function_env() {
    FUNCTION_NAME=$1
        # updaet lambda environment variables with values from .env
        json_env=$(awk -F= '{printf "\"%s\":\"%s\",", $1, $2}' ../.env | sed 's/,$//')
        json_env="{\"Variables\":{${json_env}}}"
        echo "Updating $FUNCTION_NAME environment variables with values from .env"
        aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment "$json_env" --no-cli-pager >/dev/null
}


upsert_function() {
    FUNCTION_NAME=$1
    HANDLER=$2
    ZIP_FILE=fileb://function.zip
    RUNTIME=python3.11
    ROLE="arn:aws:iam::463881414897:role/lambda-ex"

    # Check if the Lambda function exists
    if aws lambda get-function --function-name $FUNCTION_NAME --no-cli-pager >/dev/null; then
        # Function exists, update it
        echo "Updating $FUNCTION_NAME Lambda function"
        aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file $ZIP_FILE --no-cli-pager >/dev/null
    else
        # Function doesn't exist, create it
        echo "Creating $FUNCTION_NAME new Lambda function"
        aws lambda create-function \
            --function-name $FUNCTION_NAME \
            --zip-file $ZIP_FILE \
            --handler $HANDLER \
            --runtime $RUNTIME \
            --role $ROLE \
            --timeout 60 \
            --no-cli-pager \
            --query 'FunctionArn'
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

    aws lambda get-function-url-config --function-name $FUNCTION_NAME --query 'FunctionUrl' --output text >/dev/null
}


upsert_function "email-ingest" "email_receiver_lambda.lambda_handler"
upsert_function "connect-gmail" "connect_gmail_lambda.lambda_handler"
update_function_env "email-ingest"
update_function_env "connect-gmail"



cd ..
rm -rf package