# Life Assistant

A LLM Integration with your Google Calendar and Todoist to send you relevant reminders (via text message) related your events and tasks. You can customize/slowly accrue the list of reminders you want.

Technologies used:
- Modal for severless hosting of a function
- Google Cloud Firestore for storage of persistent data for the Modal function
- Llama 3.1 for natural language analysis of tasks and calendar events
- Google Cloud Tasks for scheduled notifications
- Google Calendar API to read calendar events and changes
- Todoist API to read tasks and changes
- Pushover to send push notifications to a mobile device

Note: LifeAssistant requires Pushover, which charges a one-time $5 fee beyond the 30-day trial.


#### Modal Installation and Setup


#### Creating Google Cloud Platform Credentials
1. Project Creation
2. Service account stuff


#### Setting Calendar Permissions
1. Go to the settings menu in your Google Calendar (gear icon top right corner)
2. Click Settings for my calendar.
3. Select the calendar you want to share.
4. In Calendar settings, under Share with specific people or groups, click + Add people and groups
5. Add your service account email with the permissions "See all event details" at a minimum
6. Click Send.
7. Within the same Google Cloud Project, also enable the *Calendar API* on Google Cloud Platform.


#### Configuring Google Cloud Firestore
1. Within the same Google Cloud Project, enable the *Firestore API* on Google Cloud Platform.
2. In the Firestore dashboard, create a new default database.
3. In the Frestore dashboard, within the "(default)" database, add a Collection and name it "LifeAssistant".

LifeAssistant will now be able to store persistant data (such as Calendar sync tokens, a queue of scheduled notifications, etc.) in documents in Google Firestore!


#### Todoist App Setup
1. Log into Todoist and create a new app in your Todoist Developer Console (https://developer.todoist.com/appconsole.html)
2. Set "OAuth redirect URL" to `https://todoist.com/oauth/authorize`
3. Set "Webhook callback URL" to your Modal Function URL
4. Add the following items to "Watched Events":
 - `item:added`
 - `item:updated`
5. Click "Activate webhook"
6. Perform Todoist webhook Authorization procedure (See ["Webhook Activation & Personal Use"](https://developer.todoist.com/sync/v8/#webhooks))
    a. Enter the following string into your browser, replacing the `client_id` with the actual Client ID of your Todoist app (found in your Todoist Developer Console): `https://todoist.com/oauth/authorize?client_id=0123456789abcdef&scope=data:read,data:delete&state=secretstring`
    b. Press "Agree"
    c. This should redirect you to a url containing a `code`. Copy this code.
    d. In a command line, run this command, replacing the `client_id` and `client_secret` with their respective values from your Todoist Developer Console and replacing `code` with the code you got in step 6. c.:
    ```bash
    $ curl "https://todoist.com/oauth/access_token" \
    -d "client_id=0123456789abcdef" \
    -d "client_secret=secret" \
    -d "code=abcdef" \
    -d "redirect_uri=https://www.google.com/"
    ```

Your Todoist should now be authorized to send webhooks to your Modal function whenever you add or modify a task!


#### Pushover Setup
To send life reminders, Pushover is used. Pushover accepts simple HTTP Requests and sends push notifications to a device using the Pushover app.
1. Download the Pushover mobile app (works on IOS or Android).
2. In the Pushover App, create an account and take note of your User Key.
3. Create a Pushover Application from the Pushover [web dashboard](https://pushover.net/apps/build). Take note of the resulting API Token/Key.


#### HuggingFace and LLama Setup
LifeAssistant utilizes Meta AI's pre-trained Meta-Llama-3-8B-Instruct model to analyze your tasks and calendar events and determine whether they are worthy of sending a reminder for. LifeAssistant also uses HuggingFace to download the model weights and run inferences. Therefore, you need to set up an account with HuggingFace and request access to the Llama 3 8B Instruct model (it is not publicly accessible without requesting access).
1. [Create a HuggingFace account.](https://huggingface.co/join)
2. [Generate a HuggingFace token.](https://huggingface.co/settings/tokens) Save this token.
3. [Rquest Access to Meta-Llama-3-8B-Instruct.](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) This may take some time to get approved.


#### Data File
- Create a file in the outermost directory called `data.py`
- Enter this data into `data.py`:
```python
google_cloud_project_id = 'Your Google Cloud Project ID (i.e. `lifeassistant-123456`)'
calendar_id = 'Your Calendar ID (i.e. 'primary', or 'your_email@gmail.com')'
modal_function_address = 'Your Modal Function URL'
todoist_api_token = 'Your Todoist account API token (see https://todoist.com/help/articles/find-your-api-token-Jpzx9IIlB)'
todoist_projects = ['0123456789', '9876543210']  # List of project ID's whose tasks you want LifeAssistant to be able to see. You can find your project's ID by opening your Todoist project in the web-version of Todoist and extracting it from the URL.
pushover_api_token = "Your Pushover Application API Token/Key"
pushover_user_key = "Your Pushover Account User Key"
huggingface_token = "Your HuggingFace token"
```

You can find your calendar ID by going to your Google Calendar, clicking on the three dots next to your calendar in the bottom left, --> "Settings and Sharing" --> "Calendar ID".


### Common Links to Monitor LifeAssistant Status and Credit Usage
- [Modal Dashboard for Cloud Function/Compute/Storage Usage](https://modal.com/apps/)
- [Google Cloud Tasks Queue](https://console.cloud.google.com/cloudtasks)
- [Google Cloud Firestore File Storage](https://console.cloud.google.com/firestore/databases)
- [Todoist Dashboard](https://developer.todoist.com/appconsole.html)

### Disclaimers:

One underlying assumption is that the Modal function is invoked at least once every 30 days, or else the Google Calendar Watcher will expire without getting renewed. If 30 days does pass without the function being invoked, making or updating a task in Todoist (or invoking the function in some other way) will revive the Calendar watcher.


## Credits
- https://github.com/ayvi-0001/example-py-gcal-api-cloud-function
- https://github.com/ActivityWatch/aw-import-ical/