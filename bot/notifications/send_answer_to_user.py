import argparse
import os

from dotenv import load_dotenv
from telegram import Bot


def send_answer_to_user(user_id, answer, question_id, bot):
    bot.send_message(
        chat_id=user_id,
        text=answer,
        reply_to_message_id=question_id,
        allow_sending_without_reply=True,
    )


def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    bot = Bot(token=token)

    argparser = argparse.ArgumentParser(description='Send answer to user.')
    argparser.add_argument(
        'user_id',
        type=int,
        help="User's Telegram ID"
    )
    argparser.add_argument(
        'answer',
        help='Answer to send'
    )
    argparser.add_argument(
        'question_id',
        help='Message ID of the original question'
    )
    args = argparser.parse_args()

    send_answer_to_user(args.user_id, args.answer, args.question_id, bot)


if __name__ == "__main__":
    main()
