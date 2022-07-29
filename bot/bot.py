import logging
import os
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from notifications.notify_user_of_registration import notify_user_of_registration

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
    AWAIT_ANSWER,
) = range(7)

# TODO: insert real API endpoints
root_url = 'http://127.0.0.1:8000/meetup/'
schedule_url = 'http://####'
meetings_url = 'http://####'
speakers_url = 'http://####'
create_user_url = urljoin(root_url, 'participant/register/')
sections_url = urljoin(root_url, 'sections/')
participant_url = urljoin(root_url, 'participant/')


def start(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Dummy start text."
    )

    user_id = update.effective_user.id
    if participant_is_in_db(user_id):
        return offer_to_choose_schedule_or_question(update, context)

    keyboard = [
        [
            InlineKeyboardButton("Register", callback_data='register')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('You are now in the AWAIT_REGISTRATION stage. Press the button:', reply_markup=reply_markup)
    return AWAIT_REGISTRATION


def request_full_name(update: Update, context: CallbackContext) -> int:
    """Ask the user to send their full name"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(f'Query text: {query.data}. You are now in the AWAIT_NAME stage. Enter full name.')
    return AWAIT_NAME


def request_company_name(update: Update, context: CallbackContext) -> int:
    """Store full name and ask the user to send the name of their company"""

    # This checks if we came here from entering full name or from pressing "Back" in the next step.
    # If we came back from the confirmation step, there will be no update.message. This can be refactored into
    # something more self-describing later.
    if update.message:
        context.chat_data['full_name'] = update.message.text

    keyboard = [
        [InlineKeyboardButton("Back", callback_data='back_to_name')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(
        f'Full name stored: {context.chat_data["full_name"]}. You are now in the AWAIT_COMPANY stage. Enter company name or press Back to reenter full name.',
        reply_markup=reply_markup
    )

    return AWAIT_COMPANY


def confirm_company_name(update: Update, context: CallbackContext) -> int:
    """Ask user to confirm company name they just entered or return to previous step"""

    # Same check as in request_company_name(), can be refactored.
    if update.message:
        context.chat_data['company'] = update.message.text

    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm')],
        [InlineKeyboardButton("Back", callback_data='back_to_company')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(
        f'Company name stored: {context.chat_data["company"]}. Confirm registration or press Back to reenter company name.',
        reply_markup=reply_markup
    )
    return AWAIT_CONFIRMATION


def send_user_to_db(update: Update, context: CallbackContext, bot):
    query = update.callback_query
    query.answer()

    user = {
        'user_id': update.effective_user.id,
        'full_name': context.chat_data['full_name'],
        'company': context.chat_data['company'],
    }

    response = requests.post(create_user_url, json=user)
    response.raise_for_status()
    if response.status_code == 200:
        notify_user_of_registration(user['user_id'], bot)
    query.edit_message_text(f'User registered: {user}. You are now in the CHOOSE_SCH_OR_Q stage.')

    return offer_to_choose_schedule_or_question(update, context)


def offer_to_choose_schedule_or_question(update: Update, context: CallbackContext) -> int:
    """Display two inline buttons: Schedule and Ask a question"""
    keyboard = [
        [
            InlineKeyboardButton("Schedule", callback_data='schedule'),
            InlineKeyboardButton("Question", callback_data='question'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message('You are now in the CHOOSE_SCH_OR_Q stage. Please choose:', reply_markup=reply_markup)
    return CHOOSE_SCHEDULE_OR_QUESTION


def send_schedule_to_user(update: Update, context: CallbackContext) -> int:
    """Send the schedule when the user requests it.
    The script in ./notifications is for mass sending by admins.
    """
    query = update.callback_query
    query.answer()

    schedule = fetch_schedule_from_db()

    update.effective_chat.send_message('Here is a dummy schedule.')

    return offer_to_choose_schedule_or_question(update, context)


def show_sections_for_question(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    sections = fetch_sections_from_db()

    keyboard = [
        [
            InlineKeyboardButton("Section 1", callback_data='section_1'),
            InlineKeyboardButton("Section 2", callback_data='section_2'),
        ],
        [InlineKeyboardButton("Section 3", callback_data='section_3')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text('Please choose a section:', reply_markup=reply_markup)


def show_meetings_for_question(update: Update, context: CallbackContext):
    """Store selected section and show a list of meetings"""
    query = update.callback_query
    query.answer()
    context.chat_data['section'] = query.data

    meetings = fetch_meetings_from_db()

    keyboard = [
        [
            InlineKeyboardButton("Meeting 1", callback_data='meeting_1'),
            InlineKeyboardButton("Meeting 2", callback_data='meeting_2'),
        ],
        [InlineKeyboardButton("Meeting 3", callback_data='meeting_3')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text('Please choose a meeting:', reply_markup=reply_markup)


def show_speakers_for_question(update: Update, context: CallbackContext):
    """Store selected meeting and show a list of speakers on an inline keyboard"""
    query = update.callback_query
    query.answer()
    context.chat_data['meeting'] = query.data

    speakers = fetch_speakers_from_db()

    keyboard = [
        [
            InlineKeyboardButton("Speaker 1", callback_data='speaker_1'),
            InlineKeyboardButton("Speaker 2", callback_data='speaker_2'),
        ],
        [InlineKeyboardButton("Speaker 3", callback_data='speaker_3')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text('Please choose a speaker:', reply_markup=reply_markup)


def request_question_text(update: Update, context: CallbackContext):
    """Store selected speaker and ask user to send their question to the bot"""
    query = update.callback_query
    query.answer()
    context.chat_data['speaker'] = query.data

    query.edit_message_text(f'All right. Please send me the question for {query.data}. You are now in the AWAIT_QUESTION stage.')

    return AWAIT_QUESTION


# TODO insert this function into the logic
def confirm_sending_question(update: Update, context: CallbackContext):
    """Show the user their question and the speaker it will go to. Ask to confirm or cancel."""
    pass


def send_question_to_speaker(update: Update, context: CallbackContext):
    """Send question to the database with the user id of the speaker, ideally the question is an dict
    with data about the asking user and the message id of the question so that the
    answer can be sent as a reply to the user's message.
    """
    # TODO retrieve the message id of the question and send it along with the question's text
    update.message.reply_text(f'Question to send: {update.message.text}.\n\nSpeaker selected: {context.chat_data["speaker"]}')
    return offer_to_choose_schedule_or_question(update, context)

# the user receives an answer through a separate script in ./notifications


# the following 2 functions are for speakers:
def request_answer(question):
    """When a speaker taps the inline button 'Answer' under one of the questions,
    ask them to send the answer.
    """
    return AWAIT_ANSWER


def send_answer_to_participant(answer, question):
    # TODO get the user_id of the asking user from the question object
    # TODO get the message_id of the question to reply to
    # TODO either import and call the function from script or run the script in ./notifications
    pass


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the current operation and offer to choose schedule or question."""
    query = update.callback_query
    query.answer()
    query.edit_message_text('Okay, cancelled.')
    return offer_to_choose_schedule_or_question(update, context)


def help(update: Update, context: CallbackContext):
    """Send help text"""
    update.effective_chat.send_message('Dummy help text.')


def fetch_schedule_from_db() -> str:
    response = requests.get(schedule_url)
    response.raise_for_status()
    return response.text


def fetch_sections_from_db():
    response = requests.get(sections_url)
    response.raise_for_status()
    return response.content


def fetch_meetings_from_db():
    """Ask DB for a list of meetings in a given section"""
    response = requests.get(meetings_url)
    response.raise_for_status()
    return response.content


def fetch_speakers_from_db():
    """Ask DB for a list of users who are marked as speakers"""
    response = requests.get(speakers_url)
    response.raise_for_status()
    return response.content


def participant_is_in_db(participant_telegram_id: int):
    response = requests.get(f'{participant_url}{participant_telegram_id}')
    return response.ok



def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
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
                CallbackQueryHandler(send_user_to_db, pattern='^confirm$')
            ],
            CHOOSE_SCHEDULE_OR_QUESTION: [
                CallbackQueryHandler(send_schedule_to_user, pattern=r'^schedule$'),
                CallbackQueryHandler(show_sections_for_question, pattern=r'^question$'),
                CallbackQueryHandler(show_meetings_for_question, pattern=r'^section_\d+$'),
                CallbackQueryHandler(show_speakers_for_question, pattern=r'^meeting_\d+$'),
                CallbackQueryHandler(request_question_text, pattern=r'^speaker_\d+$'),
                # TODO the CallbackQueryHandler for the "Answer" button under a question received by the speaker can live here too
            ],
            AWAIT_QUESTION: [MessageHandler(Filters.text & ~Filters.command, send_question_to_speaker)],
            AWAIT_ANSWER: [MessageHandler(Filters.text & ~Filters.command, send_answer_to_participant)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern=r'^cancel$'),
            MessageHandler(Filters.text, help),
        ]
    )

    dispatcher.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

