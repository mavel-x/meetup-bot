from urllib.parse import urljoin

import requests

root_url = 'http://127.0.0.1:8000/meetup/'
sections_url = urljoin(root_url, 'sections/')
meetings_url = urljoin(root_url, 'section/')
speakers_url = urljoin(root_url, 'meeting/')
participant_url = urljoin(root_url, 'participant/')
create_user_url = urljoin(root_url, 'participant/register/')


def fetch_schedule_from_db() -> dict:
    response = requests.get(speakers_url)
    response.raise_for_status()
    return response.json()


def fetch_sections_from_db() -> list:
    """Ask DB for a list of sections in the event"""
    response = requests.get(sections_url)
    response.raise_for_status()
    return response.json()['sections']


def fetch_meetings_for_section_from_db(section_id) -> dict:
    """Ask DB for a list of meetings in a given section"""
    url = urljoin(meetings_url, section_id)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['meetings']


def fetch_meeting_from_db(meeting_id) -> dict:
    """Get data of a single meeting."""
    url = urljoin(speakers_url, meeting_id)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def participant_is_in_db(participant_telegram_id: int) -> bool:
    response = requests.get(f'{participant_url}{participant_telegram_id}')
    return response.ok
