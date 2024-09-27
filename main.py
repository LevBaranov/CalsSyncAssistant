import os
from gcal import GCall
from ecal import ECall


def check_and_update_event(event, account_id, service):
    account_events = {ev.external_id: ev for ev in service.get_events(account_id) if hasattr(ev, 'external_id')}
    if event.id in account_events.keys():
        if account_events[event.id].start == event.start and account_events[event.id].end == event.end:
            print(f"Event {event.summary} is exist in {account_id}")
        else:
            service.update_event(account_id, account_events[event.id].id, event)
            print(f"Event {event.summary} modified in {account_id}")
    else:
        service.create_event(account_id, event)
        print(f"Event {event.summary} create in {account_id}")


def main():
    first_gmail_cal_id = os.getenv("FIRST_GMAIL_CAL_ID")
    second_gmail_cal_id = os.getenv("SECOND_GMAIL_CAL_ID")
    google_service = GCall()
    exchange_service = ECall()

    for event in google_service.get_events(second_gmail_cal_id):
        if not hasattr(event, 'external_id') and event.response_type != 'transparent':
            new_event = exchange_service.create_event(event)
            print(f"Event {event.summary} create in Exchange")
            google_service.update_event(second_gmail_cal_id, event.id, new_event, "Bitrix")
        else:
            print(f"Event {event.summary} is exist in Exchange")

    exchange_events = exchange_service.get_events()

    for exchange_event in exchange_events:
        if exchange_event.isPrivate:
            print(f"Event {exchange_event.summary} shouldn't sync")
            continue
        if exchange_event.response_type in ["Accept", "Organizer"]:
            check_and_update_event(exchange_event, second_gmail_cal_id, google_service)
        else:
            check_and_update_event(exchange_event, first_gmail_cal_id, google_service)


if __name__ == '__main__':
    main()
