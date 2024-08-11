# import functions_framework
from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import time

from data import *

DEBUG = 0

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account_v3.json'

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)


################################################################################
### Helper Functions
################################################################################
def get_token():
    try:
        with open("token.txt", "r") as f:
            date, token = f.readline().split(" ")
    except FileNotFoundError:
        token = None
        date = None
    return token, date


def store_token(token):
    with open("token.txt", "w") as f:
        f.write(str(datetime.now().date()) + " " + token)


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
        if event.status == "confirmed":  # Event made or modified
            print('Event:', event)

    # Update sync token
    sync_token = events_result.get('nextSyncToken')

    if DEBUG:
        print('New sync token:', sync_token)

    store_token(sync_token)
                
    return 'OK', 200


data: dict[str, Any] = {}

if __name__ == "__main__":
    main(data)