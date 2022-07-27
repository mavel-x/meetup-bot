import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def send_question_to_speaker(user_id, question, bot):
    bot.send_message(
        chat_id=user_id,
        text=f'Новый вопрос:\n{question}'
    )


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Send question to speaker.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's Telegram ID"
    )
    argparser.add_argument(
        'question',
        help='Question to send'
    )
    args = argparser.parse_args()

    send_question_to_speaker(args.user_id, args.question, bot)


if __name__ == "__main__":
    main()
