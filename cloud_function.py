# import functions_framework
from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import uuid
import time

from data import *

DEBUG = 0

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)


################################################################################
### Helper Functions
################################################################################
def get_token():
    try:
        with open("gcal_sync_token.txt", "r") as f:
            date, token = f.readline().split(" ")
    except FileNotFoundError:
        token = None
        date = None
    return token, date


def store_token(token):
    with open("gcal_sync_token.txt", "w") as f:
        f.write(str(datetime.now().date()) + " " + token)


def get_calendar_watcher_data():
    try:
        with open("calendar_watcher_data.txt", "r") as f:
            resource_id, channel_id = f.readline().split(" ")
    except FileNotFoundError:
        resource_id = None
        channel_id = None
    return resource_id, channel_id


def store_calendar_watcher_data(resource_id, channel_id):
    with open("calendar_watcher_data.txt", "w") as f:
        f.write(resource_id + " " + channel_id)


def stop_calendar_watcher(resource_id, channel_id):
    request_body = {
        'id': channel_id,
        'resourceId': resource_id,
    }

    try:
        request = service.channels().stop(body=request_body)
        response = request.execute()
        print('Watcher Stop succeeded.')
    except Exception as e:
        print('An error occurred:', e)


def start_calendar_watcher():
    channel_id = str(uuid.uuid4())

    request_body = {
        'id': channel_id,  # A unique string ID for this channel
        'type': 'web_hook',         # Type of delivery method
        'address': cloud_function_address,  # The Google Cloud Function URL
    }

    try:
        request = service.events().watch(calendarId=calendar_id, body=request_body)
        response = request.execute()
        print('\nWatch response:', response)

        resource_id = response.get("resourceId", None)
        store_calendar_watcher_data(resource_id, channel_id)

    except Exception as e:
        print('An error occurred:', e)


################################################################################
### Establish Listener to Calendar
################################################################################
resource_id, channel_id = get_calendar_watcher_data()
if resource_id and channel_id:  # Stop the old watcher
    stop_calendar_watcher(resource_id, channel_id)
# Establish new watcher
start_calendar_watcher()


################################################################################
### Get Initial Sync with Calendar
################################################################################
sync_token, date_stored = get_token()
page_token = None

# deal with pagination of events; each page either has a page token or (is the last page and) has the sync token
time_max = datetime.now(timezone.utc) + timedelta(days=2)
time_max = datetime.strftime(time_max, "%Y-%m-%dT%H:%M:%S%z")
events_result = (
    service.events()
    .list(calendarId=calendar_id, singleEvents=True, timeMax=str(time_max))
    .execute()
)
while sync_token is None:
    nextPageToken = events_result.get("nextPageToken", None)
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            singleEvents=True,
            pageToken=nextPageToken,
            timeMax=str(time_max),
            maxResults=2500,  # max of 2500
        )
        .execute()
    )
    sync_token = events_result.get("nextSyncToken", None)

if DEBUG:
    print('Initial sync token:', sync_token)

store_token(sync_token)   


################################################################################
### Handle Notifications from Calendar upon event changes
################################################################################

# @functions_framework.http
# def event_callback(request):
def main(request: Optional[dict[str, Any]] = None) -> str:
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    global sync_token

    # First re-establish calendar watcher so that it never expires
    resource_id, channel_id = get_calendar_watcher_data()
    if resource_id and channel_id:  # Stop the old watcher
        stop_calendar_watcher(resource_id, channel_id)
    # Establish new watcher
    start_calendar_watcher()

    data = request.json

    if not data:  # GCal event updated
        # Retrieve updated events
        events_result = service.events().list(
            calendarId=calendar_id,
            maxResults=2500,  # max of 2500
            singleEvents=True,
            syncToken=sync_token,
        ).execute()

        events = events_result.get('items', [])
        print(f'Retrieved {len(events)} events')

        # Process events
        for event in events:
            if event.get('status', "") == "confirmed":  # Event made or modified
                print('GCal event made or modified:', event)

        # Update sync token
        sync_token = events_result.get('nextSyncToken')

        if DEBUG:
            print('New sync token:', sync_token)

        store_token(sync_token)

    else:  # TODOist task update
        if 'event_name' in data and data['event_data']['project_id'] in todoist_projects and not data['event_data']['is_deleted'] and (data['event_name'] == 'item:added' or data['event_name'] == 'item:updated'):
            # Process the new task
            print(f"TODOist task added/updated: {data['event_data']['content']}")

    return 'OK', 200





################################################################################
### Build fake Flask Request for testing
################################################################################

from flask import Request
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WerkzeugRequest

# Define minimal headers (only essential ones)
headers = {
    "Host": "localhost",
    "Content-Type": "application/json",
}

# Define an empty JSON body
body = b'{}'

# Create the environment builder
builder = EnvironBuilder(
    method='POST',
    headers=headers,
    data=body,
)
# Build the environment
env = builder.get_environ()
request = Request(env)


if __name__ == "__main__":
    main(request)