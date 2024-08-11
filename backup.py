import functions_framework
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import logging

from data import *

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

# Perform initial full sync
events_result = service.events().list(
    calendarId=calendar_id,
    maxResults=2500,
    singleEvents=True,
    orderBy='startTime'
).execute()

events = events_result.get('items', [])
sync_token = events_result.get('nextSyncToken')

# Save sync_token for future use
print('Initial sync token:', sync_token)


def sync_calendar():
    global sync_token
    events_result = service.events().list(
        calendarId=calendar_id,
        syncToken=sync_token
    ).execute()

    # Process events
    for event in events_result.get('items', []):
        print('Event:', event)

    # Update sync token
    sync_token = events_result.get('nextSyncToken')


@functions_framework.http
def event_callback(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    print(f'Headers: {request.headers}')
    print(f'Body: {request.data}')
    print(f'Form: {request.form}')

    request_json = request.get_json(silent=True)
    request_args = request.args
    
    print(f'Parsed JSON: {request_json}')

    sync_calendar()

    if request_json:
        print("request_json")
        resource_id = request_json.get('resourceId')
        if resource_id:
            print("resource_id")
            # Get the event details from the calendar
            event = service.events().get(calendarId=calendar_id, eventId=resource_id).execute()
            if event.get('status') == 'confirmed' and event.get('created') == event.get('updated'):
                print(f'New event created: {event}')
                
    return 'OK', 200
