#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Send your tasks directly to the calendar rather than todo list.

tocal Read http://this.link                # Add 30 min event to the first empty slot starting from tomorrow.
tocal +3 @15 Check something really quick  # Add 15 min event to the first empty slot starting from 3 days in future.

TODO Handle OOO.
TODO Enable Autopilot.
"""


from __future__ import print_function
import datetime
import os.path
import pytz
import re
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


### User preferences ###
OFFICE_HOURS_START = 9  # day hour
OFFICE_HOURS_END = 17  # day hour
DEFAULT_DURATION = 30  # minutes
DEFAULT_OFFSET = 1  # days
MAX_OFFSET_DRIFT = 7  # days


DURATION_RE = re.compile(r"@(\d+)")
OFFSET_RE = re.compile(r"\+(\d+)")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

ONE_DAY = datetime.timedelta(hours=24)


def get_service():
    """Initialize GCal API. Auth if necessary."""

    configs = os.path.dirname(os.path.realpath(__file__))
    token = configs + "/token.json"
    secrets = configs + "/client_secrets.json"

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def offset_to_datetime(offset):
    """Convert offset from today in days to datetime of office hours start."""

    return datetime.datetime.now().astimezone().replace(
        hour=OFFICE_HOURS_START, minute=0, second=0, microsecond=0
    ) + datetime.timedelta(days=offset)


def datetime_to_gdate(t):
    """Format datetime to GCal API friendly string RFC3339."""

    return (
        t.astimezone(pytz.utc).replace(tzinfo=None).isoformat() + "Z"
    )  # 'Z' indicates UTC time


def gdate_to_datetime(s):
    """Parse GCal API datetime."""

    return datetime.datetime.fromisoformat(s[:-1]).replace(tzinfo=pytz.utc).astimezone()


def get_int_arg(argv, pattern, default):
    """Find the first argument matching the pattern and extract int value.
    As the second result return argv without the matching argument.
    """

    for i, arg in enumerate(argv):
        m = pattern.match(arg)
        if m:
            return int(m.group(1)), argv[:i] + argv[i + 1 :]
    return default, argv


def create_event(service, summary, start, duration):
    event = {
        "summary": summary,
        "start": {
            "dateTime": datetime_to_gdate(start),
        },
        "end": {
            "dateTime": datetime_to_gdate(start + duration),
        },
    }
    service.events().insert(calendarId="primary", body=event).execute()


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    argv = sys.argv[1:]  # drop script name

    duration, argv = get_int_arg(argv, DURATION_RE, DEFAULT_DURATION)
    offset, argv = get_int_arg(argv, OFFSET_RE, DEFAULT_OFFSET)
    summary = " ".join(argv)

    duration = datetime.timedelta(minutes=duration)
    duration_seconds = duration.total_seconds()
    free_start = offset_to_datetime(offset)

    service = get_service()

    body = {
        "items": [{"id": "primary"}],
        "timeMin": datetime_to_gdate(free_start),
        "timeMax": datetime_to_gdate(free_start + ONE_DAY * MAX_OFFSET_DRIFT),
    }
    busy = service.freebusy().query(body=body).execute()["calendars"]["primary"]["busy"]

    for entry in busy:
        # Fast-forward to a workday if we are on a weekend.
        while free_start.weekday() > 4:
            free_start = free_start.replace(hour=OFFICE_HOURS_START) + ONE_DAY

        free_end = gdate_to_datetime(entry["start"])

        free_duration = (free_end - free_start).total_seconds()

        if free_duration >= duration_seconds:
            # Found a slot.
            break

        free_start = gdate_to_datetime(entry["end"])
        if free_start.hour < OFFICE_HOURS_START:
            free_start = free_start.replace(hour=OFFICE_HOURS_START)
        elif free_start.hour >= OFFICE_HOURS_END:
            free_start = free_start.replace(hour=OFFICE_HOURS_START) + ONE_DAY

    create_event(service, summary, free_start, duration)


if __name__ == "__main__":
    main()
