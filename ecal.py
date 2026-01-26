import os
import datetime
from zoneinfo import ZoneInfo
from typing import List

from exchangelib import Credentials, Account, CalendarItem, Configuration, DELEGATE, BaseProtocol, NoVerifyHTTPAdapter
import urllib3

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
        exchange_server = os.getenv("EXCHANGE_SERVER")

        self.SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL"))
        self.USER_TIMEZONE = os.getenv("USER_TIMEZONE")

        urllib3.disable_warnings()
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        # Настройка Exchange
        credentials = Credentials(exchange_username, exchange_password)

        config = Configuration(
            server=exchange_server,
            credentials=credentials
        )

        self.account = Account(
            primary_smtp_address=exchange_email,
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )

    def get_events(self, interval=None) -> List[Event]:
        """
        Получить список событий из календаря Exchange за переданное кол-во дней.
        """

        if not interval:
            interval = self.SYNC_INTERVAL

        now = datetime.datetime.now(datetime.timezone.utc)
        end = now + datetime.timedelta(days=interval)
        events = []
        for _event in self.account.calendar.view(start=now, end=end).all():
            events.append(Event(
                id=_event.id,
                system="Exchange",
                summary=_event.subject,
                start=_event.start.astimezone(ZoneInfo(self.USER_TIMEZONE)),
                end=_event.end.astimezone(ZoneInfo(self.USER_TIMEZONE)),
                location=_event.location,
                response_type=_event.my_response_type,
                exchange_changekey=_event.changekey,
                is_external=_event.sensitivity == "Private"  #Считаем что приватные задачи создаются только из вне
            ))

        return events

    def create_event(self, new_event: Event):
        """
        Создать событие в календаре.
        """

        item = CalendarItem(
            folder=self.account.calendar,
            subject=new_event.summary,
            location=new_event.location,
            start=new_event.start,
            end=new_event.end,
            sensitivity="Private"
        ).save()

        return Event(
            id=item.id,
            system="Exchange",
            summary=new_event.summary,
            start=item.start,
            end=item.end,
            location=new_event.location,
            response_type=new_event.response_type,
            exchange_changekey=item.changekey,
            is_external=True
        )

    def delete_event(self, event):
        """
        Обновление существующего события
        """

        item = CalendarItem(
            account=self.account,
            id=event.id,
            changekey=event.exchange_changekey
        )

        return item.delete(
            send_meeting_cancellations='SendToNone'
        )
