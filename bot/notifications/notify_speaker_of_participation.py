import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def notify_speaker(user_id, bot, time):
    bot.send_message(chat_id=user_id, text=f'Âàñ íàçíà÷èëè ñïèêåðîì íà {time}!')


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Notify speaker of participation.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's telegram ID"
    )
    argparser.add_argument(
        'time',
        help='Time of speaking'
    )
    args = argparser.parse_args()

    notify_speaker(args.user_id, bot, args.time)


if __name__ == "__main__":
    main()
