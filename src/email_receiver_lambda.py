import boto3
import email
import json
from botocore.exceptions import ClientError
from googleapiclient.discovery import build

import storage
from openai import OpenAI
from openai_tools import generate_completion
from emails import send_email


def lambda_handler(event, context):
    # Initialize the S3 client
    s3_client = boto3.client('s3')

    try:
        # Extract S3 bucket name and email key from the SES event
        ses_notification = event['Records'][0]['ses']
        mail = ses_notification['mail']
        message_id = mail['messageId']

        print("Mail:", json.dumps(mail))

        email_key = "email/" + message_id
        email_content = storage.get(email_key)
        
        # Parse the email content
        msg = email.message_from_string(email_content)
        subject = msg['Subject']
        from_field = msg.get('From')
        sender_name, sender_email = email.utils.parseaddr(from_field)

        print("Subject:", subject)
        print("From:", sender_name, sender_email)

        # Check if from_address contains brevoort.com
        if "brevoort.com" not in sender_email:
            print("Not processing email from", sender_email)
            return {
                'statusCode': 200,
                'body': json.dumps('Email processed')
            }

        body = ""

        # Process and print the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # Generate completion
        completion_input = '''Email Subject: {}\nEmail Body:\n{}'''.format(subject, body)
        completion = generate_completion(sender_email, completion_input)
        print("Response completion:", completion)

        # Send email
        subject = "Re: " + subject
        send_email(subject, completion, [from_field], msg['To'])

    except Exception as e:
        print(e)
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Email processed')
    }
