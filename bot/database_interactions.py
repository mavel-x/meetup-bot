from urllib.parse import urljoin

import requests

root_url = 'http://127.0.0.1:8000/meetup/'
sections_url = urljoin(root_url, 'sections/')
meetings_url = urljoin(root_url, 'section/')
speakers_url = urljoin(root_url, 'meeting/')
participant_url = urljoin(root_url, 'participant/')
create_user_url = urljoin(root_url, 'participant/register/')
create_question_url = urljoin(root_url, 'question/create/')
add_answer_url = urljoin(root_url, 'question/{question_message_id}/add_answer/')


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


def get_participant_name_from_db(telegram_id: int or str) -> str:
    response = requests.get(f'{participant_url}{telegram_id}')
    response.raise_for_status()
    return response.json()['name']


def participant_is_in_db(telegram_id: int or str) -> bool:
    response = requests.get(f'{participant_url}{telegram_id}')
    return response.ok


def send_question_to_db(question: dict):
    response = requests.post(create_question_url, data=question)
    response.raise_for_status()


def send_answer_to_db(answer, question_id):
    url = add_answer_url.format(question_message_id=question_id)
    response = requests.post(url, data={'answer': answer})
    response.raise_for_status()


def send_user_to_db(user: dict):
    response = requests.post(create_user_url, data=user)
    response.raise_for_status()
