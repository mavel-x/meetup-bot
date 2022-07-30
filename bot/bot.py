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
) = range(6)


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

    # Same check as in request_company_name(), can be refactored to be more self-descriptive.
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


def complete_registration(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user = {
        'telegram_id': update.effective_user.id,
        'name': context.chat_data['full_name'],
        'company': context.chat_data['company'],
    }
    send_user_to_db(user)

    query.edit_message_text('Регистрация успешна. Приятного мероприятия!')
    update.effective_chat.send_message(text=f'User registered: {user}.')

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

    # If we came here through pressing "Okay" after choosing a meeting with no speakers,
    # delete the message saying "No speakers"
    if update.callback_query:
        update.callback_query.answer()
        if update.callback_query.data == 'back_to_start':
            update.callback_query.delete_message()

    update.effective_chat.send_message('You are now in the CHOOSE_SCH_OR_Q stage. Please choose:', reply_markup=reply_markup)
    return CHOOSE_SCHEDULE_OR_QUESTION


def show_sections_to_user(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.chat_data['branch'] = query.data
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


def show_meetings_in_section_to_user(update: Update, context: CallbackContext) -> None:
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


def show_schedule_to_user(update: Update, context: CallbackContext, meeting_id) -> int:
    query = update.callback_query
    meeting = fetch_meeting_from_db(meeting_id)
    message_text = f"{meeting['title']}:\n\n{meeting['content']}"
    query.edit_message_text(message_text)
    context.chat_data['branch'] = None
    return offer_to_choose_schedule_or_question(update, context)


def show_speakers_for_question(update: Update, context: CallbackContext, meeting_id):
    query = update.callback_query
    speakers = fetch_meeting_from_db(meeting_id)['speakers']
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
            [InlineKeyboardButton('Okay.', callback_data='back_to_start')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)
    context.chat_data['branch'] = None


def show_speakers_keyboard_or_schedule(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.chat_data['meeting'] = selection = query.data
    meeting_id = selection.split('_')[1]

    if context.chat_data['branch'] == 'question':
        show_speakers_for_question(update, context, meeting_id)

    else:
        return show_schedule_to_user(update, context, meeting_id)


def request_question_text(update: Update, context: CallbackContext):
    """Store selected speaker and ask user to send their question to the bot"""
    query = update.callback_query
    query.answer()
    context.chat_data['speaker_id'] = speaker_id = query.data.split('_')[1]
    context.chat_data['speaker_name'] = speaker_name = get_participant_name_from_db(speaker_id)

    query.edit_message_text(f'All right. Please send me the question for {speaker_name}. You are now in the AWAIT_QUESTION stage.')

    return AWAIT_QUESTION


# TODO insert this function into the logic if there's time
def confirm_sending_question(update: Update, context: CallbackContext):
    """Show the user their question and the speaker it will go to. Ask to confirm or cancel."""
    pass


def send_question_to_speaker_and_db(update: Update, context: CallbackContext):
    """Send question to the speaker and to the database"""
    question_text = update.message.text
    question_message_id = update.message.message_id
    speaker_id = context.chat_data['speaker_id']
    speaker_name = context.chat_data['speaker_name']
    participant_name = get_participant_name_from_db(update.effective_user.id)
    question_text_formatted = (f"Question #{question_message_id} "
                               f"from {participant_name} ({update.effective_user.id}):\n\n"
                               f"{question_text}\n\n"
                               f"To answer, simply send me a reply to this message.")
    question = {
        'question': question_text,
        'question_message_id': question_message_id,
        'speaker_telegram_id': speaker_id,
        'participant_telegram_id': update.effective_user.id,
    }
    send_question_to_db(question)
    context.bot.send_message(
        chat_id=speaker_id,
        text=question_text_formatted,
    )
    update.message.reply_text(f'Question "{question}" sent to speaker "{speaker_name}"')
    return offer_to_choose_schedule_or_question(update, context)


def send_answer_to_participant(update: Update, context: CallbackContext):
    question = update.message.reply_to_message
    if not question.text.startswith('Question #'):
        return
    answer = update.message.text
    answer_formatted = f"Answer from speaker:\n\n{answer}"
    question_message_id = question.text.partition('#')[2].partition(' ')[0]
    asking_participant_id = question.text.partition('(')[2].partition(')')[0]

    send_answer_to_db(answer, question_message_id)

    context.bot.send_message(
        chat_id=asking_participant_id,
        text=answer_formatted,
        reply_to_message_id=question_message_id,
    )


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
                MessageHandler(Filters.reply & ~Filters.command, send_answer_to_participant)
            ],
            AWAIT_QUESTION: [MessageHandler(Filters.text & ~Filters.command, send_question_to_speaker_and_db)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern=r'^cancel$'),
            CallbackQueryHandler(offer_to_choose_schedule_or_question, pattern=r'back_to_start'),
            MessageHandler(Filters.text, help),
        ]
    )

    dispatcher.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
