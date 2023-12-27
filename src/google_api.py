import os
from urllib.parse import urlencode
import requests
import json
import base64
import re
from storage import save, get
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def save_google_credentials(email, credentials):
    value = credentials.to_json()
    save('google/' + email, value)

def get_google_credentials(email):
    value = get('google/' + email)
    if value == None:
        print("No google credentials found for " + email)
        return None

    credentials_dict = json.loads(value)
    credentials = Credentials(**credentials_dict)

    if not credentials.valid:
        print("credentials for " + email + " not valid")
        if credentials.expired and credentials.refresh_token:
            print("credentials for " + email + " expired, refreshing")
            credentials.refresh(Request())
            save_google_credentials(email, credentials.to_json())
        else:
            print("credentials for " + email + " expired without refresh token")
            return None
        
    return credentials

def is_google_connected(email):
    is_connected = get_google_credentials(email) != None
    print("is_google_connected for " + email + ":", is_connected)
    return is_connected

def generate_auth_url(state):
    # Construct the authorization URL with the required parameters
    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
        'redirect_uri': os.environ.get('REDIRECT_URI', ''),
        'response_type': 'code',
        'scope': ','.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state
    }
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    return auth_url

def exchange_code_for_credentials(code):
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
    return convert_oauth2_tokens_to_credentials(response.json())

def convert_oauth2_tokens_to_credentials(tokens):
    credentials = Credentials(
        token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.environ['GOOGLE_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_CLIENT_SECRET']
    )
    return credentials


def search_gmail(send_email, query):
    response = {
        'metadata': '',
        'messages': []
    }
    credentials = get_google_credentials(send_email)
    if credentials == None:
        response['metadata'] = "Gmail not connected for " + send_email
        return response
    
    service = build('gmail', 'v1', credentials=credentials)
    
    # Search gmail api for emails
    # Use the API to search emails
    user_id = 'me'

    # Call the Gmail API
    results = service.users().messages().list(userId=user_id, q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
        response['metadata'] = "No messages found"
        return response
    else:
        response['metadata'] = "Email messages found for the query: " + query + "."

        for message in messages: 
            msg = service.users().messages().get(userId=user_id, id=message['id'], format='full').execute()

            headers = msg['payload']['headers']
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            from_ = next(header['value'] for header in headers if header['name'] == 'From')

            # read the email body and decode it
            # Check if the email is multipart
            try:
                if 'parts' in msg['payload']:
                    # Assume the first part is the text content
                    part = msg['payload']['parts'][0]
                    body_data = part['body']['data']
                else:
                    # The body is in the payload itself
                    body_data = msg['payload']['body']['data']
                
                # Decode the body
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            except:
                body = msg['snippet']
                
            # strip out any html tags and content that is not text from body
            body = BeautifulSoup(body, "html.parser").get_text()
            
            # remove extraneous characters
            body = remove_extraneous_characters(body)

            response['messages'].append({
                'subject': subject,
                'from': from_,
                'body': body
            })  

        return response

def remove_extraneous_characters(s):
    # Replace \n and \r with a space
    s = re.sub(r'[\n\r]+', ' ', s)
    # Optional: Remove other control characters like \t
    s = re.sub(r'[\t]+', ' ', s)
    # Remove unicode non-breaking spaces and similar characters
    s = re.sub(r'[\u0080-\uFFFF]+', ' ', s)
    # Remove extra spaces (more than one space)
    s = re.sub(r' +', ' ', s)
    # Optional: Remove leading and trailing whitespace
    s = s.strip()
    return s