from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from .models import Participant, Question, Section, Meeting
from adminsortable2.admin import SortableAdminMixin, SortableTabularInline


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_speaker')
    search_fields = ('name', 'company')
    list_filter = ('is_speaker',)
    list_editable = ('is_speaker',)


class MeetingInline(SortableTabularInline):
    model = Meeting
    extra = 1
    fields = ('order', 'title', 'content', 'speakers')
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }


@admin.register(Section)
class SectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title',)
    inlines = (MeetingInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'participant', 'speaker')
    list_filter = ('speaker',)


# @admin.register(Meeting)
# class MeetingAdmin(admin.ModelAdmin):
#     pass
