import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List

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
        self.SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL"))
        self.USER_TIMEZONE = os.getenv("USER_TIMEZONE")
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
    def __create_event_data(event: Event, event_type='Exchange') -> dict:
        """
        Подготовка данных для отправки в гугл-календарь.
        """
        event_data = {
            'summary': event.summary,
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
                    'isExternal': event_type == 'Exchange',
                    'exchangeChangekey': event.exchange_changekey,
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

    def get_events(self, calendar_id, interval = None) -> List[Event]:
        """
        Получить список событий из переданного календаря, за переданное кол-во дней.
        """
        def calculate_response_type(e) -> str:

            if e.get("extendedProperties"):
                resp_type = event.get("extendedProperties").get("private").get("responseType")
            else:
                if e.get("transparency"):
                    resp_type = "Organizer"
                else:
                    resp_type = "Organizer" if e.get("status") == "confirmed" else "Canceled"

            return resp_type


        if not interval:
            interval = self.SYNC_INTERVAL

        now = datetime.now(timezone.utc).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(days=interval)).isoformat()
        events_result = self.service.events().list(calendarId=calendar_id, timeMin=now, timeMax=end, singleEvents=True,
                                                   orderBy='startTime').execute()

        events = []
        for event in events_result.get('items', []):
            if event.get('eventType') and event.get('eventType') == 'birthday':     # синхронизация ДР не нужна
                continue
            start_raw = event.get("start", {}).get("dateTime")
            end_raw = event.get("end", {}).get("dateTime")

            if not start_raw or not end_raw:    # all-day события пропускаем
                continue

            start_dt = dateutil.parser.isoparse(start_raw).astimezone(ZoneInfo(self.USER_TIMEZONE))
            end_dt = dateutil.parser.isoparse(end_raw).astimezone(ZoneInfo(self.USER_TIMEZONE))

            new_event = Event(
                id=event.get("id"),
                system="Google",
                summary=event.get("summary"),
                start=start_dt,
                end=end_dt,
                location=event.get("location"),
                response_type=calculate_response_type(event)
            )

            if event.get("extendedProperties"):
                new_event.is_external = event.get("extendedProperties").get("private").get("isExternal")
                new_event.exchange_changekey = event.get("extendedProperties").get("private").get("exchangeChangekey")
            events.append(new_event)
        return events

    def create_event(self, calendar_id, event: Event):
        """
        Создать новое событие в календаре
        """
        event_data = self.__create_event_data(event)
        event = self.service.events().insert(calendarId=calendar_id, body=event_data).execute()
        return event

    def delete_event(self, calendar_id, event):
        """
        Удалить событие из календаря
        """
        return self.service.events().delete(
            calendarId=calendar_id,
            eventId=event.id
        ).execute()
