import os
import json
import re
from unittest import result
from openai import OpenAI
from google_api import is_google_connected, search_gmail
from storage import count_keys, delete_all

model = "gpt-4-1106-preview"
admin_emails = ["mike@brevoort.com"]

openai_api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(
    api_key=openai_api_key,
)

def generate_completion(sender_email, text):

    messages = [
        {"role": "system", "content": "Your name is Everyday AI. You are a helpful assistant receiving commands via email. When you response, only include the text you want to send to the user as a response to an email."},
        {"role": "user", "content": text},
    ]

    tools = get_func_tools(sender_email)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:

        available_functions = {
            tool["function"]["name"]: globals()[tool["function"]["name"]]
            for tool in tools
        }

        messages.append(response_message) 

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            print("Calling function", function_name, "with args", function_args)
            function_response = function_to_call(
                sender_email,
                **function_args
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

def get_num_emails_received(sender_email):
    return str(count_keys("email/") + " emails received")

def delete_all_emails_received(sender_email):
    delete_all("email/")
    return "Deleted all emails received"

def hello_world(send_email):
    return "Hello World! (" + send_email + ")"

def connect_to_gmail(send_email):
    if (is_google_connected(send_email)):
        return "Gmail is connected for " + send_email + "."
    return "Follow this link to connect Everyday AI to Gmail: https://everydayai.brevoort.com/connect-gmail?email=" + send_email

def search_emails(send_email, query):
    response = search_gmail(send_email, query)
    return json.dumps(response)
    
def get_func_tools(sender_email):
    is_admin = sender_email in admin_emails
    tool_functions = []

    if (is_google_connected(sender_email)):
        tool_functions.append(
            {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Search emails",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "A gmail compatible search query",
                            },
                        },
                        "required": ["query"],
                    },
                },
            })
    else:
        tool_functions.append(
        {
            "type": "function",
            "function": {
                "name": "connect_to_gmail",
                "description": "Connect to Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        })

    if is_admin:
        tool_functions.extend(
        [{
            "type": "function",
            "function": {
                "name": "get_num_emails_received",
                "description": "Gets the number of emails received by the system",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_all_emails_received",
                "description": "Deletes all emails received by the system",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }])

    return tool_functions
