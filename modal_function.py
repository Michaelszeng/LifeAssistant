from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.cloud import tasks_v2
from google.cloud import firestore
from google.protobuf import timestamp_pb2
from huggingface_hub import login, snapshot_download
import transformers
from transformers import AutoTokenizer
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import http.client, urllib
import modal
import torch
import uuid
import json
import os
import pytz
import time

from data_files.data import *

app = modal.App()

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install_from_requirements(os.path.join(os.getcwd(), "modal_requirements.txt"))
)

# Firestore data
TOKEN_DOC = 'sync_token'
WATCHER_DOC = 'calendar_watcher_data'
TASKS_DOC = 'scheduled_tasks'
COLLECTION = 'LifeAssistant'  # Replace with your Firestore collection name


################################################################################
### Helper Functions
################################################################################
def get_token():
    global db
    doc_ref = db.collection(COLLECTION).document(TOKEN_DOC)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        token = data.get('token')
        date = data.get('date')
    else:
        token = None
        date = None
    
    return token, date


def store_token(token):
    global db
    doc_ref = db.collection(COLLECTION).document(TOKEN_DOC)
    doc_ref.set({
        'date': str(datetime.now().date()),
        'token': token
    })


def get_calendar_watcher_data():
    global db
    doc_ref = db.collection(COLLECTION).document(WATCHER_DOC)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        resource_id = data.get('resource_id')
        channel_id = data.get('channel_id')
    else:
        resource_id = None
        channel_id = None
    
    return resource_id, channel_id


def store_calendar_watcher_data(resource_id, channel_id):
    global db
    doc_ref = db.collection(COLLECTION).document(WATCHER_DOC)
    doc_ref.set({
        'resource_id': resource_id,
        'channel_id': channel_id
    })


def get_scheduled_tasks():
    global db
    doc_ref = db.collection(COLLECTION).document(TASKS_DOC)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict().get('tasks', [])
    else:
        data = []
    
    return data


def add_scheduled_task(log_entry):
    global db
    doc_ref = db.collection(COLLECTION).document(TASKS_DOC)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict().get('tasks', [])
    else:
        data = []
    
    data.append(log_entry)
    
    doc_ref.set({
        'tasks': data
    })


def remove_scheduled_task(event_id):
    global db
    data = get_scheduled_tasks()

    # Find the task corresponding to the event_id
    task_to_delete = None
    for entry in data:
        if entry['event_id'] == event_id:
            task_to_delete = entry
            break

    if not task_to_delete:
        print(f"No task found for event_id: {event_id}")
        return None

    task_name = task_to_delete['task_name']

    # Remove the task from the list
    updated_data = [entry for entry in data if entry['event_id'] != event_id]

    # Write the updated list back to the Firestore document
    doc_ref = db.collection(COLLECTION).document(TASKS_DOC)
    doc_ref.set({
        'tasks': updated_data
    })
    
    print(f"Log entry for event_id {event_id} deleted successfully.")

    return task_name


def stop_calendar_watcher(resource_id, channel_id):
    global service
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
    global service
    channel_id = str(uuid.uuid4())

    request_body = {
        'id': channel_id,  # A unique string ID for this channel
        'type': 'web_hook',         # Type of delivery method
        'address': cloud_function_address,  # The Google Cloud Function URL
        'expiration': 1893456000000,  # Basically will cap at Google's 30 day limit.
    }

    try:
        request = service.events().watch(calendarId=calendar_id, body=request_body)
        response = request.execute()
        print('\nWatch response:', response)

        resource_id = response.get("resourceId", None)
        store_calendar_watcher_data(resource_id, channel_id)

    except Exception as e:
        print('An error occurred:', e)


def schedule_text_message(event_id, message, schedule_time):
    client = tasks_v2.CloudTasksClient()

    # Define the queue path
    project = google_cloud_project_id
    queue = 'text-messages'
    location = 'us-central1'
    parent = client.queue_path(project, location, queue)

    # Prepare the payload
    payload = {
        'text_message': True,
        'event_id': event_id,
        'message': message
    }

    # Create the task
    task = {
        'http_request': {  
            'http_method': tasks_v2.HttpMethod.POST,
            'url': cloud_function_address,  
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(payload).encode()
        }
    }

    # Convert the schedule_time to a timestamp
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(schedule_time)
    task['schedule_time'] = timestamp

    # Create the task in the queue
    response = client.create_task(parent=parent, task=task)
    task_name = response.name
    print(f'Task created: {task_name}')

    # Write the payload and task_name to a JSON file for tracking
    log_entry = {
        'task_name': task_name,
        'event_id': event_id,
        'schedule_time': schedule_time.isoformat()
    }
    add_scheduled_task(log_entry)

    # TEMPORARY
    send_push_notif("this is a test message!", event_id)

    return task_name


def cancel_text_message(event_id):
    client = tasks_v2.CloudTasksClient()
    
    # Remove task from task log
    task_name = remove_scheduled_task(event_id)

    # Delete the task from Google Cloud Tasks
    try:
        client.delete_task(name=task_name)
        print(f'Task {task_name} deleted successfully')
    except Exception as e:
        print(f"Error deleting task {task_name}: {e}")
        return


