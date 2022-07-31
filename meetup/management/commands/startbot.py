import logging
import os

from django.views.decorators.csrf import csrf_exempt
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import error as telegram_error
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

import meetup.management.commands._strings as strings
from meetup.models import Participant, Section, Meeting, Question

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    AWAIT_REGISTRATION,
    AWAIT_NAME,
    AWAIT_COMPANY,
    AWAIT_CONFIRMATION,
    CHOOSE_SCHEDULE_OR_QUESTION,
    AWAIT_QUESTION,
) = range(6)


def start(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=strings.start
    )

    try:
        Participant.objects.get(telegram_id=update.effective_user.id)
        return offer_to_choose_schedule_or_question(update, context)
    except Participant.DoesNotExist:
        keyboard = [
            [
                InlineKeyboardButton(strings.register_button, callback_data='register')
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(strings.register_message, reply_markup=reply_markup)
        return AWAIT_REGISTRATION


def request_full_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(strings.ask_name)
    context.chat_data['message_to_delete'] = query.message.message_id
    return AWAIT_NAME


def request_company_name(update: Update, context: CallbackContext) -> int:
    """Store full name and ask the user to send the name of their company"""

    # This checks if we came here from entering full name or from pressing "Back" in the next step.
    # If we came back from the confirmation step, there will be no update.message.
    if update.message:
        context.chat_data['full_name'] = update.message.text

    if 'message_to_delete' in context.chat_data:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['message_to_delete']
        )
        del context.chat_data['message_to_delete']

    keyboard = [
        [InlineKeyboardButton(strings.back_button, callback_data='back_to_name')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        update.callback_query.edit_message_text(
            strings.ask_company_name,
            reply_markup=reply_markup
        )
        context.chat_data['message_to_delete'] = update.callback_query.message.message_id
    else:
        company_message = update.effective_chat.send_message(
            strings.ask_company_name,
            reply_markup=reply_markup,
        )
        context.chat_data['message_to_delete'] = company_message.message_id
    return AWAIT_COMPANY


def confirm_company_name(update: Update, context: CallbackContext) -> int:
    """Ask user to confirm company name they just entered or return to previous step"""

    # This checks if we came here from entering full name or from pressing "Back" in the next step.
    # If we came back from the confirmation step, there will be no update.message.
    if update.message:
        context.chat_data['company'] = update.message.text

    if 'message_to_delete' in context.chat_data:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['message_to_delete']
        )
        del context.chat_data['message_to_delete']

    keyboard = [
        [InlineKeyboardButton(strings.confirm_button, callback_data='confirm')],
        [InlineKeyboardButton(strings.back_button, callback_data='back_to_company')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(
        strings.confirm_registration,
        reply_markup=reply_markup
    )
    return AWAIT_CONFIRMATION


@csrf_exempt
def complete_registration(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    participant, created = Participant.objects.get_or_create(
        name=context.chat_data['full_name'],
        company=context.chat_data['company'],
        telegram_id=update.effective_user.id
    )
    if created:
        query.edit_message_text(strings.successful_registration)
        return offer_to_choose_schedule_or_question(update, context)


def offer_to_choose_schedule_or_question(update: Update, context: CallbackContext) -> int:
    """Display two inline buttons: Schedule and Ask a question"""
    keyboard = [
        [
            InlineKeyboardButton(strings.schedule_button, callback_data='schedule'),
            InlineKeyboardButton(strings.question_button, callback_data='question'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # If we came here through pressing "Okay" after choosing a meeting with no speakers,
    # delete the message saying "No speakers"
    if update.callback_query:
        update.callback_query.answer()
        if update.callback_query.data == 'back_to_start':
            update.callback_query.delete_message()

    update.effective_chat.send_message(strings.choose_sch_or_q, reply_markup=reply_markup)
    return CHOOSE_SCHEDULE_OR_QUESTION


def show_sections_to_user(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.chat_data['branch'] = query.data

    keyboard = [[]]
    for section in Section.objects.all():
        keyboard[-1].append(
            InlineKeyboardButton(
                section.title,
                callback_data=f"section_{section.id}"
            )
        )
        if len(keyboard[-1]) > 1:
            keyboard.append([])
    keyboard.append([InlineKeyboardButton(strings.cancel_button, callback_data='cancel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(strings.choose_section, reply_markup=reply_markup)


def show_meetings_in_section_to_user(update: Update, context: CallbackContext):
    """Store selected section and show a list of meetings"""
    query = update.callback_query
    query.answer()
    context.chat_data['section'] = selection = query.data
    section_id = selection.split('_')[1]
    try:
        section = Section.objects.get(pk=section_id)

        keyboard = [[]]
        for meeting in section.meetings.all():
            keyboard[-1].append(
                InlineKeyboardButton(
                    meeting.title,
                    callback_data=f"meeting_{meeting.id}"
                )
            )
            if len(keyboard[-1]) > 1:
                keyboard.append([])
        keyboard.append([InlineKeyboardButton(strings.cancel_button, callback_data='cancel')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(strings.choose_meeting, reply_markup=reply_markup)
    except Section.DoesNotExist:
        query.edit_message_text(strings.database_error)
        return offer_to_choose_schedule_or_question(update, context)


def show_schedule_to_user(update: Update, context: CallbackContext, meeting_id) -> int:
    query = update.callback_query
    try:
        meeting = Meeting.objects.get(pk=meeting_id)
        message_text = f"{meeting.title}:\n\n{meeting.content}"
        query.edit_message_text(message_text)
        context.chat_data['branch'] = None
        return offer_to_choose_schedule_or_question(update, context)
    except Meeting.DoesNotExist:
        query.edit_message_text(strings.database_error)
        return offer_to_choose_schedule_or_question(update, context)


def show_speakers_for_question(update: Update, context: CallbackContext, meeting_id):
    query = update.callback_query
    query.answer()
    try:
        meeting = Meeting.objects.get(pk=meeting_id)
        speakers = meeting.speakers
        if speakers.count():
            message_text = strings.choose_speaker
            keyboard = [[]]
            for speaker in speakers.all():
                keyboard[-1].append(
                    InlineKeyboardButton(
                        speaker.name,
                        callback_data=f"speaker_{speaker.telegram_id}"
                    )
                )
                if len(keyboard[-1]) > 1:
                    keyboard.append([])
            keyboard.append([InlineKeyboardButton(strings.cancel_button, callback_data='cancel')])
        else:
            message_text = strings.no_speakers
            keyboard = [
                [InlineKeyboardButton(strings.back_to_start_button, callback_data='back_to_start')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(message_text, reply_markup=reply_markup)
        context.chat_data['branch'] = None
    except Meeting.DoesNotExist:
        query.edit_message_text(strings.database_error)
        return offer_to_choose_schedule_or_question(update, context)


def show_speakers_keyboard_or_schedule(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.chat_data['meeting'] = selection = query.data
    meeting_id = selection.split('_')[1]
    if 'branch' not in context.chat_data:
        return offer_to_choose_schedule_or_question(update, context)
    if context.chat_data['branch'] == 'question':
        show_speakers_for_question(update, context, meeting_id)
    else:
        return show_schedule_to_user(update, context, meeting_id)


def request_question_text(update: Update, context: CallbackContext):
    """Store selected speaker and ask user to send their question to the bot"""
    query = update.callback_query
    query.answer()
    context.chat_data['speaker_id'] = speaker_id = query.data.split('_')[1]
    try:
        speaker = Participant.objects.get(telegram_id=speaker_id)
        context.chat_data['speaker_name'] = speaker.name
        query.edit_message_text(strings.request_question)
        return AWAIT_QUESTION
    except Participant.DoesNotExist:
        query.edit_message_text(strings.database_error)
        return offer_to_choose_schedule_or_question(update, context)


# TODO insert this function into the logic if there's time
def confirm_sending_question(update: Update, context: CallbackContext):
    """Show the user their question and the speaker it will go to. Ask to confirm or cancel."""
    pass


@csrf_exempt
def send_question_to_speaker_and_db(update: Update, context: CallbackContext):
    """Send question to the speaker and to the database"""
    question_text = update.message.text
    question_message_id = update.message.message_id
    speaker_id = context.chat_data['speaker_id']
    speaker_name = context.chat_data['speaker_name']
    try:
        participant = Participant.objects.get(telegram_id=update.effective_user.id)
        speaker = Participant.objects.get(telegram_id=speaker_id)
        question, created = Question.objects.get_or_create(
            question=question_text,
            question_message_id=question_message_id,
            participant=participant,
            speaker=speaker
        )
        if created:
            question_text_formatted = strings.question_text_formatted.format(
                question_message_id=question_message_id,
                participant_name=participant.name,
                user_id=update.effective_user.id,
                question_text=question_text,
            )
            try:
                context.bot.send_message(
                chat_id=speaker_id,
                text=question_text_formatted,
                )
                update.message.reply_text(strings.question_sent.format(speaker_name=speaker_name))
            except telegram_error.BadRequest:
                update.message.reply_text(strings.question_send_error)
            return offer_to_choose_schedule_or_question(update, context)
        # Что делаем, если вопрос не записался в БД (уже существует полный аналог)?
        # TODO уточнить ошибку
        else:
            update.message.reply_text(strings.database_error)
            return offer_to_choose_schedule_or_question(update, context)
    except Participant.DoesNotExist:
        update.message.reply_text(strings.database_error)
        return offer_to_choose_schedule_or_question(update, context)


@csrf_exempt
def send_answer_to_participant(update: Update, context: CallbackContext):
    question = update.message.reply_to_message
    if not question.text.startswith(strings.question_text_formatted.partition('#')[0]):
        return
    answer = update.message.text
    answer_formatted = strings.answer_formatted.format(answer=answer)
    question_message_id = question.text.partition('#')[2].partition(' ')[0]
    asking_participant_id = question.text.partition('(')[2].partition(')')[0]

    try:
        question_from_db = Question.objects.get(question_message_id=question_message_id)
        question_from_db.answer = answer
        question_from_db.save()
    except Question.DoesNotExist:
        update.message.reply_text(strings.database_error)

    context.bot.send_message(
        chat_id=asking_participant_id,
        text=answer_formatted,
        reply_to_message_id=question_message_id,
        allow_sending_without_reply=True,
    )


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the current operation and offer to choose schedule or question."""
    query = update.callback_query
    query.answer()
    query.edit_message_text(strings.cancelled)
    return offer_to_choose_schedule_or_question(update, context)


def help(update: Update, context: CallbackContext):
    """Send help text"""
    update.effective_chat.send_message(strings.help_message)


class Command(BaseCommand):
    help = 'Запуск чат-бота'

    def handle(self, *args, **options):
        load_dotenv()
        token = os.getenv('TG_TOKEN')
        updater = Updater(token)
        dispatcher = updater.dispatcher

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CallbackQueryHandler(
                    show_sections_to_user,
                    pattern=r'^question$|^schedule$',
                ),
                CallbackQueryHandler(show_meetings_in_section_to_user, pattern=r'^section_\d+$'),
                CallbackQueryHandler(show_speakers_keyboard_or_schedule, pattern=r'^meeting_\d+$'),
                CallbackQueryHandler(request_question_text, pattern=r'^speaker_\d+$'),
                CallbackQueryHandler(cancel, pattern=r'^cancel$'),
                CallbackQueryHandler(offer_to_choose_schedule_or_question, pattern=r'back_to_start'),
                MessageHandler(Filters.reply & ~Filters.command, send_answer_to_participant),
                MessageHandler(Filters.text, help),
            ],
            states={
                AWAIT_REGISTRATION: [CallbackQueryHandler(request_full_name, pattern='^register$')],
                AWAIT_NAME: [MessageHandler(Filters.text & ~Filters.command, request_company_name)],
                AWAIT_COMPANY: [
                    CallbackQueryHandler(request_full_name, pattern='^back_to_name$'),
                    MessageHandler(Filters.text & ~Filters.command, confirm_company_name)
                ],
                AWAIT_CONFIRMATION: [
                    CallbackQueryHandler(request_company_name, pattern='^back_to_company$'),
                    CallbackQueryHandler(complete_registration, pattern='^confirm$')
                ],
                CHOOSE_SCHEDULE_OR_QUESTION: [
                    CallbackQueryHandler(
                        show_sections_to_user,
                        pattern=r'^question$|^schedule$'
                    ),
                    CallbackQueryHandler(show_meetings_in_section_to_user, pattern=r'^section_\d+$'),
                    CallbackQueryHandler(show_speakers_keyboard_or_schedule, pattern=r'^meeting_\d+$'),
                    CallbackQueryHandler(request_question_text, pattern=r'^speaker_\d+$'),
                ],
                AWAIT_QUESTION: [MessageHandler(
                    Filters.text & ~Filters.command & ~Filters.reply,
                    send_question_to_speaker_and_db
                )],
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern=r'^cancel$'),
                CallbackQueryHandler(offer_to_choose_schedule_or_question, pattern=r'back_to_start'),
                MessageHandler(Filters.reply & ~Filters.command, send_answer_to_participant),
                MessageHandler(Filters.text, help),
                ]
        )

        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()
