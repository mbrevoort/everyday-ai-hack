import boto3
import email
import json
from openai import OpenAI
from botocore.exceptions import ClientError
import os

bucket_name = "ai-brevoort-com"
model = "gpt-4-1106-preview"

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
                    # print("Body:", body)
        else:
            body = msg.get_payload(decode=True).decode()
            # print("Body:", body)

        # Generate completion
        completion_input = '''Email Subject: {}\nEmail Body:\n{}'''.format(subject, body)
        completion = generate_completion(from_address, completion_input)
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


def generate_completion(sender_email, text):
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai_api_key,
    )

    messages = [
        {"role": "system", "content": "Your name is Everyday AI. You are a helpful assistant receiving commands via email. When you response, only include the text you want to send to the user as a response to an email."},
        {"role": "user", "content": text},
    ]

    response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=get_func_tools(),
    tool_choice="auto")

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:

        available_functions = {
            "get_num_emails_received": get_num_emails_received,
        } 

        messages.append(response_message) 

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                # email=sender_email,
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            ) 

        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
        )  
        return second_response.choices[0].message.content

    return response.choices[0].message.content



def get_num_emails_received():
    # Initialize the S3 client
    s3_client = boto3.client('s3')

    # List objects in a bucket
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix="email/"
    )

    return str(len(response['Contents'])) + " emails received"



def get_func_tools():
    return [{
        "type": "function",
        "function": {
            "name": "get_num_emails_received",
            "description": "Gets the number of emails received by the system",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": [],
            },
        },
    }]
