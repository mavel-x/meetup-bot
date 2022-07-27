import logging
import os

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Updater


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# TODO: insert real API endpoints
schedule_url = 'http://####'
create_user_url = "http://####"


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! I will help you fell comfortable at this convention! Please register before proceeding."
    )
    # TODO check if user already in database
    # TODO an inline button asking user to register
    # TODO if not in database - inline buttons for requesting the schedule and asking a question


# The following 3 functions are for the registration process
def request_full_name(update: Update, context: CallbackContext):
    """Ask the user to send back their full name"""
    pass


def request_company_name(update: Update, context: CallbackContext):
    """Ask the user to send back the name of their company"""
    pass


def send_user_to_db(update: Update, context: CallbackContext):
    user = {
        'user_id': 12345678,
        'full_name': 'some_full_name',
        'company': 'some_company',
    }
    response = requests.post(create_user_url, json=user)
    response.raise_for_status()


def fetch_schedule_from_db():
    response = requests.get(schedule_url)
    response.raise_for_status()

    # TODO actual field that contains schedule
    return response.json()['### schedule ###']


def send_schedule_to_user(update: Update, context: CallbackContext):
    """Send the schedule when the user requests it.
    The script in ./notifications is for mass sending by admins.
    """
    schedule = fetch_schedule_from_db()
    context.bot.send_message(chat_id=update.effective_chat.id, text=schedule)


def fetch_speakers_from_db():
    """Ask DB for a list of users who are marked as speakers"""
    pass


def select_speaker_to_ask(update: Update, context: CallbackContext):
    """Show a list of speakers on an inline keyboard"""
    speakers = fetch_speakers_from_db()
    pass


def request_question_text(update: Update, context: CallbackContext):
    """Ask user to send their question to the bot"""
    pass


def send_question_to_speaker(question, speaker):
    """Send question to user id of the speaker, ideally the question is an object
    with data about the asking user and the message id of the question so that the
    answer can be sent as a reply to the user's message.
    """
    pass

# the user receives an answer through a separate script in ./notifications


# the following 2 functions are for speakers:
def request_answer(question):
    """When a speaker taps the inline button 'Answer' under one of the questions,
    ask them to send the answer.
    """
    pass


def send_answer_to_participant(answer, question):
    # TODO get the user_id of the asking user from the question object
    # TODO get the message_id of the question to reply to
    # TODO either import and call the function from script or run the script in ./notifications
    pass


def help(update: Update, context: CallbackContext):
    """Send help text"""


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    updater = Updater(token)

    #TODO add handlers

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

