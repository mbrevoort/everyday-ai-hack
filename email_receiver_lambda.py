import boto3
import email
import json

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
        print("Subject:", msg['Subject'])
        print("From:", msg['From'])

        # Process and print the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    print("Body:", body.decode())
        else:
            body = msg.get_payload(decode=True)
            print("Body:", body.decode())

    except Exception as e:
        print(e)
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Email processed')
    }
