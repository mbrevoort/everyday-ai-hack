import boto3
import email
import json
from openai import OpenAI
from botocore.exceptions import ClientError
import os

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def lambda_handler(event, context):
    # Initialize the S3 client
    s3_client = boto3.client('s3')

    try:
        # Extract S3 bucket name and email key from the SES event
        ses_notification = event['Records'][0]['ses']
        mail = ses_notification['mail']
        message_id = mail['messageId']

        print("Mail:", json.dumps(mail))

        bucket_name = "ai-brevoort-com"
        email_key = "email/" + message_id

        print("Using S3 bucket:", bucket_name, "and key:", email_key, "to fetch email content")

        # Fetch the email from S3
        email_object = s3_client.get_object(Bucket=bucket_name, Key=email_key)
        email_content = email_object['Body'].read().decode('utf-8')
        
        # Parse the email content
        msg = email.message_from_string(email_content)
        subject = msg['Subject']
        from_address = msg['From']
        print("Subject:", subject)
        print("From:", from_address)

        # Check if from_address contains mike@brevoort.com
        if "brevoort.com" not in from_address:
            print("Not processing email from", from_address)
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
                    print("Body:", body)
        else:
            body = msg.get_payload(decode=True).decode()
            print("Body:", body)

        # Generate completion
        completion = generate_completion("Email Subject: " + subject + "\nEmail Body:\n" + body)
        print("Response completion:", completion)

        # Send email
        subject = "Re: " + subject
        send_email(subject, completion, [from_address], msg['To'])

    except Exception as e:
        print(e)
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Email processed')
    }

def generate_completion(text):
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "Your name is Everyday AI. You are a helpful assistant receiving commands via email. When you response, only include the text you want to send to the user as a response to an email."},
        {"role": "user", "content": text},
    ])

    return response.choices[0].message.content


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
