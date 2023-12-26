import sys
import os
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory + '/../src')
from google_util import search_gmail

from_email = 'mike@brevoort.com'
query = 'from:me'
if len(sys.argv) > 1:
    query = sys.argv[1]

print(search_gmail(from_email, query))
