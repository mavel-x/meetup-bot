import logging
import os

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

from database_interactions import *

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


def send_user_to_db(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user = {
        'telegram_id': update.effective_user.id,
        'name': context.chat_data['full_name'],
        'company': context.chat_data['company'],
    }

    response = requests.post(create_user_url, data=user)
    response.raise_for_status()
    update.effective_chat.send_message(text='Регистрация успешна. Приятного мероприятия!')
    query.edit_message_text(f'User registered: {user}.')

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

    # schedule = fetch_schedule_from_db()

    update.effective_chat.send_message('Here is a dummy schedule.')

    return offer_to_choose_schedule_or_question(update, context)


def show_sections_for_question(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    sections = fetch_sections_from_db()

    keyboard = []
    row = []
    for section in sections:
        row.append(
            InlineKeyboardButton(
                section['title'],
                callback_data=f"section_{section['id']}"
            )
        )
        if len(row) > 1:
            keyboard.append(row.copy())
            row.clear()
    keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text('Please choose a section:', reply_markup=reply_markup)


def show_meetings_for_question(update: Update, context: CallbackContext) -> None:
    """Store selected section and show a list of meetings"""
    query = update.callback_query
    query.answer()
    context.chat_data['section'] = selection = query.data
    section_id = selection.split('_')[1]
    meetings = fetch_meetings_for_section_from_db(section_id)

    keyboard = []
    row = []
    for meeting in meetings:
        row.append(
            InlineKeyboardButton(
                meeting['title'],
                callback_data=f"meeting_{meeting['id']}"
            )
        )
        if len(row) > 1:
            keyboard.append(row.copy())
            row.clear()
    keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text('Please choose a meeting:', reply_markup=reply_markup)


def show_speakers_for_question(update: Update, context: CallbackContext) -> None:
    """Store selected meeting and show a list of speakers on an inline keyboard"""
    query = update.callback_query
    query.answer()
    context.chat_data['meeting'] = selection = query.data
    meeting_id = selection.split('_')[1]
    speakers = fetch_speakers_for_meeting_from_db(meeting_id)

    keyboard = []
    row = []
    if speakers:
        message_text = 'Please choose a speaker:'
        if len(speakers) == 1:
            keyboard = [
                [InlineKeyboardButton(
                    speakers[0]['name'],
                    callback_data=f"speaker_{speakers[0]['telegram_id']}"
                )]
            ]
        else:
            for speaker in speakers:
                row.append(
                    InlineKeyboardButton(
                        speaker['name'],
                        callback_data=f"speaker_{speaker['telegram_id']}"
                    )
                )
                if len(row) > 1:
                    keyboard.append(row.copy())
                    row.clear()
        keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel')])

    else:
        message_text = 'No speakers for this event.'
        keyboard = [
            [InlineKeyboardButton('Okay.', callback_data='cancel')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)


def request_question_text(update: Update, context: CallbackContext):
    """Store selected speaker and ask user to send their question to the bot"""
    query = update.callback_query
    query.answer()
    context.chat_data['speaker'] = query.data

    query.edit_message_text(f'All right. Please send me the question for {query.data}. You are now in the AWAIT_QUESTION stage.')

    return AWAIT_QUESTION


# TODO insert this function into the logic if there's time
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
                CallbackQueryHandler(
                    show_sections_for_question,
                    pattern=r'^question$'
                ),
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

