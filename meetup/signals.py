
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from meetup.models import Meeting, Question, Participant


@receiver(post_save, sender=Meeting)
def notify_participants_about_meetings_update(sender, instance, created, **kwargs):
    if created:
        notification = f'В расписании появилось мероприятие «{instance.title}» в секции «{instance.section.title}»'\
                       f'\n\n{instance.content}'
    else:
        notification = f'Обновилась информация о мероприятии «{instance.title}» в секции «{instance.section.title}»'\
                       f'\n\n{instance.content}'


@receiver(post_delete, sender=Meeting)
def notify_participants_about_meetings_delete(sender, instance, **kwargs):
    notification = f'Мероприятие «{instance.title}» удалено из секции «{instance.section.title}»'


@receiver(post_save, sender=Question)
def notify_participant_about_answered_question(sender, instance, created, **kwargs):
    if not created and instance.answer:
        notification = f'Спикер {instance.speaker.name} ответил на ваш вопрос «{instance.question}:»'\
                       f'\n\n{instance.answer}'


@receiver(m2m_changed, sender=Meeting.speakers.through)
def notify_speakers_about_appointment_to_meeting(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        notification = f'Вас назначили спикером на мероприятие «{instance.title}» в секции «{instance.section.title}»'
    elif action == 'post_remove':
        notification = f'Вас удалили из спикеров на мероприятии «{instance.title}» в секции «{instance.section.title}»'
    if notification not in locals():
        return
    for speaker_id in pk_set:
        pass
