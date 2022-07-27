import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def notify_user_of_registration(user_id, bot):
    bot.send_message(chat_id=user_id, text='Регистрация успешна. Приятного мероприятия!')


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Notify user of successful registration.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's telegram ID"
    )
    args = argparser.parse_args()

    notify_user_of_registration(args.user_id, bot)


if __name__ == "__main__":
    main()
