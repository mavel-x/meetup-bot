import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def notify_of_new_event(user_id, event_description, bot):
    bot.send_message(chat_id=user_id, text=event_description)


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Notify of new event.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's Telegram ID"
    )
    argparser.add_argument(
        'event_description',
        help='Event description to send'
    )
    args = argparser.parse_args()

    notify_of_new_event(args.user_id, args.event_description, bot)


if __name__ == "__main__":
    main()
