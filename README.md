# Life Assistant

A LLM Integration with your Google Calendar

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

#### Data File
- Create a file in the outermost directory called `data.py`
- Enter this data into `data.py`:
```python
calendar_id = 'Your Calendar ID (i.e. \'primary\', or \'your_email@gmail.com\')'
cloud_function_address = 'Your Google Cloud Function URL'
```

You can find your calendar ID by going to your Google Calendar, clicking on the three dots next to your calendar in the bottom left, --> "Settings and Sharing" --> "Calendar ID".


## Credits
- https://github.com/ayvi-0001/example-py-gcal-api-cloud-function
- https://github.com/ActivityWatch/aw-import-ical/