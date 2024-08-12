from gcal import GCall

google_service = GCall()

# List calendars
calendar_list = google_service.get_calendars()
if calendar_list:
    print(calendar_list)
else:
    print("No calendars found.")
