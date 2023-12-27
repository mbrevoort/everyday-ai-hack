import boto3
import json
from botocore.exceptions import ClientError

def send_email(subject, body, to_addresses, from_address, aws_region="us-east-2"):
    # Create a new SES client
    client = boto3.client('ses', region_name=aws_region)

    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': to_addresses,
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=from_address,
        )
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")