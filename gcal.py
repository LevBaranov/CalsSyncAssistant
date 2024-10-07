import os
import datetime

import dateutil.parser
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from event import Event


class GCall:
    """
    Гугл календарь. Для подключения и скрытии логики методов
    """

    def __init__(self):
        SCOPES = os.getenv("SCOPES").split(';')
        self.credentials = self.__auth(SCOPES)
        self.service = build('calendar', 'v3', credentials=self.credentials)

    @staticmethod
    def __auth(scopes):
        credentials = None

        # The file refresh_token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("creds/refresh_token.json"):
            credentials = Credentials.from_authorized_user_file("creds/refresh_token.json", scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "creds/access_token.json", scopes
                )
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("creds/refresh_token.json", "w") as token:
                token.write(credentials.to_json())

        return credentials

    @staticmethod
    def __create_event_date(event: Event, event_type='Exchange') -> dict:
        if event.response_type in ["Accept", "Organizer"]:
            summary = f"[{event.response_type}] {event.summary}"
        else:
            summary = event.summary
        event_data = {
            'summary': summary,
            'start': {
                'dateTime': event.start.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event.end.isoformat(),
                'timeZone': 'UTC',
            },
            "location": event.location,
            'extendedProperties': {
                'private': {
                    'externalId': event.id,
                    'externalSystem': event.system,
                    'responseType': event.response_type
                }
            }
        }
        if event_type == "Exchange":
            event_data['colorId'] = 8
        if event.response_type == 'transparent':
            event_data['transparency'] = 'transparent'
        return event_data

    def get_calendars(self):
        # List calendars
        calendar_list = self.service.calendarList().list().execute()
        cals = []
        if 'items' in calendar_list:
            for calendar in calendar_list['items']:
                cals.append({"id": calendar['id'], "summary": calendar['summary']})

        return cals

    def get_events(self, calendar_id, interval=10):
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        end = (datetime.datetime.utcnow() + datetime.timedelta(days=interval)).isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calendar_id, timeMin=now, timeMax=end, singleEvents=True,
                                                   orderBy='startTime').execute()

        events = []
        for event in events_result.get('items', []):
            new_event = Event(
                id=event.get("id"),
                system="Google",
                summary=event.get("summary"),
                start=dateutil.parser.isoparse(event.get("start").get("dateTime")),
                end=dateutil.parser.isoparse(event.get("end").get("dateTime")),
                location=event.get("location"),
                response_type=event.get("transparency") if event.get("transparency") else event.get("status"),
                isPrivate=True
            )

            if event.get("extendedProperties"):
                new_event.external_id = event.get("extendedProperties").get("private").get("externalId")
                new_event.external_system = event.get("extendedProperties").get("private").get("externalSystem")

            events.append(new_event)
        return events

    def create_event(self, calendar_id, event: Event):
        event_data = self.__create_event_date(event)
        event = self.service.events().insert(calendarId=calendar_id, body=event_data).execute()
        return event

    def update_event(self, calendar_id, event_id, new_event: Event, event_type='Exchange'):
        event_data = self.__create_event_date(new_event, event_type)
        event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event_data).execute()
        return event
