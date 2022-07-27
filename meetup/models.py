from django.db import models


class Participant(models.Model):
    name = models.CharField(max_length=200, verbose_name='Имя')
    email = models.EmailField(max_length=200, verbose_name='Email',
                              default='', blank=True)
    company = models.CharField(max_length=200, verbose_name='Компания',
                               default='', blank=True)
    is_speaker = models.BooleanField(verbose_name='Спикер', default=False)


class Section(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название',
                             default='')
    order = models.IntegerField(verbose_name='Порядок')

    class Meta:
        ordering = ('order',)


class Meeting(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название',
                             default='')
    order = models.IntegerField(verbose_name='Порядок')
    content = models.TextField(verbose_name='Содержание', default='',
                               blank=True)
    speakers = models.ManyToManyField(Participant, related_name='meetings',
                                      verbose_name='Спикеры')

    class Meta:
        ordering = ('order',)
