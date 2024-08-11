# Life Assistant

A LLM Integration with your Google Calendar and Todoist to send you relevant reminders (via text message) related your events and tasks. You can customize/slowly accrue the list of reminders you want.

## Current TODOs:
- Either create scheduler for Cloud Function or figure out how to remove expiration on calendar watcher
- TODOist integration, LLM integration, text message integration

## Installation and Setup

#### Creating the Google Cloud Function
- Google Cloud function that enables UNAUTHORIZED access

- Download service account

#### Setting Calendar Permissions
1. Go to the settings menu in your Google Calendar (gear icon top right corner)
2. Click Settings for my calendar.
3. Select the calendar you want to share.
4. In Calendar settings, under Share with specific people or groups, click + Add people and groups
5. Add your service account email with the permissions "See all event details" at a minimum
6. Click Send.


#### TODOist App Setup
1. Log into TODOist and create a new app in your TODOist Developer Console (https://developer.todoist.com/appconsole.html)
2. Set "OAuth redirect URL" to `https://todoist.com/oauth/authorize`
3. Set "Webhook callback URL" to your Google Cloud Function URL
4. Add the following items to "Watched Events":
 - `item:added`
 - `item:updated`
5. Click "Activate webhook"
6. Perform TODOist webhook Authorization procedure
    a. Enter the following string into your browser, replacing the `client_id` with the actual Client ID of your TODOist app (found in your TODOist Developer Console): `https://todoist.com/oauth/authorize?client_id=0123456789abcdef&scope=data:read,data:delete&state=secretstring`
    b. Press "Agree"
    c. This should redirect you to a url containing a `code`. Copy this code.
    d. In a command line, run this command, replacing the `client_id` and `client_secret` with their respective values from your TODOist Developer Console and replacing `code` with the code you got in step 6. c.:
    ```bash
    $ curl "https://todoist.com/oauth/access_token" \
    -d "client_id=0123456789abcdef" \
    -d "client_secret=secret" \
    -d "code=abcdef" \
    -d "redirect_uri=https://www.google.com/"

Your TODOist should now be authorized to send webhooks to your Google Cloud function whenever you add or modify a task!
    ```


#### Data File
- Create a file in the outermost directory called `data.py`
- Enter this data into `data.py`:
```python
calendar_id = 'Your Calendar ID (i.e. 'primary', or 'your_email@gmail.com')'
cloud_function_address = 'Your Google Cloud Function URL'
todoist_api_token = 'Your TODOist account API token (see https://todoist.com/help/articles/find-your-api-token-Jpzx9IIlB)'
phone_number = 'XXXYYYZZZZ'
```

You can find your calendar ID by going to your Google Calendar, clicking on the three dots next to your calendar in the bottom left, --> "Settings and Sharing" --> "Calendar ID".


## Credits
- https://github.com/ayvi-0001/example-py-gcal-api-cloud-function
- https://github.com/ActivityWatch/aw-import-ical/