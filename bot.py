import logging
import os

import requests
from dotenv import load_dotenv

from telegram import Bot, Update
from telegram.ext import CallbackContext


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

# TODO: insert real API endpoints
schedule_url = 'http://####'
create_user_url = "http://####"


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! I will help you fell comfortable at this convention! Please register before proceeding."
    )


def register(update: Update, context: CallbackContext):
    # TODO get first and last name from user
    user_id = update.effective_user.id

    user = {
        'user_id': user_id,
        'fisrt_name': first_name,
        'last_name': last_name,
    }
    #TODO insert the actual User class from the actual DB module
    user = database.User()
    send_user_to_db(user)


def send_user_to_db(user):
    response = requests.post(create_user_url, json=user)


def get_schedule():
    response = requests.get(schedule_url)
    response.raise_for_status()

    # TODO actual field that contains schedule
    return response.json()['### schedule ###']


def send_schedule_to_user(schedule: str, user, bot: Bot):
    bot.send_message(chat_id=user, text=schedule)



if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('TG_TOKEN')

