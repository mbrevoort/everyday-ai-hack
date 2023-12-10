import json
import boto3
import email
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    ses_client = boto3.client('ses')
    
    # Get the SES message
    ses_notification = event['Records'][0]['ses']
    message_id = ses_notification['mail']['messageId']

    try:
        response = ses_client.get_received_message(MessageId=message_id)
        email_content = response['Content']
        
        # Parse the email content
        msg = email.message_from_string(email_content)
        print("Subject:", msg['Subject'])
        print("From:", msg['From'])
        
        # Process email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    print("Body:", body.decode())
        else:
            body = msg.get_payload(decode=True)
            print("Body:", body.decode())

    except ClientError as e:
        print(e.response['Error']['Message'])
    
    return {
        'statusCode': 200,
        'body': json.dumps('Email processed')
    }