def send_push_notif(message_body, event_id):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": pushover_api_token,
        "user": pushover_user_key,
        "title": "LifeAssistant",
        "message": message_body,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
    
    print("Sent Push Notification.")

    # After task is complete (text is sent), remove it from the tasks log
    remove_scheduled_task(event_id)


################################################################################
### Modal App
################################################################################
@app.cls(gpu="any", image=image, mounts=[modal.Mount.from_local_dir(os.path.join(os.getcwd(), "data_files"), remote_path="/root/data_files")])
class Model:

    @modal.build()  # add another step to the image build
    def build(self):
        """
        Run on building of the container (i.e. once per deployment). Downloads 
        the model weights.
        """
        global sync_token
        global db
        global service

        print("BULDING MODAL CONTAINER.")

        MODEL_DIR = 'llama'

        os.makedirs(MODEL_DIR, exist_ok=True)
        login(token=huggingface_token)

        # Download the model snapshot to a specific directory
        self.model_dir = snapshot_download(
            repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
            revision="main",
            local_dir=MODEL_DIR
        )

        ########################################################################
        ### Google API Authentication and Initialization
        ########################################################################
        # Retrieve service account
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        SERVICE_ACCOUNT_FILE = 'data_files/service_account.json'
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Initialize Calendar
        service = build('calendar', 'v3', credentials=credentials)

        # Initialize Firestore
        db = firestore.Client()

        ########################################################################
        ### Establish watcher for Calendar
        ########################################################################
        resource_id, channel_id = get_calendar_watcher_data()
        if resource_id and channel_id:  # Stop the old watcher
            stop_calendar_watcher(resource_id, channel_id)
        # Establish new watcher
        start_calendar_watcher()

        ########################################################################
        ### Get Initial Sync with Calendar
        ########################################################################
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

        print('Initial sync token:', sync_token)

        store_token(sync_token)   


    @modal.method()
    def setup(self):
        """
        Runs during container's start (i.e. very cold start), but not every time 
        the function is invoked. Load in the weights for the tokenizer and 
        pipeline.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)

        self.pipe = transformers.pipeline(
            "text-generation",
            model=self.model_dir,
            model_kwargs={
                "torch_dtype": torch.bfloat16,
                "quantization_config": {"load_in_4bit": True},
                "low_cpu_mem_usage": True,
            },
            device="cuda",
        )


    # @app.local_entrypoint()  # Use this instead of the below during development to run the function automatically, not as a web endpoint
    @modal.web_endpoint(method="POST")
    def web_endpoint(request: Optional[dict[str, Any]] = None) -> str:
        """
        Runs whenever the HTTP endpoint is used.
        """
        global sync_token
        global db
        global service

        print("START WEB ENDPOINT")

        # First re-establish calendar watcher so that it never expires
        resource_id, channel_id = get_calendar_watcher_data()
        if resource_id and channel_id:  # Stop the old watcher
            try:
                stop_calendar_watcher(resource_id, channel_id)
            except:
                print("stop_calendar_watcher() failed.")
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
                    event_id = event.get('id')

                    # In case this event has been modified instead of created, attempt to cancel its associated text message.
                    # If this event is new, cancel_text_message() will fail gracefully
                    cancel_text_message(event_id)

                    # Extract event start datetime
                    date_time_str = event['dateTime']
                    time_zone_str = event['timeZone']
                    naive_datetime = datetime.fromisoformat(date_time_str)
                    time_zone = pytz.timezone(time_zone_str)
                    event_start_time = time_zone.localize(naive_datetime)
                    text_schedule_time = event_start_time - timedelta(hours=4)  # Ready to be passed to schedule_text_message()

                    message = "test!"
                    schedule_text_message(event_id, message, text_schedule_time)

                elif event.get('status', "") == "cancelled":  # Event made or modified
                    print('GCal event cancelled:', event)
                    event_id = event.get('id')

                    cancel_text_message(event_id)

            # Update sync token
            sync_token = events_result.get('nextSyncToken')
            print('New sync token:', sync_token)

            store_token(sync_token)

        else:  
            if 'text_message' in data:  # Text message task
                send_push_notif(data['message'], data['event_id'])

            # TODOist task update
            elif 'event_name' in data and data['event_data']['project_id'] in todoist_projects and not data['event_data']['is_deleted'] and (data['event_name'] == 'item:added' or data['event_name'] == 'item:updated'):
                # Process the new task
                print(f"TODOist task added/updated: {data['event_data']['content']}")
                
                task_id = data['event_data']['v2_id']

                # Get the current time in the specified timezone
                time_zone = pytz.timezone('America/New_York')
                now = datetime.now(time_zone)
                text_schedule_time = now + timedelta(seconds=15)  # Make task slightly in the future

                message = "test!"
                schedule_text_message(task_id, message, text_schedule_time)

        return 'OK', 200

