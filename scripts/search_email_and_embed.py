import json
import sys
import os
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory + '/../src')
from openai_tools import search_emails

from_email = 'mike@brevoort.com'
query = 'from:me'
if len(sys.argv) > 1:
    query = sys.argv[1]

result = search_emails(from_email, query)
print(json.dumps(result, indent=4))
