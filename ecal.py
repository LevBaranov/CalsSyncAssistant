import os
import datetime

from exchangelib import Credentials, Account, CalendarItem

from event import Event


class ECall:
    """
    Exchange календарь. Для подключения и скрытии логики методов
    """

    def __init__(self):
        # Параметры для Exchange
        exchange_username = os.getenv("EXCHANGE_USERNAME")
        exchange_password = os.getenv("EXCHANGE_PASSWORD")
        exchange_email = os.getenv("EXCHANGE_EMAIL")

        # Настройка Exchange
        credentials = Credentials(exchange_username, exchange_password)
        self.account = Account(exchange_email, credentials=credentials, autodiscover=True)

    def get_events(self, interval=10):
        now = datetime.datetime.now(datetime.timezone.utc)
        end = now + datetime.timedelta(days=interval)
        events = []
        for event in self.account.calendar.view(start=now, end=end).all():
            events.append(Event(
                id=event.id,
                system="Exchange",
                summary=event.subject,
                start=event.start,
                end=event.end,
                location=event.location,
                response_type=event.my_response_type,
            ))

        return events

    def create_event(self, event: Event):
        item = CalendarItem(
            folder=self.account.calendar,
            subject=event.summary,
            start=event.start,
            end=event.end
        ).save()

        return Event(
            id=item.id,
            system="Exchange",
            summary=event.summary,
            start=item.start,
            end=item.end,
            location=event.location,
            response_type=event.response_type,
        )
