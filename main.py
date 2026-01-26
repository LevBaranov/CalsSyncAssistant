import os

from event import Event
from gcal import GCall
from ecal import ECall


def main():
    first_gmail_cal_id = os.getenv("FIRST_GMAIL_CAL_ID")
    second_gmail_cal_id = os.getenv("SECOND_GMAIL_CAL_ID")
    google_service = GCall()
    exchange_service = ECall()

    google_events  = { event.hash_id: event for event in google_service.get_events(second_gmail_cal_id) }
    exchange_events = { event.hash_id: event for event in exchange_service.get_events() }

    def filter_events_into_create_and_delete(events_list: dict, set_event_hashes: set,
                                             new_events: list = [], events_to_delete: list = []) \
            -> tuple[list[Event], list[Event]]:

        for _event_hash_id in set_event_hashes:
            event = events_list.get(_event_hash_id)

            if not event.is_external:
                new_events.append(event)
            else:
                events_to_delete.append(event)

        return new_events, events_to_delete

    new_events, events_to_delete = filter_events_into_create_and_delete(google_events, (
                set(google_events.keys()) - set(exchange_events.keys())))

    new_events, events_to_delete = filter_events_into_create_and_delete(exchange_events, (
                set(exchange_events.keys()) - set(google_events.keys())), new_events, events_to_delete)

    for _event in new_events:

        print(f"Найдено новое событие: {_event.summary} в календаре {_event.system}")
        if _event.response_type in ["Accept", "Organizer"]:
            google_calendar_id = second_gmail_cal_id
        else:
            google_calendar_id = first_gmail_cal_id

        if _event.system == "Google":
            exchange_service.create_event(_event)
            print(f"Событие: {_event.summary} добавлено в календарь Exchange")

        if _event.system == "Exchange":
            google_service.create_event(google_calendar_id, _event)
            print(f"Событие: {_event.summary} добавлено в календарь Google")


    for _event in events_to_delete:

        if _event.response_type in ["Accept", "Organizer"]:
            google_calendar_id = second_gmail_cal_id
        else:
            google_calendar_id = first_gmail_cal_id

        if _event.system == "Google":
            print(f"Событие: {_event.summary} удалено из календаря Google")
            google_service.delete_event(google_calendar_id, _event)

        if _event.system == "Exchange":
            print(f"Событие: {_event.summary} удалено из календаря Exchange")
            exchange_service.delete_event(_event)


if __name__ == '__main__':
    main()
