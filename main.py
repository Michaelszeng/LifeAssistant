# import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

# import functions_framework
import pytz

# from flask import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from data import *

os.environ["PRIMARY_CALENDAR_EMAIL"] = calendar_id

# @functions_framework.http
# def main(request: Request) -> str:
#     data = json.loads(request.data)
def main(request: Optional[dict[str, Any]] = None) -> str:

    credentials = service_account.Credentials.from_service_account_file(
        "service_account_v3.json",  # getting credentials from parent directory
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    try:
        service = build(
            "calendar", "v3", credentials=credentials, cache_discovery=False
        )

        now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        now_plus_24 = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"

        events_list = (
            service.events()
            .list(
                calendarId=os.environ["PRIMARY_CALENDAR_EMAIL"],
                timeMin=now,
                timeMax=now_plus_24,
                singleEvents=True,
                orderBy="startTime",
                maxResults=2500  # The page size can never be larger than 2500 events.
                # q="string search terms",
                # ^ Free text search terms to find events that match these terms in the following fields:
                #   summary, description, location, attendee's displayName, attendee's email. Optional.
            )
            .execute()
        )

        events = events_list.get("items", [])

        if not events:
            return "No upcoming events found."

        for event in events:
            start = datetime.fromisoformat(event["start"]["dateTime"])
            end = datetime.fromisoformat(event["end"]["dateTime"])
            title = event["summary"]

            # do something with events...
            print("%s - %s: %s" % (start, end, title))

        return "Done."

    except Exception as e: 
        print("An error occurred: %s" % e)


data: dict[str, Any] = {}

if __name__ == "__main__":
    main(data)