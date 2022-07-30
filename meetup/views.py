from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from meetup.models import Participant, Section, Meeting, Question


def get_participant(request, telegram_id):
    participant = get_object_or_404(Participant, telegram_id=telegram_id)
    context = {
        'name': participant.name,
        'company': participant.company,
        'is_speaker': participant.is_speaker
    }
    return JsonResponse(
        context,
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


@csrf_exempt
def register_participant(request):
    participant, created = Participant.objects.get_or_create(
        name=request.POST.get('name', ''),
        company=request.POST.get('company', ''),
        telegram_id=int(request.POST.get('telegram_id', 0))
    )
    return JsonResponse(
        {'status': 'ok' if created else 'error'},
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


def get_sections_list(request):
    sections = []
    for section in Section.objects.all():
        sections.append({
            'id': section.pk,
            'title': section.title
        })
    return JsonResponse(
        {'sections': sections},
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


def get_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    meetings = []
    for meeting in section.meetings.all():
        meetings.append({
            'id': meeting.id,
            'title': meeting.title
        })
    context = {
        'title': section.title,
        'meetings': meetings
    }
    return JsonResponse(
        context,
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


def get_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    speakers = []
    for speaker in meeting.speakers.all():
        speakers.append({
            'telegram_id': speaker.telegram_id,
            'name': speaker.name,
            'company': speaker.company
        })
    context = {
        'title': meeting.title,
        'content': meeting.content,
        'speakers': speakers
    }
    return JsonResponse(
        context,
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


@csrf_exempt
def create_question(request):
    participant_telegram_id = request.POST.get('participant_telegram_id', 0)
    speaker_telegram_id = request.POST.get('speaker_telegram_id', 0)
    question_message_id = request.POST.get('question_message_id', 0)
    question = request.POST.get('question', '')
    participant = get_object_or_404(Participant, telegram_id=participant_telegram_id)
    speaker = get_object_or_404(Participant, telegram_id=speaker_telegram_id)
    question, created = Question.objects.get_or_create(
        question=question,
        question_message_id=question_message_id,
        participant=participant,
        speaker=speaker
    )
    return JsonResponse(
        {'status': 'ok' if created else 'error'},
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )


@csrf_exempt
def add_answer_to_question(request, question_message_id):
    question = get_object_or_404(Question, question_message_id=question_message_id)
    question.answer = request.POST.get('answer', '')
    question.save()
    return JsonResponse(
        {'status': 'ok'},
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 4}
    )
