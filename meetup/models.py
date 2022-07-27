from django.db import models


class Participant(models.Model):
    name = models.CharField(max_length=200, verbose_name='Имя')
    email = models.EmailField(max_length=200, verbose_name='Email',
                              default='', blank=True)
    company = models.CharField(max_length=200, verbose_name='Компания',
                               default='', blank=True)
    is_speaker = models.BooleanField(verbose_name='Спикер', default=False)

    def __str__(self):
        return f'{self.name} ({self.company})'


class Section(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название',
                             default='')
    order = models.IntegerField(verbose_name='Порядок')

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.title


class Meeting(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название',
                             default='')
    order = models.IntegerField(verbose_name='Порядок')
    content = models.TextField(verbose_name='Содержание', default='',
                               blank=True)
    section = models.ForeignKey(Section, related_name='meetings',
                                verbose_name='Секция',
                                on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Participant, related_name='meetings',
                                      verbose_name='Спикеры', blank=True,
                                      limit_choices_to={'is_speaker': True})

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.title
