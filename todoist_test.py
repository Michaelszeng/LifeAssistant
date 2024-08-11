import requests

from data import *

def todoist_sync_request():
    url = "https://api.todoist.com/sync/v9/sync"
    headers = {
        "Authorization": "Bearer " + todoist_api_token
    }
    data = {
        "sync_token": "*",
        "resource_types": '["projects"]'
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()  # Convert the response to a dictionary
    else:
        # Handle the error case
        print(f"Request failed with status code {response.status_code}")
        return None


response_dict = todoist_sync_request()
if response_dict:
    print(response_dict)
