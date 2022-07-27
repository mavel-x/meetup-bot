from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from meetup.models import Participant


def get_participant(request, telegram_id):
    participant = get_object_or_404(Participant, telegram_id=telegram_id)
    context = {
        'name': participant.name,
        'company': participant.company,
        'is_speaker': participant.is_speaker
    }
    return JsonResponse(context, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 4})


def register_participant(request):
    pass


def get_sections_list(request):
    pass


def get_section(request, section_id):
    pass


def get_meeting(request, meeting_id):
    pass


def create_question(request):
    pass


def add_answer_to_question(request):
    pass
