
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from meetup.models import Meeting, Participant
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram import error as telegram_error
import os


@receiver(post_save, sender=Meeting)
def notify_participants_about_meetings_update(sender, instance, created, **kwargs):
    if created:
        notification = f'В расписании появилось мероприятие «{instance.title}» в секции «{instance.section.title}»'\
                       f'\n\n{instance.content}'
    else:
        notification = f'Обновилась информация о мероприятии «{instance.title}» в секции «{instance.section.title}»'\
                       f'\n\n{instance.content}'
    send_notification_to_participants(notification)


@receiver(post_delete, sender=Meeting)
def notify_participants_about_meetings_delete(sender, instance, **kwargs):
    notification = f'Мероприятие «{instance.title}» удалено из секции «{instance.section.title}»'
    send_notification_to_participants(notification)


@receiver(m2m_changed, sender=Meeting.speakers.through)
def notify_speakers_about_appointment_to_meeting(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        notification = f'Вас назначили спикером на мероприятие «{instance.title}» в секции «{instance.section.title}»'
    elif action == 'post_remove':
        notification = f'Вас удалили из спикеров на мероприятии «{instance.title}» в секции «{instance.section.title}»'
    if 'notification' not in locals():
        return
    send_notification_to_participants(notification, pk_set)


def send_notification_to_participants(notification, only_to_ids=None):
    if only_to_ids:
        participants = Participant.objects.filter(pk__in=only_to_ids)
    else:
        participants = Participant.objects.all()

    load_dotenv()
    token = os.getenv('TG_TOKEN')
    updater = Updater(token)

    for participant in participants:
        try:
            updater.bot.send_message(
                chat_id=participant.telegram_id,
                text=notification
            )
        except telegram_error.BadRequest:
            continue
