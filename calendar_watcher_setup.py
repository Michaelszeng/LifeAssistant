"""
Run this script once to set up the watch request to receive notifications of
calendar event changes. 
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from data import *

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account_v3.json'

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

request_body = {
    'id': '27',  # A unique string ID for this channel
    'type': 'web_hook',         # Type of delivery method
    'address': cloud_function_address,  # The Google Cloud Function URL
}

request = service.events().watch(calendarId=calendar_id, body=request_body)
print('request:', vars(request))
response = request.execute()
print('\nWatch response:', response)