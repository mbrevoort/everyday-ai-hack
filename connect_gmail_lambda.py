import os
import boto3
from urllib.parse import urlencode
import requests

s3 = boto3.client('s3')

def lambda_handler(event, context):
    query_params = event.get('queryStringParameters', {})
    email = query_params.get('email', '')
    print("email:", email)

    if (email != ''):
        # Generate the authorization URL for Google OAuth
        auth_url = generate_auth_url()

        # Redirect the user to the authorization URL
        return {
            'statusCode': 302,
            'headers': {
                'Location': auth_url
            }
        }

    # Extract the authorization code from the query parameters
    code = query_params['code']
    print("code:", code)
    token = exchange_code_for_token(code)
    print("token:", token)

def generate_auth_url():
    # Construct the authorization URL with the required parameters
    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
        'redirect_uri': os.environ.get('REDIRECT_URI', ''),
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/gmail.readonly',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    return auth_url

def exchange_code_for_token(code):
    # Construct the request payload
    payload = {
        'code': code,
        'client_id': os.environ['GOOGLE_CLIENT_ID'],
        'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
        'redirect_uri': os.environ['REDIRECT_URI'],
        'grant_type': 'authorization_code'
    }

    # Make a POST request to Google's token endpoint
    response = requests.post('https://accounts.google.com/o/oauth2/token', data=payload)

    # Parse the response and extract the access token
    token = response.json()['access_token']

    # Return the access token
    return token

#def store_token_in_s3(email, token):
    # Store the token in S3 under a key mapped to the user's email address
    # Use the email as the S3 key and the token as the value
