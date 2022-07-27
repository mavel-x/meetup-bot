import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def send_schedule_to_user(user_id, schedule, bot):
    bot.send_message(chat_id=user_id, text=schedule)


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Notify user of successful registration.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's Telegram ID"
    )
    argparser.add_argument(
        'schedule',
        help='Schedule to send'
    )
    args = argparser.parse_args()

    send_schedule_to_user(args.user_id, args.schedule, bot)


if __name__ == "__main__":
    main()
