import os
from urllib.parse import urlencode
import requests
import json
from google_util import generate_auth_url, exchange_code_for_creds, save_google_creds

def lambda_handler(event, context):
    query_params = event.get('queryStringParameters', {})
    email = query_params.get('email', '')
    code = query_params.get('code', '')

    # if code is empty, we need to redirect to Google OAuth
    if (code == ''):
        if (email == ''):
            return {
                'statusCode': 400,
                'body': 'Missing email query parameter'
            }

        # Generate the authorization URL for Google OAuth
        state = json.dumps({'email': email})
        auth_url = generate_auth_url(state)

        print("Redirecting to Google for Gmail authorization with email:", email)

        # Redirect the user to the authorization URL
        return {
            'statusCode': 302,
            'headers': {
                'Location': auth_url
            }
        }

    # Extract the email from the state
    state = json.loads(query_params['state'])  # Parse state as JSON
    email = state['email']

    if (email == ''):
        return {
            'statusCode': 400,
            'body': 'Missing email from state of result, cannot continue'
        }

    # Exchange the authorization code for an access token
    creds = exchange_code_for_creds(code)
    print("creds for " + email + ":", creds)
    save_google_creds(email, creds)

    return {
        'statusCode': 200,
        'body': 'Gmail successfully connected for ' + email + '! You can close this window.'
    }

